"use client";

import React, { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StepIndicator } from "@/components/ngo/StepIndicator";
import { CircularScore } from "@/components/ngo/CircularScore";
import {
  ArrowLeft,
  ArrowRight,
  Plus,
  Trash2,
  GripVertical,
  UploadCloud,
  CheckCircle2,
  Clock,
  Loader2,
  AlertCircle,
  MapPin,
  Calendar,
  Users,
  Home,
  Target,
} from "lucide-react";
import { campaignsApi, ngoApi, NGOProfileData, CampaignCreatePayload, FeasibilityResult } from "@/lib/api";
import Link from "next/link";

// ── Steps ──────────────────────────────────────────────────────────────────────
const STEPS = [
  { label: "About" },
  { label: "Details" },
  { label: "Milestones" },
  { label: "Media" },
  { label: "Review" },
];

// ── Cause options ──────────────────────────────────────────────────────────────
const CAUSES = [
  { value: "Healthcare & Nutrition", label: "Healthcare & Nutrition" },
  { value: "Education & Skill Development", label: "Education & Skill Development" },
  { value: "Water, Sanitation & Environment", label: "Water, Sanitation & Environment" },
  { value: "Social Welfare & Community Development", label: "Social Welfare & Community Development" },
  { value: "Emergency Relief & Rehabilitation", label: "Emergency Relief & Rehabilitation" },
];

const COMMODITY_OPTIONS = [
  { value: "Food", label: "Food (Dry Rations / Meals / Nutrition)" },
  { value: "Medical", label: "Medical (Medicines / First Aid)" },
  { value: "Relief Kits", label: "Relief Kits (Hygiene / Emergency Kits)" },
  { value: "Materials", label: "Materials (Educational / Training Tools)" },
  { value: "Shelter", label: "Shelter (Tents / Tarpaulins / Bedding)" },
];

const INDIAN_STATES = [
  "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
  "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
  "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram",
  "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
  "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
  "Andaman & Nicobar", "Chandigarh", "Delhi", "Jammu & Kashmir", "Ladakh",
  "Lakshadweep", "Puducherry",
];

// ── Form types ─────────────────────────────────────────────────────────────────
interface MilestoneDraft {
  id: string;
  title: string;
  description: string;
}

interface CampaignForm {
  // Step 1
  title: string;
  description: string;
  state: string;
  district: string;
  beneficiaries: string;
  communities: string;
  cause: string;
  // Step 2
  target_amount: string;
  commodity_type: string;
  start_date: string;
  end_date: string;
  urgency: "standard" | "urgent" | "emergency";
  is_disaster_relief: boolean;
  is_remote_area: boolean;
  // Step 3
  milestones: MilestoneDraft[];
  // Step 4
  cover_image_url: string;
}

// ── Helper UI atoms ────────────────────────────────────────────────────────────
function FormField({
  label,
  required,
  hint,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-sm font-semibold text-slate-800">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </Label>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      {children}
    </div>
  );
}

