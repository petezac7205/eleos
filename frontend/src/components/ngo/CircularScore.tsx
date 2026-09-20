/**
 * CircularScore — shared score widget used across the NGO portal.
 *
 * variant="trust"  → blue ring, labelled "Trust Score"
 *                    Represents: "How trustworthy is this organisation?"
 *
 * variant="eleos"  → emerald ring, labelled "ELEOS Score"
 *                    Represents: "How feasible is this specific campaign?"
 *
 * The two variants are intentionally visually distinct so they cannot
 * be confused with each other.
 */

import React from "react";

interface CircularScoreProps {
  score: number;
  variant: "trust" | "eleos";
  size?: "sm" | "md" | "lg";
  tooltip?: string;
  showLabel?: boolean;
}

const VARIANT_CONFIG = {
  trust: {
    ring: "stroke-blue-500",
    track: "stroke-blue-100",
    text: "text-blue-700",
    bg: "bg-blue-50 border-blue-200 hover:border-blue-300",
    label: "Trust Score",
    defaultTooltip:
      "Your Trust Score reflects ELEOS's review of your organisation — including its identity and compliance records. It does not evaluate any individual campaign.",
  },
  eleos: {
    ring: "stroke-emerald-500",
    track: "stroke-slate-100",
    text: "text-slate-800",
    bg: "bg-white border-slate-200/60 hover:border-emerald-200",
    label: "ELEOS Score",
    defaultTooltip:
      "This score is specific to this campaign. It reflects how well-defined and realistic your campaign plan appears.",
  },
} as const;

const SIZE_CONFIG = {
  sm: { circle: "w-12 h-12", radius: 18, strokeWidth: 3, fontSize: "text-xs", cardPadding: "p-2.5 pr-5", labelSize: "text-[12px]" },
  md: { circle: "w-14 h-14", radius: 22, strokeWidth: 4, fontSize: "text-sm", cardPadding: "p-3 pr-6", labelSize: "text-[13px]" },
  lg: { circle: "w-16 h-16", radius: 25, strokeWidth: 4, fontSize: "text-base", cardPadding: "p-4 pr-7", labelSize: "text-sm" },
} as const;

export function CircularScore({
  score,
  variant,
  size = "md",
  tooltip,
  showLabel = true,
}: CircularScoreProps) {
  const cfg = VARIANT_CONFIG[variant];
  const sz = SIZE_CONFIG[size];
  const circumference = 2 * Math.PI * sz.radius;
  const strokeDashoffset = circumference - (Math.min(100, Math.max(0, score)) / 100) * circumference;
  const resolvedTooltip = tooltip ?? cfg.defaultTooltip;

  return (
    <div
      className={`group relative flex items-center gap-3 border rounded-xl shadow-sm hover:shadow-md transition-all cursor-default w-fit ${cfg.bg} ${sz.cardPadding}`}
    >
      {/* Circle */}
      <div className={`relative ${sz.circle} shrink-0 flex items-center justify-center`}>
        <svg className="w-full h-full -rotate-90 absolute inset-0" viewBox={`0 0 ${sz.radius * 2 + 6} ${sz.radius * 2 + 6}`}>
          <circle
            cx={sz.radius + 3}
            cy={sz.radius + 3}
            r={sz.radius}
            className={cfg.track}
            strokeWidth={sz.strokeWidth}
            fill="transparent"
          />
          <circle
            cx={sz.radius + 3}
            cy={sz.radius + 3}
            r={sz.radius}
            className={`${cfg.ring} transition-all duration-1000 ease-out`}
            strokeWidth={sz.strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <span className={`${sz.fontSize} font-bold ${cfg.text} leading-none`}>{score}</span>
      </div>

      {/* Label */}
      {showLabel && (
        <div className="flex flex-col">
          <span className={`${sz.labelSize} font-bold text-slate-900 leading-none`}>{cfg.label}</span>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">/ 100</span>
        </div>
      )}

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 bg-slate-900 text-white text-xs p-3.5 rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20 shadow-xl pointer-events-none text-center leading-relaxed">
        {resolvedTooltip}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-slate-900" />
      </div>
    </div>
  );
}

