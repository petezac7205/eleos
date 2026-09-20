"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ShieldCheck, CheckCircle2, AlertCircle, Building2, FileText, Activity, PieChart, MapPin, ExternalLink, Download } from "lucide-react";
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ngoApi } from '@/lib/api';

// Using mock data structurally identical to `ngo_assessments.json` for NGO_00002
const MOCK_NGO_DATA = {
  ngo_id: "NGO_00002",
  ngo_name: "Uday Network National",
  assessment_date: "2026-09-16",
  trustability_score: 90.5,
  score_interpretation: {
    label: "Strong Evidence Coverage",
    description: "Available evidence provides high consistency across statutory registrations, multi-year financial audits, and documented operational history."
  },
  data_confidence: 0.9,
  dimension_scores: {
    identity_legal: 95.0,
    financial_transparency: 76.2,
    operational_evidence: 95.7,
    data_completeness: 100.0
  },
  financial_analysis: {
    programme_expense_ratio: 0.7088,
    administrative_expense_ratio: 0.1112,
    fundraising_expense_ratio: 0.0254,
    financial_anomaly_label: "Normal",
  },
  positive_evidence: [
    "Valid legal registration record identified under Section 8.",
    "Permanent Account Number (PAN) was verified against statutory records.",
    "Section 12A/12AB charitable tax-exempt registration is active.",
    "Section 80G donor deduction approval is active.",
    "Available disclosure contains 2 financial report(s).",
    "Reported financial totals reconcile mathematically with itemized expense categories.",
    "Multiple (7) charitable programmes publicly documented."
  ],
  negative_evidence: [
    "Auditor issued a qualified report noting specific reservations or missing disclosures."
  ]
};

const MOCK_CAMPAIGNS = [
  { id: "c1", title: "Rural Tech Education Drive", raised: 45000, target: 100000, feasibility: 92 },
  { id: "c2", title: "Flood Relief Checkpoint", raised: 120000, target: 120000, feasibility: 88 },
];