function SelectField({
  value,
  onChange,
  options,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full p-2.5 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function ToggleField({
  checked,
  onChange,
  label,
  hint,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  hint?: string;
}) {
  return (
    <div
      className={`flex items-start justify-between gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
        checked ? "border-emerald-200 bg-emerald-50" : "border-slate-200 bg-slate-50"
      }`}
      onClick={() => onChange(!checked)}
    >
      <div className="flex-1">
        <p className="text-sm font-semibold text-slate-800">{label}</p>
        {hint && <p className="text-xs text-slate-500 mt-0.5">{hint}</p>}
      </div>
      <div
        className={`w-10 h-5 rounded-full flex items-center transition-colors shrink-0 mt-0.5 ${
          checked ? "bg-emerald-600 justify-end" : "bg-slate-300 justify-start"
        }`}
      >
        <div className="w-4 h-4 bg-white rounded-full mx-0.5 shadow-sm" />
      </div>
    </div>
  );
}

function UrgencyButton({
  value,
  selected,
  onClick,
  icon,
  description,
}: {
  value: string;
  selected: boolean;
  onClick: () => void;
  icon: string;
  description: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 text-center transition-all ${
        selected
          ? "border-emerald-500 bg-emerald-50 text-emerald-900"
          : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
      }`}
    >
      <span className="text-2xl">{icon}</span>
      <span className="text-sm font-semibold capitalize">{value}</span>
      <span className="text-[11px] text-slate-400 leading-tight">{description}</span>
    </button>
  );
}

// ── Milestone row ──────────────────────────────────────────────────────────────
function MilestoneRow({
  milestone,
  index,
  total,
  onChange,
  onRemove,
  onMoveUp,
  onMoveDown,
}: {
  milestone: MilestoneDraft;
  index: number;
  total: number;
  onChange: (id: string, field: "title" | "description", value: string) => void;
  onRemove: (id: string) => void;
  onMoveUp: (index: number) => void;
  onMoveDown: (index: number) => void;
}) {
  return (
    <div className="flex gap-3 items-start p-4 rounded-xl border border-slate-200 bg-white hover:border-slate-300 transition-colors group">
      {/* Drag handle / number */}
      <div className="flex flex-col items-center gap-1 shrink-0 pt-1">
        <button
          type="button"
          onClick={() => onMoveUp(index)}
          disabled={index === 0}
          className="w-5 h-5 flex items-center justify-center text-slate-300 hover:text-slate-600 disabled:opacity-30 transition-colors text-xs"
          aria-label="Move up"
        >
          ▲
        </button>
        <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold">
          {index + 1}
        </div>
        <button
          type="button"
          onClick={() => onMoveDown(index)}
          disabled={index === total - 1}
          className="w-5 h-5 flex items-center justify-center text-slate-300 hover:text-slate-600 disabled:opacity-30 transition-colors text-xs"
          aria-label="Move down"
        >
          ▼
        </button>
      </div>

      {/* Fields */}
      <div className="flex-1 space-y-2 min-w-0">
        <Input
          value={milestone.title}
          onChange={(e) => onChange(milestone.id, "title", e.target.value)}
          placeholder={`Milestone ${index + 1} — e.g. Install water systems`}
          className="font-medium"
        />
        <textarea
          value={milestone.description}
          onChange={(e) => onChange(milestone.id, "description", e.target.value)}
          placeholder="Optional description of what will happen at this stage"
          rows={2}
          className="w-full p-2.5 text-sm rounded-lg border border-slate-300 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>

      {/* Remove */}
      <button
        type="button"
        onClick={() => onRemove(milestone.id)}
        className="mt-1 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 shrink-0"
        aria-label="Remove milestone"
        disabled={total <= 1}
      >
        <Trash2 className="w-4 h-4" />
      </button>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────
export default function CreateCampaignPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [createdCampaignId, setCreatedCampaignId] = useState<string | null>(null);
  const [feasibility, setFeasibility] = useState<FeasibilityResult | null>(null);
  const [isFeasibilityLoading, setIsFeasibilityLoading] = useState(false);
  const [profile, setProfile] = useState<NGOProfileData | null>(null);

  // Load profile for Trust Score display on review step
  React.useEffect(() => {
    ngoApi.getMeProfile().catch(() => null).then(setProfile);
  }, []);

  // Fetch real ML feasibility score on success screen
  React.useEffect(() => {
    if (step === 5 && createdCampaignId) {
      setIsFeasibilityLoading(true);
      campaignsApi.getFeasibility(createdCampaignId)
        .then((res) => {
          if (res && (res.score != null || res.feasibility_score != null)) {
            setFeasibility(res);
          }
        })
        .catch(() => null)
        .finally(() => setIsFeasibilityLoading(false));
    }
  }, [step, createdCampaignId]);

  const [form, setForm] = useState<CampaignForm>({
    title: "",
    description: "",
    state: "",
    district: "",
    beneficiaries: "",
    communities: "",
    cause: "",
    target_amount: "",
    commodity_type: "",
    start_date: "",
    end_date: "",
    urgency: "standard",
    is_disaster_relief: false,
    is_remote_area: false,
    milestones: [
      { id: "m1", title: "", description: "" },
      { id: "m2", title: "", description: "" },
    ],
    cover_image_url: "",
  });

  const set = (key: keyof CampaignForm, value: any) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  // ── Milestone handlers ───────────────────────────────────────────────────────
  const addMilestone = () => {
    const newId = `m${Date.now()}`;
    set("milestones", [...form.milestones, { id: newId, title: "", description: "" }]);
  };

  const removeMilestone = (id: string) => {
    if (form.milestones.length <= 1) return;
    set("milestones", form.milestones.filter((m) => m.id !== id));
  };

  const updateMilestone = (id: string, field: "title" | "description", value: string) => {
    set(
      "milestones",
      form.milestones.map((m) => (m.id === id ? { ...m, [field]: value } : m))
    );
  };

  const moveMilestone = (index: number, direction: "up" | "down") => {
    const arr = [...form.milestones];
    const target = direction === "up" ? index - 1 : index + 1;
    if (target < 0 || target >= arr.length) return;
    [arr[index], arr[target]] = [arr[target], arr[index]];
    set("milestones", arr);
  };

  // ── Step validation ──────────────────────────────────────────────────────────
  const canProceed = (): boolean => {
    switch (step) {
      case 0:
        return !!(
          form.title.trim() &&
          form.description.trim() &&
          form.state &&
          form.district.trim() &&
          form.beneficiaries &&
          form.cause
        );
      case 1:
        return !!(
          form.target_amount &&
          parseInt(form.target_amount) > 0 &&
          form.start_date &&
          form.end_date &&
          form.start_date < form.end_date
        );
      case 2:
        return form.milestones.some((m) => m.title.trim() !== "");
      case 3:
        return true; // Media is optional
      case 4:
        return true;
      default:
        return false;
    }
  };

  // ── Submit ───────────────────────────────────────────────────────────────────
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const payload: CampaignCreatePayload = {
        title: form.title,
        description: form.description,
        category: form.cause,
        location_state: form.state,
        location_district: form.district,
        beneficiaries_count: parseInt(form.beneficiaries) || 0,
        communities_count: parseInt(form.communities) || 0,
        target_amount: parseInt(form.target_amount) || 0,
        commodity_type: form.commodity_type || undefined,
        start_date: form.start_date,
        end_date: form.end_date,
        urgency: form.urgency,
        is_disaster_relief: form.is_disaster_relief,
        is_remote_area: form.is_remote_area,
        milestones: form.milestones
          .filter((m) => m.title.trim())
          .map((m) => ({ title: m.title, description: m.description })),
        cover_image_url: form.cover_image_url || undefined,
      };
      const created = await campaignsApi.createCampaign(payload);
      setCreatedCampaignId(created.id);
      setStep(5); // success state
    } catch (err: any) {
      setSubmitError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const causeLabel = CAUSES.find((c) => c.value === form.cause)?.label ?? form.cause;

  // ── Success screen ───────────────────────────────────────────────────────────
  if (step === 5) {
    const scoreVal = feasibility?.score ?? feasibility?.feasibility_score;
    const labelVal = feasibility?.label ?? feasibility?.score_label ?? "evaluated";

    return (
      <div className="max-w-lg mx-auto text-center py-16 space-y-6">
        {scoreVal != null ? (
          <>
            <div className="flex justify-center">
              <CircularScore score={scoreVal} variant="eleos" size="lg" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 mb-2 capitalize">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {labelVal} Feasibility Plan
              </div>
              <h1 className="text-2xl font-extrabold text-slate-900">Campaign plan verified & created!</h1>
              <p className="text-slate-500 mt-2 text-sm leading-relaxed max-w-sm mx-auto">
                ELEOS has evaluated your proposal. Your campaign is ready and assigned an ELEOS Score.
              </p>
              {feasibility?.expected_budget_formatted && (
                <p className="text-xs text-slate-400 mt-1">
                  Expected Regional Baseline: <span className="font-semibold text-slate-600">{feasibility.expected_budget_formatted}</span>
                </p>
              )}
            </div>
          </>
        ) : (
          <>
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
              <Clock className="w-8 h-8 text-emerald-600 animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl font-extrabold text-slate-900">Campaign evaluation in progress</h1>
              <p className="text-slate-500 mt-3 text-sm leading-relaxed max-w-sm mx-auto">
                We've received your campaign details. ELEOS is now evaluating it to generate a Feasibility Score.
              </p>
              <p className="text-slate-400 mt-2 text-xs">
                {isFeasibilityLoading ? "Computing regional benchmarks..." : "This usually takes a few moments."}
              </p>
            </div>
          </>
        )}

        <div className="p-5 bg-white rounded-xl border border-slate-200 text-left max-w-sm mx-auto">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">What is the ELEOS Score?</p>
          <p className="text-sm text-slate-600 leading-relaxed">
            The ELEOS Score is specific to this campaign. It reflects how well-defined and realistic your
            campaign plan appears — based on your funding goal, location, timeline, and commodity rates.
          </p>
          {profile?.trust_score != null && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <p className="text-xs text-slate-400 mb-2">Your organisation's score is separate:</p>
              <CircularScore score={profile.trust_score} variant="trust" size="sm" />
            </div>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
          <Link
            href={createdCampaignId ? `/ngo/campaigns/${createdCampaignId}` : "/ngo/campaigns"}
            className={buttonVariants({ className: "bg-emerald-600 hover:bg-emerald-700 text-white" })}
          >
            View campaign
          </Link>
          <Link
            href="/ngo/campaigns"
            className={buttonVariants({ variant: "outline" })}
          >
            All campaigns
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Link
            href="/ngo/campaigns"
            className={buttonVariants({ variant: "ghost", size: "sm", className: "gap-1.5 text-slate-500 -ml-2" })}
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </Link>
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900">Create a new campaign</h1>
        <p className="text-sm text-slate-500 mt-1">
          Describe your campaign clearly. Your organisation's details are already linked — you don't need to re-enter them.
        </p>
      </div>

      {/* Step indicator */}
      <StepIndicator steps={STEPS} currentStep={step} />

      <Card className="border-slate-200 shadow-sm">
        <CardContent className="p-6 md:p-8">

          {/* ── STEP 0: About the campaign ─────────────────────────────────── */}
          {step === 0 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Tell us about the campaign</h2>
                <p className="text-sm text-slate-500 mt-1">Describe what you're trying to achieve and who it's for.</p>
              </div>
              <div className="space-y-5">
                <FormField label="Campaign title" required hint="Use a clear, specific title. Example: 'Clean Drinking Water for 5 Villages in Coimbatore'">
                  <Input
                    value={form.title}
                    onChange={(e) => set("title", e.target.value)}
                    placeholder="e.g. Clean Drinking Water for 5 Villages in Coimbatore"
                    className="text-base"
                  />
                </FormField>

                <FormField label="What are you trying to achieve?" required hint="Tell donors the story — what problem exists and what you will do about it.">
                  <textarea
                    value={form.description}
                    onChange={(e) => set("description", e.target.value)}
                    rows={5}
                    placeholder="Describe the situation, the need, and your plan to address it..."
                    className="w-full p-2.5 text-sm rounded-lg border border-slate-300 bg-white resize-none focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </FormField>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField label="What state is this campaign in?" required>
                    <SelectField
                      value={form.state}
                      onChange={(v) => set("state", v)}
                      placeholder="Select state"
                      options={INDIAN_STATES.map((s) => ({ value: s, label: s }))}
                    />
                  </FormField>
                  <FormField label="District or area" required>
                    <Input
                      value={form.district}
                      onChange={(e) => set("district", e.target.value)}
                      placeholder="e.g. Coimbatore"
                    />
                  </FormField>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField label="How many people will benefit?" required hint="Approximate number of beneficiaries.">
                    <div className="relative">
                      <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        type="number"
                        value={form.beneficiaries}
                        onChange={(e) => set("beneficiaries", e.target.value)}
                        placeholder="e.g. 2500"
                        className="pl-10"
                        min={1}
                      />
                    </div>
                  </FormField>
                  <FormField label="How many communities will this reach?">
                    <div className="relative">
                      <Home className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                      <Input
                        type="number"
                        value={form.communities}
                        onChange={(e) => set("communities", e.target.value)}
                        placeholder="e.g. 5 villages"
                        className="pl-10"
                        min={1}
                      />
                    </div>
                  </FormField>
                </div>

                <FormField label="What is this campaign for?" required>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {CAUSES.map((cause) => (
                      <button
                        key={cause.value}
                        type="button"
                        onClick={() => set("cause", cause.value)}
                        className={`px-3 py-2.5 rounded-lg text-sm font-medium border text-left transition-all ${
                          form.cause === cause.value
                            ? "border-emerald-500 bg-emerald-50 text-emerald-800 font-semibold"
                            : "border-slate-200 bg-white text-slate-600 hover:border-slate-400"
                        }`}
                      >
                        {cause.label}
                      </button>
                    ))}
                  </div>
                </FormField>
              </div>
            </div>
          )}

          {/* ── STEP 1: Campaign details ─────────────────────────────────────── */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Campaign details</h2>
                <p className="text-sm text-slate-500 mt-1">Set your funding goal, timeline, and a few quick context questions.</p>
              </div>
              <div className="space-y-5">
                <FormField label="How much funding do you need?" required hint="Enter the total amount in Indian Rupees (INR).">
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 font-semibold">₹</span>
                    <Input
                      type="number"
                      value={form.target_amount}
                      onChange={(e) => set("target_amount", e.target.value)}
                      placeholder="e.g. 500000"
                      className="pl-8 text-base font-mono"
                      min={1000}
                    />
                  </div>
                  {form.target_amount && parseInt(form.target_amount) > 0 && (
                    <p className="text-xs text-slate-500 mt-1">
                      = ₹{parseInt(form.target_amount).toLocaleString("en-IN")}
                    </p>
                  )}
                </FormField>

                <FormField
                  label="Primary commodity / supply type"
                  hint="Select the primary goods, supplies, or materials this campaign requires."
                >
                  <SelectField
                    value={form.commodity_type}
                    onChange={(v) => set("commodity_type", v)}
                    placeholder="Select primary commodity (optional)"
                    options={COMMODITY_OPTIONS}
                  />
                </FormField>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField label="When does the campaign start?" required>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                      <Input
                        type="date"
                        value={form.start_date}
                        onChange={(e) => set("start_date", e.target.value)}
                        className="pl-10"
                      />
                    </div>
                  </FormField>
                  <FormField label="When does it end?" required>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                      <Input
                        type="date"
                        value={form.end_date}
                        onChange={(e) => set("end_date", e.target.value)}
                        min={form.start_date}
                        className="pl-10"
                      />
                    </div>
                  </FormField>
                </div>
                {form.start_date && form.end_date && form.end_date <= form.start_date && (
                  <p className="text-xs text-red-600 flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    End date must be after start date.
                  </p>
                )}

                <FormField label="How urgent is this campaign?">
                  <div className="grid grid-cols-3 gap-3">
                    <UrgencyButton
                      value="standard"
                      selected={form.urgency === "standard"}
                      onClick={() => set("urgency", "standard")}
                      icon="📋"
                      description="Normal fundraising timeline"
                    />
                    <UrgencyButton
                      value="urgent"
                      selected={form.urgency === "urgent"}
                      onClick={() => set("urgency", "urgent")}
                      icon="⚡"
                      description="Time-sensitive need"
                    />
                    <UrgencyButton
                      value="emergency"
                      selected={form.urgency === "emergency"}
                      onClick={() => set("urgency", "emergency")}
                      icon="🚨"
                      description="Immediate crisis response"
                    />
                  </div>
                </FormField>

                <div className="space-y-3">
                  <ToggleField
                    checked={form.is_disaster_relief}
                    onChange={(v) => set("is_disaster_relief", v)}
                    label="Is this a disaster relief campaign?"
                    hint="e.g. responding to a flood, cyclone, or earthquake."
                  />
                  <ToggleField
                    checked={form.is_remote_area}
                    onChange={(v) => set("is_remote_area", v)}
                    label="Is this in a remote or hard-to-reach area?"
                    hint="This helps us understand potential logistical challenges."
                  />
                </div>
              </div>
            </div>
          )}

          {/* ── STEP 2: Milestones ────────────────────────────────────────────── */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Campaign milestones</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Break your campaign into major stages. Milestones let donors track your progress as you deliver on your promises.
                </p>
              </div>

              <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl text-xs text-blue-800 leading-relaxed">
                <p className="font-semibold mb-1">Tips for good milestones</p>
                <ul className="space-y-1 list-disc list-inside">
                  <li>Be specific about what will happen at each stage</li>
                  <li>Use plain language — "Install 10 water pumps", not "Phase 1 procurement"</li>
                  <li>3–5 milestones is usually ideal for most campaigns</li>
                </ul>
              </div>

              <div className="space-y-3">
                {form.milestones.map((m, idx) => (
                  <MilestoneRow
                    key={m.id}
                    milestone={m}
                    index={idx}
                    total={form.milestones.length}
                    onChange={updateMilestone}
                    onRemove={removeMilestone}
                    onMoveUp={(i) => moveMilestone(i, "up")}
                    onMoveDown={(i) => moveMilestone(i, "down")}
                  />
                ))}
              </div>

              <Button
                type="button"
                onClick={addMilestone}
                variant="outline"
                className="w-full gap-2 border-dashed border-slate-300 text-slate-600 hover:border-emerald-400 hover:text-emerald-700"
              >
                <Plus className="w-4 h-4" />
                Add another milestone
              </Button>
            </div>
          )}

          {/* ── STEP 3: Media ─────────────────────────────────────────────────── */}
          {step === 3 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Campaign media</h2>
                <p className="text-sm text-slate-500 mt-1">
                  A cover image makes your campaign stand out to donors. Images should be clear and relevant to your cause.
                </p>
              </div>

              <FormField
                label="Cover image"
                required
                hint="This is the main image donors will see. Recommended: 1200×630px."
              >
                <div className="space-y-3">
                  <div
                    className="border-2 border-dashed border-slate-200 rounded-xl p-8 flex flex-col items-center justify-center gap-3 text-center bg-slate-50 hover:border-emerald-300 hover:bg-emerald-50/30 transition-all cursor-pointer"
                    onClick={() => {
                      // Simulated — in production this would open a file picker
                      const url = prompt("Enter image URL (temporary until file upload is wired):");
                      if (url) set("cover_image_url", url);
                    }}
                  >
                    {form.cover_image_url ? (
                      <img
                        src={form.cover_image_url}
                        alt="Cover preview"
                        className="max-h-48 rounded-lg object-cover"
                      />
                    ) : (
                      <>
                        <UploadCloud className="w-10 h-10 text-slate-400" />
                        <div>
                          <p className="text-sm font-medium text-slate-700">
                            <span className="text-emerald-600 underline underline-offset-2">Click to upload</span>
                            {" "}your cover image
                          </p>
                          <p className="text-xs text-slate-400 mt-0.5">JPG, PNG · Recommended 1200×630</p>
                        </div>
                      </>
                    )}
                  </div>
                  {form.cover_image_url && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => set("cover_image_url", "")}
                      className="text-slate-400 hover:text-red-500 text-xs"
                    >
                      Remove image
                    </Button>
                  )}
                </div>
              </FormField>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500">
                Additional images (photos from the field, community photos, etc.) can be added after your campaign is published.
              </div>
            </div>
          )}

          {/* ── STEP 4: Review & submit ───────────────────────────────────────── */}
          {step === 4 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Review before submitting</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Here's a preview of your campaign. Check everything looks right before submitting.
                </p>
              </div>

              {/* Campaign preview card */}
              <div className="rounded-2xl border border-slate-200 overflow-hidden bg-white shadow-sm">
                {form.cover_image_url && (
                  <div className="h-48 overflow-hidden">
                    <img src={form.cover_image_url} alt="" className="w-full h-full object-cover" />
                  </div>
                )}
                <div className="p-5 space-y-4">
                  <div className="flex flex-wrap items-center gap-2">
                    {form.cause && (
                      <span className="inline-block text-xs font-semibold bg-slate-100 text-slate-600 px-2.5 py-1 rounded-md">
                        {causeLabel}
                      </span>
                    )}
                    {form.commodity_type && (
                      <span className="inline-block text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-md">
                        Commodity: {form.commodity_type}
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-extrabold text-slate-900">{form.title || "Campaign title"}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed line-clamp-3">{form.description}</p>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 border-t border-slate-100">
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Location</p>
                      <p className="text-sm font-medium text-slate-800 mt-0.5">
                        {form.district ? `${form.district}, ${form.state}` : form.state}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Beneficiaries</p>
                      <p className="text-sm font-medium text-slate-800 mt-0.5">
                        {form.beneficiaries ? parseInt(form.beneficiaries).toLocaleString("en-IN") : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Funding Goal</p>
                      <p className="text-sm font-medium text-slate-800 mt-0.5 font-mono">
                        {form.target_amount ? `₹${parseInt(form.target_amount).toLocaleString("en-IN")}` : "—"}
                      </p>
                    </div>
                    <div>
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Timeline</p>
                      <p className="text-sm font-medium text-slate-800 mt-0.5">
                        {form.start_date && form.end_date
                          ? `${new Date(form.start_date).toLocaleDateString("en-IN", { month: "short", day: "numeric" })} – ${new Date(form.end_date).toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}`
                          : "—"}
                      </p>
                    </div>
                  </div>

                  {/* Milestones preview */}
                  {form.milestones.filter((m) => m.title.trim()).length > 0 && (
                    <div className="pt-2 border-t border-slate-100">
                      <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Milestones</p>
                      <ol className="space-y-1.5">
                        {form.milestones.filter((m) => m.title.trim()).map((m, i) => (
                          <li key={m.id} className="flex items-start gap-2 text-sm text-slate-700">
                            <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                              {i + 1}
                            </span>
                            {m.title}
                          </li>
                        ))}
                      </ol>
                    </div>
                  )}
                </div>
              </div>

              {/* Trust Score callout — clearly separate from ELEOS score */}
              {profile?.trust_score != null && (
                <div className="p-4 rounded-xl border border-blue-100 bg-blue-50 flex items-start gap-4">
                  <CircularScore score={profile.trust_score} variant="trust" size="sm" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-blue-900">Your organisation's Trust Score</p>
                    <p className="text-xs text-blue-700 mt-0.5">
                      This belongs to your organisation — it is separate from this campaign's evaluation.
                      Donors will be able to see both scores on the campaign page.
                    </p>
                  </div>
                </div>
              )}

              {/* ELEOS score explanation */}
              <div className="p-4 rounded-xl border border-emerald-100 bg-emerald-50">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-200 flex items-center justify-center shrink-0">
                    <Target className="w-4 h-4 text-emerald-700" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-emerald-900">What happens after you submit?</p>
                    <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
                      ELEOS will evaluate this campaign and generate an <strong>ELEOS Score</strong> — 
                      a measure of how well-defined and realistic your plan appears. This score is specific to 
                      this campaign, and is separate from your organisation's Trust Score.
                    </p>
                  </div>
                </div>
              </div>

              {submitError && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  {submitError}
                </div>
              )}
            </div>
          )}

          {/* ── Navigation ─────────────────────────────────────────────────────── */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t border-slate-100">
            <Button
              variant="ghost"
              onClick={() => setStep((s) => Math.max(0, s - 1))}
              disabled={step === 0}
              className="gap-1.5 text-slate-600"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </Button>

            {step < 4 ? (
              <Button
                onClick={() => setStep((s) => s + 1)}
                disabled={!canProceed()}
                className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                Continue
                <ArrowRight className="w-4 h-4" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white min-w-40"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Submitting…
                  </>
                ) : (
                  <>
                    Submit campaign
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

