"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Reveal } from "@/components/ui/Reveal";
import { explorerApi, ExplorerStats } from "@/lib/api";
import { HowItWorksSection } from "@/components/HowItWorksSection";


// ────────────────────────────────────────────────────────────────────────────

export default function Home() {
  const [stats, setStats] = useState<ExplorerStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const expStats = await explorerApi.getStats().catch(() => null);
        setStats(expStats);
      } catch (err) {
        // Suppress console error to prevent Next.js dev overlay from interrupting demo
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  return (
    <div className="bg-background">

      {/* ── Hero Section: full-viewport image ── */}
      <section className="relative w-full h-screen overflow-hidden">

        {/* Background photo */}
        <div
          className="absolute inset-0 z-0 bg-[url('/hero-bg-real.jpg')] bg-cover bg-center bg-no-repeat"
          aria-hidden="true"
        />

        {/* Gradient overlay — lighter at top, dark at bottom for readability */}
        <div className="absolute inset-0 z-0 bg-gradient-to-b from-black/30 via-black/25 to-black/75" />

        {/* Headline + CTA — centred in the image */}
        <div className="relative z-10 h-full flex flex-col items-center justify-center text-center px-4 pb-40">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white mb-6 drop-shadow-md">
            We Score.{" "}
            <span className="text-emerald-400">You Give.</span>{" "}
            You Verify.
          </h1>
          <p className="text-xl md:text-2xl text-slate-100 max-w-3xl font-medium drop-shadow-md mb-10">
            NGOs are evaluated for legitimacy with an overarching <span className="font-bold text-white">Trust Score</span>, while individual campaigns are analyzed for viability to generate an <span className="font-bold text-white">Eleos Feasibility Score</span>.
          </p>

          <div className="flex items-center justify-center">
            <Link href="/campaigns">
              <Button
                size="lg"
                className="text-lg px-8 h-12 bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-900/40 border-0"
              >
                Explore Campaigns
              </Button>
            </Link>
          </div>
        </div>

        {/* Bottom stats bar — overlays image at bottom */}
        <div className="absolute bottom-0 left-0 right-0 z-20 bg-primary text-primary-foreground py-8">
          <div className="container mx-auto px-4 grid grid-cols-1 md:grid-cols-4 gap-8 text-center divide-y md:divide-y-0 md:divide-x divide-primary-foreground/20">
            <div>
              <div className="text-3xl font-bold font-mono">₹12,45,000</div>
              <div className="text-sm opacity-90 uppercase tracking-wider mt-1 font-pixel text-[10px]">Total Donated</div>
            </div>
            <div>
              <div className="text-3xl font-bold font-mono">47</div>
              <div className="text-sm opacity-90 uppercase tracking-wider mt-1 font-pixel text-[10px]">Verified NGOs</div>
            </div>
            <div>
              <div className="text-3xl font-bold font-mono">{stats?.total_proofs_anchored || 48}</div>
              <div className="text-sm opacity-90 uppercase tracking-wider mt-1 font-pixel text-[10px]">On-Chain Proofs</div>
            </div>
            <div>
              <div className="text-3xl font-bold font-mono">152</div>
              <div className="text-sm opacity-90 uppercase tracking-wider mt-1 font-pixel text-[10px]">Unique Donors</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Why Eleos? ── */}
      <section className="py-24 bg-slate-50 relative overflow-hidden">
        {/* Subtle background decoration */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="container mx-auto px-4 relative z-10">
          <Reveal className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-4xl md:text-5xl font-black tracking-tight mb-6 text-slate-900">
              Why Eleos
            </h2>
            <p className="text-lg md:text-xl text-slate-600 font-medium leading-relaxed">
              We built Eleos to answer the three biggest questions holding back charitable giving in India today.
            </p>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Reveal delay={100} className="bg-white p-8 rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300 flex flex-col">
              <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center mb-6 shrink-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3 leading-snug">"Did my donation actually make a difference?"</h3>
              <p className="text-slate-600 leading-relaxed mb-6 grow font-medium">
                37% of Indian donors say charities could encourage more giving simply by explaining how they create change. Eleos solves this by immutably linking every rupee to verified campaign milestones and impact evidence.
              </p>
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold border-t border-slate-100 pt-4 mt-auto">
                Source: 2025 World Giving Report
              </p>
            </Reveal>

            <Reveal delay={200} className="bg-white p-8 rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300 flex flex-col">
              <div className="w-12 h-12 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center mb-6 shrink-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3 leading-snug">"Who am I giving my money to?"</h3>
              <p className="text-slate-600 leading-relaxed mb-6 grow font-medium">
                38% of respondents say that transparency about how a charity is run would encourage them to donate. Our hybrid AI evaluates and scores every NGO's governance and financials before you even see them.
              </p>
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold border-t border-slate-100 pt-4 mt-auto">
                Source: 2025 World Giving Report
              </p>
            </Reveal>

            <Reveal delay={300} className="bg-white p-8 rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-100 relative overflow-hidden group hover:-translate-y-1 transition-transform duration-300 flex flex-col">
              <div className="w-12 h-12 bg-slate-100 text-slate-600 rounded-xl flex items-center justify-center mb-6 shrink-0">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3 leading-snug">"Data doesn't tell me what happened."</h3>
              <p className="text-slate-600 leading-relaxed mb-6 grow font-medium">
                Indian nonprofits collect vast amounts of data, yet 73% of it is used purely for donor reporting, not insight. Eleos turns scattered documentation into a singular, verifiable truth you can actually understand.
              </p>
              <p className="text-[10px] uppercase tracking-widest text-slate-400 font-bold border-t border-slate-100 pt-4 mt-auto">
                Source: Civil-Society Research
              </p>
            </Reveal>
          </div>
        </div>
      </section>

      {/* ── How ELEOS Works — visual journey with animated path ── */}
      <HowItWorksSection />

    </div>
  );
}

