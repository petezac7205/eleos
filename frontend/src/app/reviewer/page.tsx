"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Filter, 
  Search, 
  Eye, 
  FileText, 
  HelpCircle, 
  Cpu, 
  Loader2, 
  X, 
  ArrowUpRight,
  TrendingUp,
  Building2,
  Flag,
  Sparkles,
  Layers,
  AlertCircle
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { reviewerApi, ReviewQueueItem, ReviewerStats } from "@/lib/api";

export default function ReviewerPage() {
  const { user, switchPersona } = useAuth();
  const [queueItems, setQueueItems] = useState<ReviewQueueItem[]>([]);
  const [stats, setStats] = useState<ReviewerStats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [priorityFilter, setPriorityFilter] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");

  // Audit modal state
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [itemDetail, setItemDetail] = useState<any | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [decisionNotes, setDecisionNotes] = useState<string>("");
  const [submittingDecision, setSubmittingDecision] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchQueueData = async () => {
    setIsLoading(true);
    try {
      const [queueData, statsData] = await Promise.all([
        reviewerApi.getQueue({
          status: statusFilter !== "all" ? statusFilter : undefined,
          priority: priorityFilter !== "all" ? priorityFilter : undefined,
        }).catch(() => []),
        reviewerApi.getStats().catch(() => null),
      ]);
      setQueueItems(queueData);
      setStats(statsData);
    } catch (err) {
      console.error("Failed to load review queue data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQueueData();
  }, [statusFilter, priorityFilter]);

  const handleOpenAuditModal = async (item: ReviewQueueItem) => {
    setSelectedItem(item);
    setDecisionNotes("");
    setActionSuccess(null);
    setActionError(null);
    setIsLoadingDetail(true);
    try {
      const detail = await reviewerApi.getItem(item.id);
      setItemDetail(detail);
    } catch (err: any) {
      console.error("Failed to load item detail:", err);
      setActionError(err.message || "Could not fetch entity details.");
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleSubmitDecision = async (decision: "approved" | "rejected" | "needs_info" | "escalated") => {
    if (!selectedItem) return;
    setSubmittingDecision(true);
    setActionError(null);
    try {
      await reviewerApi.submitDecision(selectedItem.id, decision, decisionNotes);
      setActionSuccess(`Audit decision recorded: ${decision.toUpperCase()}. Underlying entity updated.`);
      setTimeout(() => {
        setSelectedItem(null);
        setItemDetail(null);
        fetchQueueData();
      }, 1500);
    } catch (err: any) {
      setActionError(err.message || "Failed to submit decision.");
    } finally {
      setSubmittingDecision(false);
    }
  };

  const filteredQueue = queueItems.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.entity_name?.toLowerCase().includes(q) ||
      item.entity_id?.toLowerCase().includes(q) ||
      item.flags.some((f) => f.toLowerCase().includes(q))
    );
  });

  const isReviewer = user?.role === "reviewer" || user?.role === "admin";

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      {/* Header */}
      <div className="border-b border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold mb-3">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" />
                Auditor & Compliance Hub
              </div>
              <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
                Review & Verification Queue
              </h1>
              <p className="text-slate-600 mt-1 text-sm max-w-2xl">
                Independent oversight engine inspecting AI flagged budget anomalies, high-risk NGO profiles, and on-chain compliance proofs.
              </p>
            </div>

            {!isReviewer && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-center justify-between gap-3 text-xs text-amber-800">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>Viewing as <strong>{user?.role || "Guest"}</strong>. Switch to auditor mode to take review actions.</span>
                </div>
                <Button
                  size="sm"
                  onClick={() => switchPersona("reviewer")}
                  className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold px-3 py-1.5 h-auto rounded-lg shrink-0 shadow-xs"
                >
                  Switch to Auditor
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Audits</p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1">
                  {stats ? (stats as any).pending_reviews ?? stats.pending_total ?? 0 : "0"}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Awaiting verification</p>
              </div>
              <div className="w-11 h-11 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
                <Clock className="w-5 h-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-rose-600 uppercase tracking-wider">Critical Priority</p>
                <h3 className="text-2xl font-bold text-rose-700 mt-1">
                  {stats ? (stats as any).critical_priority ?? stats.critical_total ?? 0 : "0"}
                </h3>
                <p className="text-xs text-rose-500 mt-0.5">High anomaly triggers</p>
              </div>
              <div className="w-11 h-11 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
                <AlertTriangle className="w-5 h-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wider">Resolved Audits</p>
                <h3 className="text-2xl font-bold text-emerald-700 mt-1">
                  {stats ? (stats as any).resolved_reviews ?? stats.resolved_today ?? 0 : "0"}
                </h3>
                <p className="text-xs text-emerald-600 mt-0.5">Decisions anchored</p>
              </div>
              <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200/80 shadow-xs hover:shadow-md transition-shadow">
            <CardContent className="p-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-indigo-600 uppercase tracking-wider">Pending Campaigns</p>
                <h3 className="text-2xl font-bold text-indigo-700 mt-1">
                  {stats ? (stats as any).pending_campaigns ?? 0 : "0"}
                </h3>
                <p className="text-xs text-indigo-500 mt-0.5">Under launch review</p>
              </div>
              <div className="w-11 h-11 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
                <Layers className="w-5 h-5" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filter & Search Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 inset-y-0 my-auto" />
            <Input
              placeholder="Search by entity name, UUID, or flag..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-10 text-sm bg-slate-50 border-slate-200 focus:bg-white"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mr-1">
              <Filter className="w-3.5 h-3.5" />
              Status:
            </div>
            {["pending", "resolved", "all"].map((status) => (
              <Button
                key={status}
                variant={statusFilter === status ? "default" : "outline"}
                size="sm"
                onClick={() => setStatusFilter(status)}
                className={`text-xs h-8 capitalize ${
                  statusFilter === status 
                    ? "bg-slate-900 text-white" 
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {status}
              </Button>
            ))}

            <div className="w-px h-6 bg-slate-200 mx-1 hidden md:block" />

            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mr-1">
              Priority:
            </div>
            {["all", "critical", "high", "normal"].map((priority) => (
              <Button
                key={priority}
                variant={priorityFilter === priority ? "default" : "outline"}
                size="sm"
                onClick={() => setPriorityFilter(priority)}
                className={`text-xs h-8 capitalize ${
                  priorityFilter === priority 
                    ? "bg-indigo-600 text-white" 
                    : "border-slate-200 text-slate-600 hover:bg-slate-50"
                }`}
              >
                {priority}
              </Button>
            ))}
          </div>
        </div>

        {/* Queue Table */}
        <Card className="border-slate-200/80 shadow-xs overflow-hidden">
          <CardHeader className="bg-slate-50/70 border-b border-slate-200/80 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base font-bold text-slate-900">
                  Audit Worklist
                </CardTitle>
                <CardDescription className="text-xs text-slate-500">
                  Sorted by priority: critical anomalies and escalated items first.
                </CardDescription>
              </div>
              <Badge variant="outline" className="text-xs bg-white text-slate-700 font-mono">
                {filteredQueue.length} {filteredQueue.length === 1 ? "Item" : "Items"}
              </Badge>
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-12 text-center flex flex-col items-center justify-center">
                <Loader2 className="w-7 h-7 text-indigo-600 animate-spin mb-3" />
                <p className="text-sm text-slate-600">Loading audit queue...</p>
              </div>
            ) : filteredQueue.length === 0 ? (
              <div className="p-12 text-center">
                <div className="w-12 h-12 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center mx-auto mb-3">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h4 className="text-base font-bold text-slate-900">All Audits Cleared</h4>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  No items match the current filters. Outstanding campaigns and NGO profiles are in good standing.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50/50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                      <th className="py-3.5 px-6">Entity</th>
                      <th className="py-3.5 px-4">Type</th>
                      <th className="py-3.5 px-4">Priority</th>
                      <th className="py-3.5 px-4">Anomaly Flags</th>
                      <th className="py-3.5 px-4">Status</th>
                      <th className="py-3.5 px-4">Submitted</th>
                      <th className="py-3.5 px-6 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {filteredQueue.map((item) => {
                      const isCritical = item.priority === "critical";
                      const isHigh = item.priority === "high";

                      return (
                        <tr key={item.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="py-4 px-6 font-medium text-slate-900">
                            <div>
                              <span className="font-semibold text-slate-900">{item.entity_name}</span>
                              <p className="text-[11px] font-mono text-slate-400 mt-0.5">
                                ID: {item.entity_id?.slice(0, 8)}...
                              </p>
                            </div>
                          </td>

                          <td className="py-4 px-4">
                            <Badge
                              variant="outline"
                              className={`text-[11px] capitalize font-medium ${
                                item.entity_type === "campaign"
                                  ? "bg-blue-50 text-blue-700 border-blue-200"
                                  : "bg-purple-50 text-purple-700 border-purple-200"
                              }`}
                            >
                              {item.entity_type === "campaign" ? "Campaign" : "NGO Org"}
                            </Badge>
                          </td>

                          <td className="py-4 px-4">
                            <Badge
                              className={`text-[11px] capitalize font-semibold ${
                                isCritical
                                  ? "bg-rose-100 text-rose-800 border-rose-200"
                                  : isHigh
                                  ? "bg-amber-100 text-amber-800 border-amber-200"
                                  : "bg-slate-100 text-slate-700 border-slate-200"
                              }`}
                            >
                              {item.priority}
                            </Badge>
                          </td>

                          <td className="py-4 px-4">
                            <div className="flex flex-wrap gap-1 max-w-xs">
                              {item.flags && item.flags.length > 0 ? (
                                item.flags.map((flag, idx) => (
                                  <span
                                    key={idx}
                                    className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-red-50 text-red-700 border border-red-200"
                                  >
                                    {flag}
                                  </span>
                                ))
                              ) : (
                                <span className="text-xs text-slate-400 italic">Routine audit</span>
                              )}
                            </div>
                          </td>

                          <td className="py-4 px-4">
                            <Badge
                              variant="outline"
                              className={`text-[11px] capitalize font-medium ${
                                item.status === "resolved"
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : "bg-amber-50 text-amber-700 border-amber-200"
                              }`}
                            >
                              {item.status}
                              {item.decision ? ` (${item.decision})` : ""}
                            </Badge>
                          </td>

                          <td className="py-4 px-4 text-xs text-slate-500 whitespace-nowrap">
                            {item.created_at
                              ? new Date(item.created_at).toLocaleDateString("en-IN", {
                                  month: "short",
                                  day: "numeric",
                                })
                              : "—"}
                          </td>

                          <td className="py-4 px-6 text-right">
                            <Button
                              size="sm"
                              onClick={() => handleOpenAuditModal(item)}
                              className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold h-8 px-3 rounded-lg shadow-xs"
                            >
                              <Eye className="w-3.5 h-3.5 mr-1.5" />
                              Inspect
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Deep Inspection & Decision Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-200 flex items-center justify-between shrink-0 bg-slate-50/50 rounded-t-2xl">
              <div>
                <div className="flex items-center gap-2">
                  <Badge
                    className={`text-[10px] uppercase font-bold ${
                      selectedItem.priority === "critical"
                        ? "bg-rose-600 text-white"
                        : "bg-amber-500 text-white"
                    }`}
                  >
                    {selectedItem.priority} Priority
                  </Badge>
                  <Badge variant="outline" className="text-[10px] font-mono capitalize">
                    {selectedItem.entity_type}
                  </Badge>
                </div>
                <h3 className="text-xl font-bold text-slate-900 mt-1.5">
                  Audit: {selectedItem.entity_name}
                </h3>
              </div>
              <button
                onClick={() => setSelectedItem(null)}
                className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6">
              {isLoadingDetail ? (
                <div className="py-12 text-center flex flex-col items-center justify-center">
                  <Loader2 className="w-7 h-7 text-indigo-600 animate-spin mb-3" />
                  <p className="text-sm text-slate-600">Retrieving anomaly reports and scoring telemetry...</p>
                </div>
              ) : (
                <>
                  {/* Flag Alerts */}
                  {selectedItem.flags && selectedItem.flags.length > 0 && (
                    <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-rose-800 font-semibold text-sm mb-2">
                        <AlertTriangle className="w-4 h-4 text-rose-600" />
                        Automated Anomaly Detection Triggers
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {selectedItem.flags.map((flag, idx) => (
                          <span
                            key={idx}
                            className="bg-white text-rose-700 font-mono text-xs px-2.5 py-1 rounded-md border border-rose-200 font-semibold shadow-xs"
                          >
                            ⚠️ {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Entity Specific Details */}
                  {itemDetail?.entity_detail && (
                    <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 space-y-4">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        AI Scoring Telemetry & Metrics
                      </h4>

                      {selectedItem.entity_type === "campaign" && (
                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">Target Budget</p>
                            <p className="text-base font-bold text-slate-900 mt-0.5">
                              ₹{itemDetail.entity_detail.target_amount?.toLocaleString("en-IN")}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">Feasibility Score</p>
                            <p className="text-base font-bold text-indigo-600 mt-0.5">
                              {itemDetail.entity_detail.feasibility_score ?? "N/A"}/100
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">Safety Tier</p>
                            <p className="text-base font-bold text-slate-800 capitalize mt-0.5">
                              {itemDetail.entity_detail.safety_tier?.replace("_", " ") ?? "Standard"}
                            </p>
                          </div>
                        </div>
                      )}

                      {selectedItem.entity_type === "ngo" && (
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">Registration No</p>
                            <p className="text-xs font-mono font-bold text-slate-800 mt-1 truncate">
                              {itemDetail.entity_detail.registration_number || "Pending"}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">PAN ID</p>
                            <p className="text-xs font-mono font-bold text-slate-800 mt-1">
                              {itemDetail.entity_detail.pan || "N/A"}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">NGO Darpan ID</p>
                            <p className="text-xs font-mono font-bold text-slate-800 mt-1">
                              {itemDetail.entity_detail.darpan_id || "N/A"}
                            </p>
                          </div>
                          <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-xs">
                            <p className="text-[11px] text-slate-500 font-medium">Trust Score</p>
                            <p className="text-sm font-bold text-emerald-600 mt-1">
                              {itemDetail.entity_detail.trustability_score?.overall_score ?? "N/A"}/100
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Auditor Notes Input */}
                  <div className="space-y-2">
                    <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                      Auditor Compliance Notes & Findings
                    </label>
                    <textarea
                      rows={3}
                      placeholder="Add compliance notes, justification for approval/rejection, or required additional documents..."
                      value={decisionNotes}
                      onChange={(e) => setDecisionNotes(e.target.value)}
                      className="w-full text-sm p-3 rounded-xl border border-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-slate-50 focus:bg-white"
                    />
                  </div>

                  {/* Feedback alerts */}
                  {actionSuccess && (
                    <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3.5 flex items-center gap-2.5 text-xs font-medium text-emerald-800">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>{actionSuccess}</span>
                    </div>
                  )}
                  {actionError && (
                    <div className="bg-rose-50 border border-rose-200 rounded-xl p-3.5 flex items-center gap-2.5 text-xs font-medium text-rose-800">
                      <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                      <span>{actionError}</span>
                    </div>
                  )}
                </>
              )}
            </div>

            {/* Modal Footer / Action Buttons */}
            <div className="p-6 border-t border-slate-200 bg-slate-50/80 rounded-b-2xl flex flex-wrap items-center justify-between gap-3 shrink-0">
              <div className="flex items-center gap-2 text-xs text-slate-500 font-mono">
                <Cpu className="w-3.5 h-3.5 text-slate-400" />
                Decision anchored to Polygon Amoy Registry
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedItem(null)}
                  disabled={submittingDecision}
                  className="text-xs"
                >
                  Cancel
                </Button>

                <Button
                  size="sm"
                  onClick={() => handleSubmitDecision("needs_info")}
                  disabled={submittingDecision}
                  className="bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs"
                >
                  Request Info
                </Button>

                <Button
                  size="sm"
                  onClick={() => handleSubmitDecision("rejected")}
                  disabled={submittingDecision}
                  className="bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs"
                >
                  Reject Entity
                </Button>

                <Button
                  size="sm"
                  onClick={() => handleSubmitDecision("approved")}
                  disabled={submittingDecision}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs"
                >
                  {submittingDecision ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin mr-1.5" />
                      Anchoring...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                      Approve & Verify
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

