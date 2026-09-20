"use client";

import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CircularScore } from "@/components/ngo/CircularScore";
import { CheckCircle2, Clock, AlertCircle, ChevronDown, ChevronUp } from "lucide-react";
import { ngoApi, NGOProfileData, ComplianceDocument } from "@/lib/api";

// ── Status badge ───────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { icon: React.ReactNode; label: string; className: string }> = {
    verified: {
      icon: <CheckCircle2 className="w-3 h-3" />,
      label: "Verified",
      className: "text-emerald-700 bg-emerald-50 border-emerald-200",
    },
    pending: {
      icon: <Clock className="w-3 h-3" />,
      label: "Pending",
      className: "text-amber-700 bg-amber-50 border-amber-200",
    },
    under_review: {
      icon: <Clock className="w-3 h-3" />,
      label: "Under review",
      className: "text-blue-700 bg-blue-50 border-blue-200",
    },
    rejected: {
      icon: <AlertCircle className="w-3 h-3" />,
      label: "Rejected",
      className: "text-red-700 bg-red-50 border-red-200",
    },
  };
  const s = cfg[status] ?? { icon: null, label: status, className: "text-slate-600 bg-slate-50 border-slate-200" };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold border ${s.className}`}>
      {s.icon}{s.label}
    </span>
  );
}

// ── Score breakdown bar ────────────────────────────────────────────────────────
function ScoreBar({ label, value, items }: { label: string; value: number; items: string[] }) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-sm font-semibold text-slate-800">{label}</span>
        <span className="font-mono font-bold text-sm">{value}/100</span>
      </div>
      <Progress
        value={value}
        className="h-2 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-blue-500"
      />
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex items-center gap-1.5 text-xs text-slate-600">
            <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

// ── Document label map ─────────────────────────────────────────────────────────
const DOC_LABELS: Record<string, string> = {
  registration_certificate: "Registration Certificate",
  pan_document: "PAN Document",
  certificate_12a: "12A Certificate",
  "12a_certificate": "12A Certificate",
  certificate_80g: "80G Certificate",
  "80g_certificate": "80G Certificate",
  darpan_certificate: "NGO Darpan Certificate",
  fcra_certificate: "FCRA Certificate",
  fcra_registration: "FCRA Registration",
  audit_report_fy25: "Audited Financial Report (FY25)",
};

// ── Main page ──────────────────────────────────────────────────────────────────
export default function OrganisationPage() {
  const [profile, setProfile] = useState<NGOProfileData | null>(null);
  const [documents, setDocuments] = useState<ComplianceDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [scoreExpanded, setScoreExpanded] = useState(false);
  const [howCalcExpanded, setHowCalcExpanded] = useState(false);

  useEffect(() => {
    Promise.all([
      ngoApi.getMeProfile().catch(() => null),
      ngoApi.getDocuments().catch(() => []),
    ]).then(([prof, docs]) => {
      setProfile(prof);
      setDocuments(docs);
      setIsLoading(false);
    });
  }, []);

  const isVerified = profile?.verification_status === "verified";

  if (isLoading) {
    return (
      <div className="space-y-4 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-48" />
        <div className="h-40 bg-slate-200 rounded-xl" />
        <div className="h-40 bg-slate-200 rounded-xl" />
      </div>
    );
  }

  const regTypeLabel: Record<string, string> = {
    trust: "Trust",
    society: "Society",
    section_8: "Section 8 Company",
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-slate-900">Organisation</h1>
        <p className="text-sm text-slate-500 mt-1">
          Your organisation's identity, compliance status, and verification documents.
        </p>
      </div>

      {/* ── Organisation info card ─────────────────────────────────────────── */}
      <Card className="border-slate-200 bg-white">
        <CardContent className="p-6 space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">{profile?.name ?? "—"}</h2>
              <p className="text-sm text-slate-500">
                {regTypeLabel[profile?.registration_type ?? ""] ?? profile?.registration_type ?? "—"}
              </p>
            </div>
            <StatusBadge status={profile?.verification_status ?? "pending"} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-4">
            {[
              { label: "Registration Number", value: profile?.registration_number },
              { label: "PAN", value: profile?.pan },
              { label: "NGO Darpan ID", value: profile?.darpan_id },
              { label: "State of Registration", value: profile?.state_of_registration },
            ].map(({ label, value }) => (
              <div key={label}>
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">{label}</p>
                <p className="text-sm font-medium text-slate-800 mt-0.5">{value ?? "—"}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Compliance status card ─────────────────────────────────────────── */}
      <Card className="border-slate-200 bg-white">
        <CardContent className="p-6">
          <h2 className="text-base font-bold text-slate-900 mb-4">Compliance status</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[
              {
                label: "Section 12A",
                active: profile?.has_12a ?? !!profile?.section_12a_number,
                detail: profile?.section_12a_number,
              },
              {
                label: "Section 80G",
                active: profile?.has_80g ?? !!profile?.section_80g_number,
                detail: profile?.section_80g_number,
              },
              {
                label: "FCRA",
                active: profile?.has_fcra ?? !!profile?.fcra_number,
                detail: profile?.fcra_number,
              },
            ].map(({ label, active, detail }) => (
              <div
                key={label}
                className={`p-4 rounded-xl border ${active ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50"}`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {active ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <AlertCircle className="w-4 h-4 text-slate-400" />
                  )}
                  <span className="text-sm font-semibold text-slate-800">{label}</span>
                </div>
                <p className={`text-xs ${active ? "text-emerald-700" : "text-slate-400"}`}>
                  {active ? (detail ?? "Active") : "Not registered"}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Documents card ─────────────────────────────────────────────────── */}
      <Card className="border-slate-200 bg-white">
        <CardContent className="p-6">
          <h2 className="text-base font-bold text-slate-900 mb-4">Uploaded documents</h2>
          {documents.length === 0 ? (
            <p className="text-sm text-slate-400">No documents uploaded yet.</p>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-slate-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-slate-200 rounded-md flex items-center justify-center text-slate-500 text-xs font-bold">
                      PDF
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">
                        {DOC_LABELS[doc.doc_type] ?? doc.doc_type.replace(/_/g, " ")}
                      </p>
                      {doc.valid_until && (
                        <p className="text-[11px] text-slate-400">
                          Valid until {new Date(doc.valid_until).toLocaleDateString("en-IN", { year: "numeric", month: "short" })}
                        </p>
                      )}
                    </div>
                  </div>
                  <StatusBadge status={doc.status} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Trust Score card ───────────────────────────────────────────────── */}
      {isVerified && profile?.trust_score != null && (
        <Card className="border-blue-100 bg-gradient-to-br from-blue-50 to-white">
          <CardContent className="p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-1">Organisation Trust Score</p>
                <p className="text-xs text-slate-500 max-w-sm">
                  This score belongs to your organisation, not to any individual campaign.
                </p>
              </div>
              <CircularScore score={profile.trust_score} variant="trust" size="lg" />
            </div>

            {/* Breakdown — expandable */}
            {profile.breakdown && (
              <>
                <button
                  onClick={() => setScoreExpanded((v) => !v)}
                  className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 hover:text-blue-900 transition-colors mt-2"
                >
                  {scoreExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  {scoreExpanded ? "Hide breakdown" : "View breakdown"}
                </button>

                {scoreExpanded && (
                  <div className="mt-5 space-y-6 pt-5 border-t border-blue-100">
                    <ScoreBar
                      label="Identity & Legal"
                      value={profile.breakdown.legal}
                      items={[
                        "NGO Darpan registration confirmed",
                        "PAN verified",
                        ...(profile.has_12a ? ["Section 12A active"] : []),
                        ...(profile.has_fcra ? ["FCRA registration active"] : []),
                      ]}
                    />
                    <ScoreBar
                      label="Financial Transparency"
                      value={profile.breakdown.financial}
                      items={["Organisation financial documents reviewed"]}
                    />
                    <ScoreBar
                      label="Operational History"
                      value={profile.breakdown.operational}
                      items={["Campaign track record on ELEOS"]}
                    />
                  </div>
                )}
              </>
            )}

            {/* How is this calculated */}
            <div className="mt-4 pt-4 border-t border-blue-100">
              <button
                onClick={() => setHowCalcExpanded((v) => !v)}
                className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors"
              >
                {howCalcExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                How is this calculated?
              </button>
              {howCalcExpanded && (
                <div className="mt-3 p-4 bg-white rounded-lg border border-slate-200 text-xs text-slate-600 leading-relaxed space-y-2">
                  <p>
                    Your Trust Score is generated by ELEOS after reviewing your organisation's submitted documents and information.
                    It takes into account your legal registration, compliance status (12A, 80G, FCRA), and any prior campaign history on the platform.
                  </p>
                  <p>
                    This score is visible to donors on any campaign your organisation runs. It is updated periodically
                    as your organisation's information changes.
                  </p>
                  <p>
                    If you believe your score is incorrect, you can{" "}
                    <a href="mailto:support@eleos.app" className="text-blue-600 hover:underline">contact our support team</a>{" "}
                    to request a review.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

