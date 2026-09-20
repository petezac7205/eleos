"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CircularScore } from "@/components/ngo/CircularScore";
import {
  Plus,
  Clock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Building2,
  FolderOpen,
  TrendingUp,
  ChevronRight,
} from "lucide-react";
import { ngoApi, campaignsApi, Campaign, NGOProfileData } from "@/lib/api";

// ── Status badge helper ────────────────────────────────────────────────────────
function CampaignStatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { label: string; className: string }> = {
    active: { label: "Active", className: "bg-emerald-100 text-emerald-800 border-emerald-200" },
    pending_review: { label: "Under review", className: "bg-amber-100 text-amber-800 border-amber-200" },
    draft: { label: "Draft", className: "bg-slate-100 text-slate-600 border-slate-200" },
    funded: { label: "Funded", className: "bg-blue-100 text-blue-800 border-blue-200" },
    completed: { label: "Completed", className: "bg-emerald-100 text-emerald-800 border-emerald-200" },
    paused: { label: "Paused", className: "bg-slate-100 text-slate-600 border-slate-200" },
  };
  const s = cfg[status] ?? { label: status, className: "bg-slate-100 text-slate-500 border-slate-200" };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold border ${s.className}`}>
      {s.label}
    </span>
  );
}

// ── Campaign mini-card ─────────────────────────────────────────────────────────
function CampaignMiniCard({ campaign }: { campaign: Campaign }) {
  const percent = campaign.funding_percentage
    ? Math.min(100, Math.round(campaign.funding_percentage))
    : Math.min(100, Math.round(((campaign.current_amount ?? 0) / (campaign.target_amount || 1)) * 100));

  return (
    <Link href={`/ngo/campaigns/${campaign.id}`} className="group block">
      <div className="flex items-center gap-4 p-4 rounded-xl border border-slate-200 bg-white hover:border-emerald-200 hover:shadow-sm transition-all">
        {/* ELEOS score dot */}
        <div className="shrink-0">
          {campaign.ngo_trust_score != null ? (
            <CircularScore score={campaign.ngo_trust_score} variant="eleos" size="sm" showLabel={false} />
          ) : (
            <div className="w-12 h-12 rounded-full border-2 border-dashed border-slate-300 flex items-center justify-center">
              <Clock className="w-4 h-4 text-slate-400" />
            </div>
          )}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-semibold text-slate-900 truncate">{campaign.title}</h3>
            <CampaignStatusBadge status={campaign.status} />
          </div>
          <div className="flex items-center gap-2">
            <Progress
              value={percent}
              className="h-1.5 flex-1 bg-slate-100 [&_[data-slot=progress-indicator]]:bg-emerald-500"
            />
            <span className="text-xs text-slate-500 shrink-0">{percent}% funded</span>
          </div>
        </div>

        <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-emerald-500 transition-colors shrink-0" />
      </div>
    </Link>
  );
}

// ── Main dashboard ─────────────────────────────────────────────────────────────
export default function NgoDashboard() {
  const [profile, setProfile] = useState<NGOProfileData | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [prof, camps] = await Promise.all([
        ngoApi.getMeProfile().catch(() => null),
        campaignsApi.list().catch(() => []),
      ]);
      setProfile(prof);
      setCampaigns(camps);
      setIsLoading(false);
    };
    load();
  }, []);

  const isVerified = profile?.verification_status === "verified";
  const isPending = profile?.verification_status === "pending";
  const isUnsubmitted = !profile || profile.verification_status === "unsubmitted";

  const activeCampaigns = campaigns.filter((c) => c.status === "active");
  const totalRaised = campaigns.reduce((sum, c) => sum + (c.current_amount ?? c.raised_amount ?? 0), 0);
  const recentCampaigns = campaigns.slice(0, 3);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[0, 1, 2].map((i) => <div key={i} className="h-28 bg-slate-200 rounded-xl" />)}
        </div>
        <div className="h-48 bg-slate-200 rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-8">

      {/* ── Welcome header ─────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-start gap-4 justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">
            {isVerified ? `Welcome back` : "Organisation Dashboard"}
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            {profile?.name ?? "Your NGO Portal"}
          </p>
        </div>
        {isVerified && (
          <Link
            href="/ngo/campaigns/new"
            className={buttonVariants({ className: "bg-emerald-600 hover:bg-emerald-700 text-white shrink-0 gap-2" })}
          >
            <Plus className="w-4 h-4" />
            Create Campaign
          </Link>
        )}
      </div>

      {/* ── Verification state banners ─────────────────────────────────────── */}
      {isUnsubmitted && (
        <div className="p-6 rounded-2xl border-2 border-dashed border-slate-300 bg-white flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center shrink-0">
            <Building2 className="w-6 h-6 text-slate-500" />
          </div>
          <div className="flex-1">
            <h2 className="font-bold text-slate-900">Complete your organisation registration</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Register your organisation once to unlock campaign creation. It takes about 5 minutes.
            </p>
          </div>
          <Link
            href="/ngo/register"
            className={buttonVariants({ className: "bg-emerald-600 hover:bg-emerald-700 text-white shrink-0" })}
          >
            Start registration
            <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>
      )}

      {isPending && (
        <div className="p-5 rounded-xl border border-amber-200 bg-amber-50 flex items-start gap-4">
          <Clock className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-amber-900">Verification in progress</p>
            <p className="text-sm text-amber-800 mt-0.5">
              We've received your organisation details and documents. We're reviewing them now. 
              You'll be able to create campaigns once your organisation has been verified.
            </p>
          </div>
        </div>
      )}

      {/* ── Organisation card (verified) ───────────────────────────────────── */}
      {isVerified && profile && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Trust Score card */}
          <Card className="border-blue-100 bg-gradient-to-br from-blue-50 to-white">
            <CardContent className="p-5">
              <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-3">Organisation</p>
              <div className="flex items-center gap-4 mb-3">
                <CircularScore
                  score={profile.trust_score ?? 0}
                  variant="trust"
                  size="md"
                />
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-xs text-slate-600 font-medium">Verified organisation</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                This score reflects ELEOS's review of your organisation — not any individual campaign.
              </p>
              <Link href="/ngo/organisation" className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-3">
                View details <ChevronRight className="w-3 h-3" />
              </Link>
            </CardContent>
          </Card>

          {/* Active campaigns stat */}
          <Card className="border-slate-200 bg-white">
            <CardContent className="p-5 flex flex-col h-full">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Active Campaigns</p>
              <div className="flex items-end gap-2 mb-2">
                <span className="text-4xl font-extrabold text-slate-900 font-mono">{activeCampaigns.length}</span>
                <span className="text-sm text-slate-400 mb-1">of {campaigns.length} total</span>
              </div>
              <div className="flex items-center gap-1.5 mt-auto">
                <FolderOpen className="w-3.5 h-3.5 text-slate-400" />
                <Link href="/ngo/campaigns" className="text-xs text-emerald-600 hover:underline">
                  View all campaigns
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Total raised stat */}
          <Card className="border-slate-200 bg-white">
            <CardContent className="p-5 flex flex-col h-full">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3">Total Raised</p>
              <div className="mb-2">
                <span className="text-3xl font-extrabold text-slate-900 font-mono">
                  ₹{totalRaised.toLocaleString("en-IN")}
                </span>
              </div>
              <p className="text-xs text-slate-400">Across all campaigns on ELEOS</p>
              <div className="flex items-center gap-1.5 mt-auto">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                <span className="text-xs text-slate-500">Fundraising total</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Campaigns section ──────────────────────────────────────────────── */}
      {isVerified && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-slate-900">Your campaigns</h2>
            <div className="flex items-center gap-2">
              <Link href="/ngo/campaigns" className="text-xs text-slate-500 hover:text-emerald-600 transition-colors">
                View all
              </Link>
              <Link
                href="/ngo/campaigns/new"
                className={buttonVariants({
                  size: "sm",
                  variant: "outline",
                  className: "gap-1.5 border-emerald-200 text-emerald-700 hover:bg-emerald-50",
                })}
              >
                <Plus className="w-3.5 h-3.5" />
                New campaign
              </Link>
            </div>
          </div>

          {recentCampaigns.length === 0 ? (
            <div className="p-10 rounded-2xl border-2 border-dashed border-slate-200 bg-white text-center">
              <FolderOpen className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="font-semibold text-slate-700">No campaigns yet</p>
              <p className="text-sm text-slate-400 mt-1 mb-4">
                Create your first campaign to start raising funds.
              </p>
              <Link
                href="/ngo/campaigns/new"
                className={buttonVariants({ className: "bg-emerald-600 hover:bg-emerald-700 text-white" })}
              >
                Create your first campaign
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {recentCampaigns.map((camp) => (
                <CampaignMiniCard key={camp.id} campaign={camp} />
              ))}
              {campaigns.length > 3 && (
                <Link
                  href="/ngo/campaigns"
                  className="block text-center text-sm text-emerald-600 hover:underline py-2"
                >
                  View all {campaigns.length} campaigns →
                </Link>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Score distinction callout ──────────────────────────────────────── */}
      {isVerified && campaigns.some((c) => c.ngo_trust_score != null) && (
        <div className="p-5 rounded-xl border border-slate-200 bg-white">
          <h3 className="text-sm font-bold text-slate-800 mb-3">Understanding your scores</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50 border border-blue-100">
              <div className="w-8 h-8 rounded-full bg-blue-200 flex items-center justify-center shrink-0">
                <Building2 className="w-4 h-4 text-blue-700" />
              </div>
              <div>
                <p className="text-sm font-bold text-blue-900">Trust Score</p>
                <p className="text-xs text-blue-700 mt-0.5">About your organisation — its identity and compliance record.</p>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 rounded-lg bg-emerald-50 border border-emerald-100">
              <div className="w-8 h-8 rounded-full bg-emerald-200 flex items-center justify-center shrink-0">
                <FolderOpen className="w-4 h-4 text-emerald-700" />
              </div>
              <div>
                <p className="text-sm font-bold text-emerald-900">ELEOS Score</p>
                <p className="text-xs text-emerald-700 mt-0.5">About each campaign — how well-defined and realistic the plan is.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
