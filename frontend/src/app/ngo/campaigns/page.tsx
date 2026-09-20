"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CircularScore } from "@/components/ngo/CircularScore";
import { Plus, FolderOpen, MapPin, Calendar, Clock, ChevronRight } from "lucide-react";
import { campaignsApi, Campaign } from "@/lib/api";

// ── Status badge ───────────────────────────────────────────────────────────────
function CampaignStatusBadge({ status }: { status: string }) {
  const cfg: Record<string, string> = {
    active: "bg-emerald-100 text-emerald-800 border-emerald-200",
    pending_review: "bg-amber-100 text-amber-800 border-amber-200",
    draft: "bg-slate-100 text-slate-600 border-slate-200",
    funded: "bg-blue-100 text-blue-800 border-blue-200",
    completed: "bg-emerald-100 text-emerald-800 border-emerald-200",
    paused: "bg-slate-100 text-slate-500 border-slate-200",
  };
  const label: Record<string, string> = {
    active: "Active",
    pending_review: "Under review",
    draft: "Draft",
    funded: "Funded",
    completed: "Completed",
    paused: "Paused",
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold border ${cfg[status] ?? "bg-slate-100 text-slate-500 border-slate-200"}`}>
      {label[status] ?? status}
    </span>
  );
}

// ── Campaign card ──────────────────────────────────────────────────────────────
function CampaignCard({ campaign }: { campaign: Campaign }) {
  const percent = campaign.funding_percentage
    ? Math.min(100, Math.round(campaign.funding_percentage))
    : Math.min(100, Math.round(((campaign.current_amount ?? 0) / (campaign.target_amount || 1)) * 100));

  const raised = campaign.current_amount ?? campaign.raised_amount ?? 0;

  return (
    <Link href={`/ngo/campaigns/${campaign.id}`} className="group block">
      <Card className="border-slate-200 bg-white hover:border-emerald-200 hover:shadow-md transition-all overflow-hidden">
        {/* Cover image strip */}
        {campaign.cover_image_url && (
          <div className="h-32 overflow-hidden">
            <img
              src={campaign.cover_image_url}
              alt=""
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          </div>
        )}
        <CardContent className="p-5 space-y-4">
          {/* Header row */}
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <h3 className="font-bold text-slate-900 text-base leading-tight line-clamp-2">{campaign.title}</h3>
              <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-slate-500">
                {(campaign.state ?? campaign.location_state) && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {campaign.state ?? campaign.location_state}
                  </span>
                )}
                {campaign.created_at && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(campaign.created_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}
                  </span>
                )}
              </div>
            </div>
            <CampaignStatusBadge status={campaign.status} />
          </div>

          {/* Funding progress */}
          <div>
            <div className="flex justify-between text-xs text-slate-600 mb-1.5">
              <span className="font-mono font-semibold text-slate-900">
                ₹{raised.toLocaleString("en-IN")}
              </span>
              <span className="text-slate-400">
                of ₹{(campaign.target_amount).toLocaleString("en-IN")}
              </span>
            </div>
            <Progress
              value={percent}
              className="h-2 [&_[data-slot=progress-track]]:bg-slate-100 [&_[data-slot=progress-indicator]]:bg-emerald-500"
            />
            <div className="flex justify-between text-[11px] text-slate-400 mt-1">
              <span>{percent}% funded</span>
            </div>
          </div>

          {/* ELEOS Score */}
          <div className="flex items-center justify-between pt-1 border-t border-slate-100">
            {campaign.ngo_trust_score != null ? (
              <CircularScore score={campaign.ngo_trust_score} variant="eleos" size="sm" />
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Clock className="w-3.5 h-3.5" />
                <span>Evaluation in progress</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium group-hover:gap-2.5 transition-all">
              Manage <ChevronRight className="w-3.5 h-3.5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

// ── Filters ────────────────────────────────────────────────────────────────────
const STATUS_FILTERS = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "pending_review", label: "Under review" },
  { value: "completed", label: "Completed" },
  { value: "draft", label: "Draft" },
];

// ── Main page ──────────────────────────────────────────────────────────────────
export default function CampaignsListPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");

  useEffect(() => {
    campaignsApi.list().catch(() => []).then((data) => {
      setCampaigns(data);
      setIsLoading(false);
    });
  }, []);

  const filtered = statusFilter
    ? campaigns.filter((c) => c.status === statusFilter)
    : campaigns;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">Your campaigns</h1>
          <p className="text-sm text-slate-500 mt-1">
            {campaigns.length} campaign{campaigns.length !== 1 ? "s" : ""} in total
          </p>
        </div>
        <Link
          href="/ngo/campaigns/new"
          className={buttonVariants({ className: "bg-emerald-600 hover:bg-emerald-700 text-white gap-2 shrink-0" })}
        >
          <Plus className="w-4 h-4" />
          Create Campaign
        </Link>
      </div>

      {/* Filters */}
      {campaigns.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setStatusFilter(f.value)}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                statusFilter === f.value
                  ? "bg-slate-800 text-white border-slate-800"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-400"
              }`}
            >
              {f.label}
              {f.value === "" && ` (${campaigns.length})`}
              {f.value !== "" && ` (${campaigns.filter((c) => c.status === f.value).length})`}
            </button>
          ))}
        </div>
      )}

      {/* Loading skeleton */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 animate-pulse">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-60 bg-slate-200 rounded-xl" />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && filtered.length === 0 && (
        <div className="py-20 flex flex-col items-center text-center">
          <FolderOpen className="w-12 h-12 text-slate-300 mb-4" />
          <h2 className="text-lg font-bold text-slate-700">
            {statusFilter ? "No campaigns match this filter" : "No campaigns yet"}
          </h2>
          <p className="text-sm text-slate-400 mt-1 mb-6 max-w-sm">
            {statusFilter
              ? "Try a different filter."
              : "Create your first campaign to start raising funds for your cause."}
          </p>
          {!statusFilter && (
            <Link
              href="/ngo/campaigns/new"
              className={buttonVariants({ className: "bg-emerald-600 hover:bg-emerald-700 text-white" })}
            >
              Create your first campaign
            </Link>
          )}
        </div>
      )}

      {/* Campaign grid */}
      {!isLoading && filtered.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filtered.map((campaign) => (
            <CampaignCard key={campaign.id} campaign={campaign} />
          ))}
        </div>
      )}
    </div>
  );
}

