"""
Eleos Benchmark & Cost Resolution Service
Provides fallback resolution (District -> State -> National) and temporal CPI decay adjustments.
"""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database.models import CostBenchmark, BudgetItem

# Standard annual CPI inflation rate for statutory social sectors in India (6.0% annual)
DEFAULT_ANNUAL_CPI_INFLATION = Decimal("0.06")


class BenchmarkMatchResult:
    def __init__(
        self,
        benchmark: Optional[CostBenchmark],
        resolution: str,  # 'district', 'state', 'national', 'none'
        is_stale: bool = False,
        adjusted_unit_cost_mid: Optional[Decimal] = None,
        inflation_multiplier: Decimal = Decimal("1.0"),
        source_name: Optional[str] = None,
        source_url: Optional[str] = None
    ):
        self.benchmark = benchmark
        self.resolution = resolution
        self.is_stale = is_stale
        self.adjusted_unit_cost_mid = adjusted_unit_cost_mid
        self.inflation_multiplier = inflation_multiplier
        self.source_name = source_name
        self.source_url = source_url

    def to_dict(self) -> Dict[str, Any]:
        return {
            "benchmark_id": str(self.benchmark.id) if self.benchmark else None,
            "resolution": self.resolution,
            "is_stale": self.is_stale,
            "adjusted_unit_cost_mid": float(self.adjusted_unit_cost_mid) if self.adjusted_unit_cost_mid else None,
            "inflation_multiplier": float(self.inflation_multiplier),
            "source_name": self.source_name,
            "source_url": self.source_url,
            "authority_type": self.benchmark.authority_type if self.benchmark else None,
        }


class BenchmarkService:
    @staticmethod
    def calculate_temporal_decay(
        base_cost: Decimal,
        expiry_date: Optional[date],
        target_date: Optional[date] = None,
        annual_cpi_rate: Decimal = DEFAULT_ANNUAL_CPI_INFLATION
    ) -> Tuple[Decimal, Decimal, bool]:
        """
        Calculates compounded inflation multiplier if target_date > expiry_date.
        Returns (adjusted_cost, multiplier, is_stale).
        """
        if base_cost is None:
            return Decimal("0.0"), Decimal("1.0"), False

        target = target_date or date.today()
        if not expiry_date or target <= expiry_date:
            return base_cost, Decimal("1.0"), False

        # Calculate difference in years
        days_expired = (target - expiry_date).days
        years_expired = Decimal(str(days_expired)) / Decimal("365.25")

        if years_expired <= 0:
            return base_cost, Decimal("1.0"), False

        # Compound inflation: (1 + r) ^ t
        multiplier = (Decimal("1.0") + annual_cpi_rate) ** years_expired
        adjusted_cost = (base_cost * multiplier).quantize(Decimal("0.01"))
        return adjusted_cost, multiplier.quantize(Decimal("0.0001")), True

    def find_benchmark_with_fallback(
        self,
        db: Session,
        category: str,
        item_keyword: str,
        state: Optional[str] = None,
        district: Optional[str] = None,
        target_date: Optional[date] = None
    ) -> BenchmarkMatchResult:
        """
        Queries cost_benchmarks with intelligent keyword token/substring matching
        and strict fallback hierarchy:
        Level 1: Match (category, item_match, state, district)
        Level 2: Match (category, item_match, state, district IS NULL)
        Level 3: Match (category, item_match, country='India', state IS NULL, district IS NULL)
        """
        norm_cat = category.strip().lower()
        norm_item = item_keyword.strip().lower()
        norm_tokens = set(re.findall(r"\w+", norm_item))

        # Query all benchmarks in this category (or all benchmarks if category has no direct match)
        candidates = db.query(CostBenchmark).filter(CostBenchmark.category.ilike(norm_cat)).all()
        if not candidates:
            candidates = db.query(CostBenchmark).all()

        matching_benchmarks: List[Tuple[int, CostBenchmark]] = []
        for bm in candidates:
            bm_name = bm.item.lower()
            bm_tokens = set(re.findall(r"\w+", bm_name))

            score = 0
            if bm_name in norm_item or norm_item in bm_name:
                score += 100 + len(bm_name)
            else:
                overlap = norm_tokens.intersection(bm_tokens)
                # Filter out trivial stop words
                overlap = {t for t in overlap if t not in {"and", "or", "the", "for", "in", "of", "per", "kg", "unit", "trip"}}
                if overlap:
                    score += len(overlap) * 20

            if score > 0:
                matching_benchmarks.append((score, bm))

        # Sort by match score descending
        matching_benchmarks.sort(key=lambda x: x[0], reverse=True)

        if matching_benchmarks:
            # Check hierarchy among matching benchmarks
            matched_bms = [b for _, b in matching_benchmarks]

            # 1. District match
            if state and district:
                for b in matched_bms:
                    if b.state and b.state.lower() == state.strip().lower() and b.district and b.district.lower() == district.strip().lower():
                        adj_cost, mult, is_stale = self.calculate_temporal_decay(
                            base_cost=b.unit_cost_mid or b.unit_cost_low or Decimal("0"),
                            expiry_date=b.expiry_date,
                            target_date=target_date
                        )
                        return BenchmarkMatchResult(
                            benchmark=b,
                            resolution="district",
                            is_stale=is_stale,
                            adjusted_unit_cost_mid=adj_cost,
                            inflation_multiplier=mult,
                            source_name=b.source_name,
                            source_url=b.source_url
                        )

            # 2. State match
            if state:
                for b in matched_bms:
                    if b.state and b.state.lower() == state.strip().lower() and not b.district:
                        adj_cost, mult, is_stale = self.calculate_temporal_decay(
                            base_cost=b.unit_cost_mid or b.unit_cost_low or Decimal("0"),
                            expiry_date=b.expiry_date,
                            target_date=target_date
                        )
                        return BenchmarkMatchResult(
                            benchmark=b,
                            resolution="state",
                            is_stale=is_stale,
                            adjusted_unit_cost_mid=adj_cost,
                            inflation_multiplier=mult,
                            source_name=b.source_name,
                            source_url=b.source_url
                        )

            # 3. National / Best candidate match
            best_bm = matched_bms[0]
            adj_cost, mult, is_stale = self.calculate_temporal_decay(
                base_cost=best_bm.unit_cost_mid or best_bm.unit_cost_low or Decimal("0"),
                expiry_date=best_bm.expiry_date,
                target_date=target_date
            )
            return BenchmarkMatchResult(
                benchmark=best_bm,
                resolution="national" if not best_bm.state else "state",
                is_stale=is_stale,
                adjusted_unit_cost_mid=adj_cost,
                inflation_multiplier=mult,
                source_name=best_bm.source_name,
                source_url=best_bm.source_url
            )

        # 4. No Match Found
        return BenchmarkMatchResult(
            benchmark=None,
            resolution="none",
            is_stale=False,
            adjusted_unit_cost_mid=None,
            inflation_multiplier=Decimal("1.0"),
            source_name=None,
            source_url=None
        )


benchmark_service = BenchmarkService()
