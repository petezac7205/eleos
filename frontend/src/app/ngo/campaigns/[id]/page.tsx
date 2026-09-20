"use client";

import React, { useState, useEffect, use } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { CircularScore } from "@/components/ngo/CircularScore";
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Users,
  Target,
  ExternalLink,
  CheckCircle2,
  Clock,
  AlertCircle,
  Video,
  Loader2,
  X,
  ChevronRight,
  TrendingUp,
} from "lucide-react";
import { campaignsApi, explorerApi, ngoApi, Campaign, Milestone, TimelineEvent } from "@/lib/api";

// ── Milestone status display ──────────────────────────────────────────────────
const MILESTONE_STATUS: Record<string, { label: string; icon: React.ReactNode; className: string }> = {
  pending: { label: "Not started", icon: <Clock className="w-4 h-4" />, className: "text-slate-500 bg-slate-50 border-slate-200" },
  funded: { label: "Funded", icon: <CheckCircle2 className="w-4 h-4" />, className: "text-blue-700 bg-blue-50 border-blue-200" },
  in_progress: { label: "In progress", icon: <TrendingUp className="w-4 h-4" />, className: "text-amber-700 bg-amber-50 border-amber-200" },
  evidence_submitted: { label: "Evidence submitted", icon: <CheckCircle2 className="w-4 h-4" />, className: "text-purple-700 bg-purple-50 border-purple-200" },
  review_pending: { label: "Under donor review", icon: <Clock className="w-4 h-4" />, className: "text-purple-700 bg-purple-50 border-purple-200" },
  verified: { label: "Completed", icon: <CheckCircle2 className="w-4 h-4" />, className: "text-emerald-700 bg-emerald-50 border-emerald-200" },
  flagged: { label: "Flagged for review", icon: <AlertCircle className="w-4 h-4" />, className: "text-red-700 bg-red-50 border-red-200" },
};

// ── Milestone card ─────────────────────────────────────────────────────────────
function MilestoneCard({
  milestone,
  index,
  onShareProgress,
}: {
  milestone: Milestone;
  index: number;
  onShareProgress: (m: Milestone) => void;
}) {
  const s = MILESTONE_STATUS[milestone.status] ?? MILESTONE_STATUS.pending;
  const canShare = ["in_progress", "funded"].includes(milestone.status);

  return (
    <div className={`p-5 rounded-xl border ${s.className} transition-all`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="w-8 h-8 rounded-full bg-white border-2 border-current flex items-center justify-center shrink-0 text-sm font-bold">
            {index + 1}
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold text-slate-900 leading-tight">{milestone.title}</h3>
            <div className="flex items-center gap-1.5 mt-1.5">
              {s.icon}
              <span className="text-xs font-medium">{s.label}</span>
            </div>
            {milestone.target_amount > 0 && (
              <p className="text-xs text-slate-500 mt-1">
                Milestone amount: ₹{milestone.target_amount.toLocaleString("en-IN")}
              </p>
            )}
          </div>
        </div>

        {canShare && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onShareProgress(milestone)}
            className="gap-1.5 text-xs shrink-0 border-current text-inherit bg-white/70 hover:bg-white"
          >
            <Video className="w-3.5 h-3.5" />
            Share progress
          </Button>
        )}
      </div>
    </div>
  );
}

