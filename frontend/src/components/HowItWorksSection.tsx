"use client";

import Link from "next/link";
import { Reveal } from "@/components/ui/Reveal";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

// ── Step definitions ────────────────────────────────────────────────────────

const STEPS = [
  {
    number: "01",
    label: "AI Evaluation",
    title: "Every NGO is scored before you give",
    body: "We replace guesswork with data. Our hybrid AI evaluates NGOs to establish a baseline Trust Score for legitimacy, while individual campaigns are rigorously analyzed to generate an Eleos Feasibility Score you can rely on.",
    image: "/svgs/analytics.svg",
    imageAlt: "Analytics dashboard illustration",
    imageOnLeft: true,
    // which direction does the path travel to reach the NEXT illustration?
    connector: "ltr" as const,
  },
  {
    number: "02",
    label: "Your Choice",
    title: "You choose what matters to you",
    body: "Browse campaigns with full transparency. You'll see the Eleos Score, a clear funding goal, and exactly what your money will fund — no vague promises, no hidden fees, no surprises.",
    image: "/svgs/choose.svg",
    imageAlt: "Campaign selection illustration",
    imageOnLeft: false,
    connector: "rtl" as const,
  },
  {
    number: "03",
    label: "On-Chain Record",
    title: "Your donation is recorded forever",
    body: "The moment you give, your donation is written to the Polygon blockchain — a permanent public record that no one can alter, remove, or tamper with. Not even us.",
    image: "/svgs/donation.svg",
    imageAlt: "Donation illustration",
    imageOnLeft: true,
    connector: "ltr" as const,
  },
  {
    number: "04",
    label: "Verified Impact",
    title: "Cryptographic proof of impact",
    body: "No more taking their word for it. Every milestone, expense, and impact report is verified by independent auditors and immutably anchored to a public ledger for total transparency.",
    image: "/svgs/payments.svg",
    imageAlt: "Milestone verification illustration",
    imageOnLeft: false,
    connector: null, // last step — no connector
  },
] as const;

// ── Animated path connector ─────────────────────────────────────────────────
// A bezier curve that snakes from one side of the layout to the other,
// drawn progressively via stroke-dashoffset as it enters the viewport.

function PathConnector({ direction }: { direction: "ltr" | "rtl" }) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const pathRef = useRef<SVGPathElement>(null);
  const [drawn, setDrawn] = useState(false);

  useEffect(() => {
    const path = pathRef.current;
    const wrap = wrapRef.current;
    if (!path || !wrap) return;

    // Set initial dash state so the path is invisible
    const len = path.getTotalLength();
    path.style.strokeDasharray = `${len}`;
    path.style.strokeDashoffset = `${len}`;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setDrawn(true);
          // rAF ensures the initial invisible state is painted before animating
          requestAnimationFrame(() => {
            path.style.transition =
              "stroke-dashoffset 1.3s cubic-bezier(0.4, 0, 0.2, 1)";
            path.style.strokeDashoffset = "0";
          });
          observer.disconnect();
        }
      },
      { threshold: 0.5 }
    );
    observer.observe(wrap);
    return () => observer.disconnect();
  }, []);

  // Fixed 440×80 canvas.
  // LTR: curve leaves from illustration-left zone (x≈100) → illustration-right zone (x≈340)
  // RTL: curve leaves from right (x≈340) → left (x≈100)
  const isLTR = direction === "ltr";
  const startX = isLTR ? 100 : 340;
  const endX = isLTR ? 340 : 100;
  const d = `M ${startX},0 C ${startX},40 ${endX},40 ${endX},80`;

  // Alternate emerald ↔ violet for visual rhythm
  const color = isLTR ? "#059669" : "#7c3aed";

  return (
    <div
      ref={wrapRef}
      className="hidden md:flex justify-center pointer-events-none select-none py-2 overflow-visible"
      aria-hidden="true"
    >
      <svg
        width="440"
        height="104"
        viewBox="-12 -12 464 104"
        fill="none"
        overflow="visible"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* ── Journey path ── */}
        <path
          ref={pathRef}
          d={d}
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          opacity="0.45"
        />

        {/* ── Origin node (appears as path starts drawing) ── */}
        <circle
          cx={startX}
          cy={2}
          r={4}
          fill={color}
          style={{
            opacity: drawn ? 0.75 : 0,
            transition: "opacity 0.3s ease 0.2s",
          }}
        />
        {/* Origin ring */}
        <circle
          cx={startX}
          cy={2}
          r={8}
          stroke={color}
          strokeWidth="1"
          fill="none"
          style={{
            opacity: drawn ? 0.25 : 0,
            transition: "opacity 0.3s ease 0.35s",
          }}
        />

        {/* ── Destination node (appears as path finishes) ── */}
        <circle
          cx={endX}
          cy={78}
          r={4}
          fill={color}
          style={{
            opacity: drawn ? 0.75 : 0,
            transition: "opacity 0.3s ease 1.2s",
          }}
        />
        {/* Destination ring — subtle glow */}
        <circle
          cx={endX}
          cy={78}
          r={8}
          stroke={color}
          strokeWidth="1"
          fill="none"
          style={{
            opacity: drawn ? 0.25 : 0,
            transition: "opacity 0.3s ease 1.35s",
          }}
        />
      </svg>
    </div>
  );
}