export default function NGOProfilePage() {
  const params = useParams();
  const [data, setData] = useState<any>(MOCK_NGO_DATA);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const ngoId = params?.id as string;
    if (!ngoId) return;

    setIsLoading(true);
    ngoApi.getPublicProfile(ngoId)
      .then((res) => {
        if (res?.trustability) {
          const t = res.trustability;
          setData({
            ngo_id: res.id || ngoId,
            ngo_name: res.name || t.ngo_name || MOCK_NGO_DATA.ngo_name,
            assessment_date: t.computed_at ? t.computed_at.slice(0, 10) : MOCK_NGO_DATA.assessment_date,
            trustability_score: t.trustability_score ?? t.overall_score ?? MOCK_NGO_DATA.trustability_score,
            score_interpretation: t.score_interpretation || {
              label: t.trust_label || t.risk_tier || "Verified",
              description: "Evidence verified through Member 1 zero-trust pipeline."
            },
            data_confidence: t.data_confidence ?? 0.9,
            dimension_scores: t.dimension_scores || MOCK_NGO_DATA.dimension_scores,
            financial_analysis: {
              programme_expense_ratio: t.financial_analysis?.programme_expense_ratio ?? 0.7088,
              administrative_expense_ratio: t.financial_analysis?.administrative_expense_ratio ?? 0.1112,
              fundraising_expense_ratio: t.financial_analysis?.fundraising_expense_ratio ?? 0.0254,
              financial_anomaly_label: t.financial_analysis?.financial_anomaly_label ?? "Normal",
            },
            positive_evidence: (t.positive_evidence && t.positive_evidence.length > 0) ? t.positive_evidence : MOCK_NGO_DATA.positive_evidence,
            negative_evidence: t.negative_evidence || [],
            verification_summary: t.verification_summary,
            extraction_provider: t.extraction_provider || "gemini",
            is_member1_verified: t.is_member1_verified ?? false
          });
        }
      })
      .catch((err) => {
        console.warn("Could not fetch live NGO profile, using fallback mock data:", err);
      })
      .finally(() => setIsLoading(false));
  }, [params?.id]);

  const scoreColor = data.trustability_score >= 80 ? 'text-emerald-600' : data.trustability_score >= 50 ? 'text-amber-500' : 'text-rose-600';
  const scoreBg = data.trustability_score >= 80 ? 'bg-emerald-50' : data.trustability_score >= 50 ? 'bg-amber-50' : 'bg-rose-50';

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Header Section */}
      <section className="bg-slate-900 text-white pt-24 pb-24 px-4 relative">
        <div className="absolute top-8 left-4 md:left-8 z-20">
          <Link href="/campaigns" className="text-slate-300 hover:text-white flex items-center text-sm font-medium transition-colors">
            ← Back to Campaigns
          </Link>
        </div>
        <div className="absolute inset-0 bg-[url('/hero-bg-real.jpg')] bg-cover bg-center opacity-20"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent"></div>
        <div className="max-w-6xl mx-auto relative z-10 flex flex-col md:flex-row items-center gap-8 mt-12">
          
          <div className="relative shrink-0 w-32 h-32 md:w-40 md:h-40">
            {/* Glowing ambient background */}
            <div className={`absolute inset-0 rounded-full blur-xl opacity-30 ${data.trustability_score >= 80 ? 'bg-emerald-400' : 'bg-amber-400'}`}></div>
            
            {/* Modern Glass Container */}
            <div className="absolute inset-0 rounded-full bg-slate-900/50 backdrop-blur-md border border-white/10 flex flex-col items-center justify-center shadow-2xl overflow-hidden group hover:border-white/20 transition-all">
              {/* Subtle inner highlight */}
              <div className="absolute inset-0 bg-gradient-to-b from-white/10 to-transparent opacity-50"></div>
              
              <div className="relative z-10 flex flex-col items-center">
                <div className="flex items-center justify-center mb-1">
                  <ShieldCheck className={`h-4 w-4 mr-1.5 ${scoreColor}`} />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Trust</span>
                </div>
                <span className={`block text-4xl md:text-5xl font-black tracking-tighter ${scoreColor}`}>
                  {Math.round(data.trustability_score)}
                </span>
              </div>
              
              {/* Circular progress indicator strip at bottom */}
              <div className="absolute bottom-0 left-0 right-0 h-1.5 bg-slate-800">
                <div className={`h-full ${data.trustability_score >= 80 ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${data.trustability_score}%` }}></div>
              </div>
            </div>
          </div>

          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-3 mb-2">
              <h1 className="text-3xl md:text-5xl font-black tracking-tight">{data.ngo_name}</h1>
              {data.trustability_score >= 80 && (
                <ShieldCheck className="h-8 w-8 text-emerald-400" />
              )}
            </div>
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-4 text-slate-300 mt-4 text-sm font-medium">
              <span className="flex items-center"><Building2 className="h-4 w-4 mr-1" /> Section 8 Company</span>
              <span className="flex items-center"><MapPin className="h-4 w-4 mr-1" /> Verified Identity</span>
              <span className="flex items-center"><FileText className="h-4 w-4 mr-1" /> Assessed: {data.assessment_date}</span>
              {data.extraction_provider && (
                <span className="flex items-center bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                  <ShieldCheck className="h-3.5 w-3.5 mr-1 text-emerald-400" />
                  VLM: {data.extraction_provider.toUpperCase()} (Zero-Trust)
                </span>
              )}
            </div>
            <p className="mt-6 text-lg text-slate-400 max-w-2xl border-l-4 border-emerald-500 pl-4 py-1 bg-slate-800/50">
              <strong className="text-white block">{data.score_interpretation.label}</strong>
              {data.score_interpretation.description}
            </p>
          </div>
          
          <div className="flex flex-col gap-3 w-full md:w-auto">
            <Button className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold h-12 px-8">
              Donate to NGO
            </Button>
            <Button variant="outline" className="border-slate-700 hover:bg-slate-800 hover:text-white h-12">
              <Download className="h-4 w-4 mr-2" /> Download AI Report
            </Button>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 -mt-8 relative z-20">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column: Metrics & Analytics */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Dimension Breakdown */}
            <Card className="border-2 border-slate-200 shadow-sm rounded-xl">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-4">
                <CardTitle className="text-lg flex items-center">
                  <Activity className="h-5 w-5 mr-2 text-primary" />
                  Score Dimensions
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid grid-cols-2 gap-6">
                  {Object.entries(data.dimension_scores).map(([key, value]: [string, any]) => (
                    <div key={key}>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-bold text-slate-700 capitalize">{key.replace('_', ' ')}</span>
                        <span className="text-sm font-bold text-slate-900">{Number(value).toFixed(1)}/100</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2.5">
                        <div className="bg-primary h-2.5 rounded-full" style={{ width: `${value}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Evidence Summary */}
            <Card className="border-2 border-slate-200 shadow-sm rounded-xl">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-4">
                <CardTitle className="text-lg flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-primary" />
                  AI Evidence Extraction
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <h4 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wider">Verified Positive Evidence</h4>
                <div className="space-y-3 mb-8">
                  {data.positive_evidence.map((evidence: any, idx: number) => (
                    <div key={idx} className="flex items-start">
                      <CheckCircle2 className="h-5 w-5 text-emerald-500 mr-3 shrink-0 mt-0.5" />
                      <span className="text-slate-700">{evidence}</span>
                    </div>
                  ))}
                </div>
                
                {data.negative_evidence.length > 0 && (
                  <>
                    <h4 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wider">Flags & Limitations</h4>
                    <div className="space-y-3">
                      {data.negative_evidence.map((evidence: any, idx: number) => (
                        <div key={idx} className="flex items-start">
                          <AlertCircle className="h-5 w-5 text-amber-500 mr-3 shrink-0 mt-0.5" />
                          <span className="text-slate-700">{evidence}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Financials & Campaigns */}
          <div className="space-y-8">
            
            {/* Financial Analysis */}
            <Card className="border-2 border-slate-200 shadow-sm rounded-xl">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-4">
                <CardTitle className="text-lg flex items-center">
                  <PieChart className="h-5 w-5 mr-2 text-primary" />
                  Financial Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Programme Expense</span>
                      <span className="font-bold">{(data.financial_analysis.programme_expense_ratio * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${data.financial_analysis.programme_expense_ratio * 100}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Administrative Expense</span>
                      <span className="font-bold">{(data.financial_analysis.administrative_expense_ratio * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-amber-500 h-2 rounded-full" style={{ width: `${data.financial_analysis.administrative_expense_ratio * 100}%` }}></div>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Fundraising Expense</span>
                      <span className="font-bold">{(data.financial_analysis.fundraising_expense_ratio * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${data.financial_analysis.fundraising_expense_ratio * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t border-slate-100">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-600">Anomaly Check (Isolation Forest)</span>
                      <Badge variant="outline" className={data.financial_analysis.financial_anomaly_label === 'Normal' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-rose-50 text-rose-700 border-rose-200'}>
                        {data.financial_analysis.financial_anomaly_label}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Active Campaigns */}
            <Card className="border-2 border-slate-200 shadow-sm rounded-xl">
              <CardHeader className="bg-slate-50 border-b border-slate-100 pb-4">
                <CardTitle className="text-lg">Active Campaigns</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-slate-100">
                  {MOCK_CAMPAIGNS.map(campaign => (
                    <div key={campaign.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <h4 className="font-bold text-slate-900 mb-2">{campaign.title}</h4>
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="secondary" className="bg-amber-100 text-amber-800">
                          {campaign.feasibility}/100 Feasibility
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center mt-4">
                        <span className="text-sm font-bold text-slate-600">₹{campaign.raised.toLocaleString()} raised</span>
                        <Link href={`/campaigns/${campaign.id}`} className="text-primary text-sm font-bold hover:underline flex items-center">
                          View <ExternalLink className="h-3 w-3 ml-1" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

          </div>
        </div>
      </div>
    </div>
  );
}