// ── Share progress modal ───────────────────────────────────────────────────────
function ShareProgressModal({
  milestone,
  onClose,
  onSubmit,
}: {
  milestone: Milestone;
  onClose: () => void;
  onSubmit: (milestoneId: string, videoUrl: string, note: string) => Promise<void>;
}) {
  const [videoUrl, setVideoUrl] = useState("");
  const [note, setNote] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!videoUrl.trim()) return;
    setIsSubmitting(true);
    try {
      await onSubmit(milestone.id, videoUrl, note);
      setSuccess(true);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <div>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Milestone {milestone.title}</p>
            <h3 className="text-base font-bold text-slate-900 mt-0.5">Share progress with donors</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5">
          {success ? (
            <div className="text-center py-6 space-y-4">
              <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>
              <div>
                <h4 className="font-bold text-slate-900 text-lg">Progress shared!</h4>
                <p className="text-sm text-slate-500 mt-1">
                  Donors who contributed to this campaign will be invited to review this update.
                </p>
              </div>
              <Button onClick={onClose} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white mt-2">
                Done
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-800">
                  Progress video URL <span className="text-red-500">*</span>
                </label>
                <p className="text-xs text-slate-500">
                  Share a video showing progress at this milestone — field visit footage, installation videos, community interactions, etc.
                </p>
                <input
                  type="url"
                  value={videoUrl}
                  onChange={(e) => setVideoUrl(e.target.value)}
                  placeholder="https://..."
                  required
                  className="w-full p-2.5 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-sm font-semibold text-slate-800">Message to donors</label>
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="Tell donors what you've accomplished at this stage and how their support made it possible..."
                  rows={3}
                  className="w-full p-2.5 text-sm rounded-lg border border-slate-300 resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex gap-3 pt-1">
                <Button type="button" variant="outline" onClick={onClose} className="flex-1">
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={isSubmitting || !videoUrl.trim()}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white gap-2"
                >
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Video className="w-4 h-4" />}
                  Share progress
                </Button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Campaign status badge ──────────────────────────────────────────────────────
function CampaignStatusBadge({ status }: { status: string }) {
  const cfg: Record<string, string> = {
    active: "bg-emerald-100 text-emerald-800 border-emerald-200",
    pending_review: "bg-amber-100 text-amber-800 border-amber-200",
    draft: "bg-slate-100 text-slate-600 border-slate-200",
    funded: "bg-blue-100 text-blue-800 border-blue-200",
    completed: "bg-emerald-100 text-emerald-800 border-emerald-200",
  };
  const label: Record<string, string> = {
    active: "Active",
    pending_review: "Under review",
    draft: "Draft",
    funded: "Funded",
    completed: "Completed",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold border ${cfg[status] ?? "bg-slate-100 text-slate-500 border-slate-200"}`}>
      {label[status] ?? status}
    </span>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function CampaignManagePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedMilestone, setSelectedMilestone] = useState<Milestone | null>(null);

  useEffect(() => {
    campaignsApi.getById(id).catch(() => null).then((data) => {
      setCampaign(data);
      setIsLoading(false);
    });
  }, [id]);

  const handleShareProgress = async (milestoneId: string, videoUrl: string, note: string) => {
    await ngoApi.uploadMilestoneVideo(milestoneId, {
      video_url: videoUrl,
      hearty_note_top: note,
      donor_threshold: 500,
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-6 bg-slate-200 rounded w-32" />
        <div className="h-48 bg-slate-200 rounded-xl" />
        <div className="h-32 bg-slate-200 rounded-xl" />
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="py-20 text-center">
        <AlertCircle className="w-10 h-10 text-amber-500 mx-auto mb-3" />
        <h2 className="text-lg font-bold text-slate-800">Campaign not found</h2>
        <Link
          href="/ngo/campaigns"
          className={buttonVariants({ variant: "outline", className: "mt-4" })}
        >
          Back to campaigns
        </Link>
      </div>
    );
  }

  const raised = campaign.current_amount ?? campaign.raised_amount ?? 0;
  const percent = campaign.funding_percentage
    ? Math.min(100, Math.round(campaign.funding_percentage))
    : Math.min(100, Math.round((raised / (campaign.target_amount || 1)) * 100));

  const milestones = campaign.milestones ?? [];

  return (
    <div className="space-y-6">
      {/* Back */}
      <div>
        <Link
          href="/ngo/campaigns"
          className={buttonVariants({ variant: "ghost", size: "sm", className: "gap-1.5 text-slate-500 -ml-2 mb-4" })}
        >
          <ArrowLeft className="w-4 h-4" />
          All campaigns
        </Link>
      </div>

      {/* Campaign header */}
      <Card className="border-slate-200 bg-white overflow-hidden">
        {campaign.cover_image_url && (
          <div className="h-40 overflow-hidden">
            <img src={campaign.cover_image_url} alt="" className="w-full h-full object-cover" />
          </div>
        )}
        <CardContent className="p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-start gap-3 justify-between">
            <div className="min-w-0 flex-1">
              <h1 className="text-xl font-extrabold text-slate-900 leading-tight">{campaign.title}</h1>
              <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-slate-500">
                {(campaign.state ?? campaign.location_state) && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5" />
                    {campaign.district ?? campaign.location_district
                      ? `${campaign.district ?? campaign.location_district}, ${campaign.state ?? campaign.location_state}`
                      : campaign.state ?? campaign.location_state}
                  </span>
                )}
                {campaign.created_at && (
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    Created {new Date(campaign.created_at).toLocaleDateString("en-IN", { month: "short", year: "numeric" })}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <CampaignStatusBadge status={campaign.status} />
              <Link href={`/campaigns/${campaign.id}`} target="_blank">
                <Button size="sm" variant="outline" className="gap-1.5 text-xs">
                  <ExternalLink className="w-3.5 h-3.5" />
                  View public page
                </Button>
              </Link>
            </div>
          </div>

          {/* ELEOS score & 4-Pillar Breakdown */}
          <div className="space-y-4 pt-3 border-t border-slate-100">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              {campaign.feasibility?.score != null ? (
                <div className="flex items-center gap-3">
                  <CircularScore score={campaign.feasibility.score} variant="eleos" size="md" />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-slate-900">Campaign Feasibility</span>
                      {campaign.feasibility.label && (
                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 capitalize">
                          {campaign.feasibility.label}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5 max-w-sm">
                      Evaluated against regional commodity benchmarks, scale metrics, and budget realism.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-slate-500 py-2">
                  <Clock className="w-4 h-4 text-slate-400" />
                  <span>ELEOS Score: Evaluation in progress</span>
                </div>
              )}
            </div>

            {/* 4 Pillars Breakdown (when available) */}
            {campaign.feasibility?.pillars && Object.keys(campaign.feasibility.pillars).length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="font-semibold text-slate-700">Budget Realism</span>
                    <span className="font-mono font-bold text-emerald-700">
                      {Math.round(campaign.feasibility.pillars.budget_realism?.score ?? 0)}
                    </span>
                  </div>
                  <Progress
                    value={campaign.feasibility.pillars.budget_realism?.score ?? 0}
                    className="h-1.5 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-500"
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">Weight: 40%</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="font-semibold text-slate-700">Project Scale</span>
                    <span className="font-mono font-bold text-emerald-700">
                      {Math.round(campaign.feasibility.pillars.project_scale?.score ?? 0)}
                    </span>
                  </div>
                  <Progress
                    value={campaign.feasibility.pillars.project_scale?.score ?? 0}
                    className="h-1.5 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-500"
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">Weight: 25%</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="font-semibold text-slate-700">Cost Context</span>
                    <span className="font-mono font-bold text-emerald-700">
                      {Math.round(campaign.feasibility.pillars.cost_context?.score ?? 0)}
                    </span>
                  </div>
                  <Progress
                    value={campaign.feasibility.pillars.cost_context?.score ?? 0}
                    className="h-1.5 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-500"
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">Weight: 20%</span>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/60">
                  <div className="flex justify-between items-center text-xs mb-1.5">
                    <span className="font-semibold text-slate-700">Capacity</span>
                    <span className="font-mono font-bold text-emerald-700">
                      {Math.round(campaign.feasibility.pillars.implementation_capacity?.score ?? 0)}
                    </span>
                  </div>
                  <Progress
                    value={campaign.feasibility.pillars.implementation_capacity?.score ?? 0}
                    className="h-1.5 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-500"
                  />
                  <span className="text-[10px] text-slate-400 mt-1 block">Weight: 15%</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-5">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-2">Raised</p>
            <p className="text-2xl font-extrabold text-slate-900 font-mono">
              ₹{raised.toLocaleString("en-IN")}
            </p>
            <div className="mt-2">
              <Progress
                value={percent}
                className="h-2 [&_[data-slot=progress-track]]:bg-slate-100 [&_[data-slot=progress-indicator]]:bg-emerald-500"
              />
              <p className="text-xs text-slate-400 mt-1">
                {percent}% of ₹{campaign.target_amount.toLocaleString("en-IN")} goal
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-5">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-2">Donors</p>
            <p className="text-2xl font-extrabold text-slate-900 font-mono">
              {Math.round(raised / 1500)}
            </p>
            <p className="text-xs text-slate-400 mt-1">Estimated from contributions</p>
          </CardContent>
        </Card>

        <Card className="border-slate-200 bg-white">
          <CardContent className="p-5">
            <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-2">Milestones</p>
            <p className="text-2xl font-extrabold text-slate-900 font-mono">
              {milestones.filter((m) => m.status === "verified").length}
              <span className="text-base text-slate-400 font-normal"> / {milestones.length}</span>
            </p>
            <p className="text-xs text-slate-400 mt-1">Completed</p>
          </CardContent>
        </Card>
      </div>

      {/* Milestones */}
      {milestones.length > 0 && (
        <div className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Milestones</h2>
            <p className="text-sm text-slate-500 mt-0.5">
              Share progress updates at each stage to keep donors informed.
            </p>
          </div>
          <div className="space-y-3">
            {milestones.map((m, i) => (
              <MilestoneCard
                key={m.id}
                milestone={m}
                index={i}
                onShareProgress={setSelectedMilestone}
              />
            ))}
          </div>
        </div>
      )}

      {/* Campaign description */}
      {campaign.description && (
        <Card className="border-slate-200 bg-white">
          <CardContent className="p-6">
            <h2 className="text-base font-bold text-slate-900 mb-3">Campaign description</h2>
            <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{campaign.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Share progress modal */}
      {selectedMilestone && (
        <ShareProgressModal
          milestone={selectedMilestone}
          onClose={() => setSelectedMilestone(null)}
          onSubmit={handleShareProgress}
        />
      )}
    </div>
  );
}