// ── Single step row ─────────────────────────────────────────────────────────

function StepRow({
  step,
}: {
  step: (typeof STEPS)[number];
}) {
  const imgOnLeft = step.imageOnLeft;

  return (
    <div>
      <Reveal>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-20 items-center py-8">
          {/* Illustration */}
          <div
            className={[
              "flex items-center justify-center h-56 md:h-72",
              // On mobile: always first (image on top).
              // On desktop: honour imageOnLeft.
              "order-first",
              imgOnLeft ? "md:order-first" : "md:order-last",
            ].join(" ")}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={step.image}
              alt={step.imageAlt}
              className="w-full max-w-xs h-full object-contain drop-shadow-sm"
              loading="lazy"
            />
          </div>

          {/* Content */}
          <div
            className={[
              "order-last",
              imgOnLeft ? "md:order-last" : "md:order-first",
            ].join(" ")}
          >
            {/* Step badge */}
            <div className="flex items-center gap-3 mb-5">
              <span className="text-xs font-mono font-bold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2.5 py-1 rounded-md">
                {step.number}
              </span>
              <span className="text-xs uppercase tracking-widest text-slate-400 font-semibold">
                {step.label}
              </span>
            </div>

            <h3 className="text-2xl md:text-3xl font-bold text-slate-900 mb-4 leading-snug">
              {step.title}
            </h3>
            <p className="text-slate-500 leading-relaxed text-base max-w-md">
              {step.body}
            </p>
          </div>
        </div>
      </Reveal>

      {/* Connector path to the next step */}
      {step.connector && <PathConnector direction={step.connector} />}
    </div>
  );
}

// ── Section ─────────────────────────────────────────────────────────────────

export function HowItWorksSection() {
  return (
    <section className="py-24 bg-white border-t border-slate-100">
      <div className="container mx-auto px-4">

        {/* Header */}
        <Reveal className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-emerald-600 text-xs font-pixel uppercase tracking-widest mb-4">
            Our Solution
          </p>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight text-slate-900 mb-4">
            Your money. Tracked.{" "}
            <span className="text-emerald-600">Verified. Proven.</span>
          </h2>
          <p className="text-slate-500 text-lg">
            Here&apos;s exactly how ELEOS ensures every rupee reaches its
            destination — and how you can see the proof yourself.
          </p>
        </Reveal>

        {/* Steps with animated connectors */}
        <div className="max-w-4xl mx-auto">
          {STEPS.map((step) => (
            <StepRow key={step.number} step={step} />
          ))}
        </div>

        {/* CTA */}
        <Reveal delay={150} className="text-center mt-16">
          <Link href="/explorer">
            <Button
              variant="outline"
              className="gap-2 border-emerald-200 text-emerald-700 hover:bg-emerald-50 hover:border-emerald-400 transition-colors"
            >
              See the live proof on-chain <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </Reveal>

      </div>
    </section>
  );
}

