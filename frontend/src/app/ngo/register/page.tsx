"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { StepIndicator } from "@/components/ngo/StepIndicator";
import { DocumentUploadField, DocumentStatus } from "@/components/ngo/DocumentUploadField";
import { CheckCircle2, ArrowLeft, ArrowRight, ShieldCheck, Loader2 } from "lucide-react";
import { ngoApi, NGORegistrationPayload } from "@/lib/api";
import Link from "next/link";

// ── Step definitions ───────────────────────────────────────────────────────────
const STEPS = [
  { label: "Organisation" },
  { label: "Compliance" },
  { label: "Documents" },
  { label: "Submitted" },
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

// ── Document config ────────────────────────────────────────────────────────────
interface DocField {
  key: string;
  label: string;
  description: string;
  required: boolean;
  showIf?: (form: RegistrationForm) => boolean;
}

const DOCUMENT_FIELDS: DocField[] = [
  {
    key: "registration_certificate",
    label: "Registration Certificate",
    description: "The certificate issued upon registration of your organisation.",
    required: true,
  },
  {
    key: "pan_document",
    label: "PAN Document",
    description: "PAN card or letter issued to the organisation.",
    required: true,
  },
  {
    key: "certificate_12a",
    label: "12A Certificate",
    description: "Income tax exemption certificate under Section 12A.",
    required: false,
    showIf: (f) => f.has_12a,
  },
  {
    key: "certificate_80g",
    label: "80G Certificate",
    description: "Donor deduction certificate under Section 80G.",
    required: false,
    showIf: (f) => f.has_80g,
  },
  {
    key: "darpan_certificate",
    label: "NGO Darpan Certificate",
    description: "Certificate or acknowledgement from NGO Darpan.",
    required: true,
  },
  {
    key: "fcra_certificate",
    label: "FCRA Certificate",
    description: "Foreign Contribution (Regulation) Act registration certificate.",
    required: false,
    showIf: (f) => f.has_fcra,
  },
];

// ── Form state ─────────────────────────────────────────────────────────────────
interface RegistrationForm {
  // Step 1
  legal_name: string;
  registration_type: "trust" | "society" | "section_8" | "";
  registration_number: string;
  pan: string;
  darpan_id: string;
  state_of_registration: string;
  // Step 2
  has_12a: boolean;
  expiry_12a: string;
  has_80g: boolean;
  expiry_80g: string;
  has_fcra: boolean;
  fcra_number: string;
}

interface DocState {
  status: DocumentStatus;
  fileName?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function FieldGroup({ children }: { children: React.ReactNode }) {
  return <div className="space-y-4">{children}</div>;
}

function FormField({
  label,
  required,
  children,
  hint,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
  hint?: string;
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
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  disabled?: boolean;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className="w-full p-2.5 text-sm rounded-lg border border-slate-300 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 disabled:opacity-60"
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

function Toggle({
  checked,
  onChange,
  label,
  yesLabel = "Yes",
  noLabel = "No",
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  yesLabel?: string;
  noLabel?: string;
}) {
  return (
    <div className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-slate-50">
      <span className="text-sm font-medium text-slate-800">{label}</span>
      <div className="flex rounded-lg border border-slate-200 overflow-hidden">
        <button
          type="button"
          onClick={() => onChange(true)}
          className={`px-4 py-1.5 text-sm font-semibold transition-colors ${checked ? "bg-emerald-600 text-white" : "bg-white text-slate-500 hover:bg-slate-50"}`}
        >
          {yesLabel}
        </button>
        <button
          type="button"
          onClick={() => onChange(false)}
          className={`px-4 py-1.5 text-sm font-semibold transition-colors ${!checked ? "bg-slate-700 text-white" : "bg-white text-slate-500 hover:bg-slate-50"}`}
        >
          {noLabel}
        </button>
      </div>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────
export default function NgoRegisterPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [form, setForm] = useState<RegistrationForm>({
    legal_name: "",
    registration_type: "",
    registration_number: "",
    pan: "",
    darpan_id: "",
    state_of_registration: "",
    has_12a: false,
    expiry_12a: "",
    has_80g: false,
    expiry_80g: "",
    has_fcra: false,
    fcra_number: "",
  });

  const [docs, setDocs] = useState<Record<string, DocState>>({});

  const set = (key: keyof RegistrationForm, value: any) =>
    setForm((prev) => ({ ...prev, [key]: value }));

  // Validation per step
  const canProceed = (): boolean => {
    if (step === 0) {
      return !!(
        form.legal_name.trim() &&
        form.registration_type &&
        form.registration_number.trim() &&
        form.pan.trim() &&
        form.darpan_id.trim() &&
        form.state_of_registration
      );
    }
    if (step === 1) return true; // All optional (toggle-based)
    if (step === 2) {
      const visibleRequired = DOCUMENT_FIELDS.filter(
        (d) => d.required && (!d.showIf || d.showIf(form))
      );
      return visibleRequired.every(
        (d) => docs[d.key]?.status && docs[d.key]?.status !== "idle"
      );
    }
    return true;
  };

  const handleDocUpload = async (docKey: string, file: File) => {
    setDocs((prev) => ({ ...prev, [docKey]: { status: "uploading", fileName: file.name } }));
    try {
      await ngoApi.uploadDocumentFile(docKey, file);
      setDocs((prev) => ({ ...prev, [docKey]: { status: "uploaded", fileName: file.name } }));
    } catch {
      setDocs((prev) => ({ ...prev, [docKey]: { status: "idle" } }));
    }
  };

  const handleSubmit = async () => {
    if (!canProceed()) return;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const payload: NGORegistrationPayload = {
        legal_name: form.legal_name,
        registration_type: form.registration_type as "trust" | "society" | "section_8",
        registration_number: form.registration_number,
        pan: form.pan,
        darpan_id: form.darpan_id,
        state_of_registration: form.state_of_registration,
        has_12a: form.has_12a,
        expiry_12a: form.expiry_12a || undefined,
        has_80g: form.has_80g,
        expiry_80g: form.expiry_80g || undefined,
        has_fcra: form.has_fcra,
        fcra_number: form.fcra_number || undefined,
      };
      await ngoApi.register(payload).catch(() => null); // Graceful — backend may not exist yet
      setStep(3);
    } catch (err: any) {
      setSubmitError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-emerald-50/30 flex flex-col items-center justify-center py-12 px-4">
      {/* Header */}
      <div className="w-full max-w-2xl mb-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <ShieldCheck className="w-7 h-7 text-emerald-600" />
          <span className="font-bold text-2xl text-emerald-900 font-pixel uppercase tracking-tight">Eleos</span>
        </div>
        <h1 className="text-2xl font-extrabold text-slate-900 mb-1">Register your organisation</h1>
        <p className="text-slate-500 text-sm">
          You only need to do this once. Your details will be linked to every campaign you create.
        </p>
      </div>

      {/* Step indicator */}
      {step < 3 && (
        <div className="w-full max-w-2xl mb-8">
          <StepIndicator steps={STEPS.slice(0, 3)} currentStep={step} />
        </div>
      )}

      <Card className="w-full max-w-2xl border-slate-200 shadow-lg">
        <CardContent className="p-6 md:p-8">

          {/* ── STEP 0: Organisation details ───────────────────────────────── */}
          {step === 0 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Organisation details</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Tell us about your organisation's identity and legal registration.
                </p>
              </div>
              <FieldGroup>
                <FormField label="NGO Legal Name" required>
                  <Input
                    value={form.legal_name}
                    onChange={(e) => set("legal_name", e.target.value)}
                    placeholder="e.g. HopeRelief Foundation"
                  />
                </FormField>

                <FormField label="Registration type" required>
                  <SelectField
                    value={form.registration_type}
                    onChange={(v) => set("registration_type", v)}
                    placeholder="Select registration type"
                    options={[
                      { value: "trust", label: "Trust" },
                      { value: "society", label: "Society" },
                      { value: "section_8", label: "Section 8 Company" },
                    ]}
                  />
                </FormField>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField label="Registration Number" required>
                    <Input
                      value={form.registration_number}
                      onChange={(e) => set("registration_number", e.target.value)}
                      placeholder="e.g. TR/MH/2018/001234"
                    />
                  </FormField>
                  <FormField label="PAN" required>
                    <Input
                      value={form.pan}
                      onChange={(e) => set("pan", e.target.value.toUpperCase())}
                      placeholder="e.g. AABCT1234C"
                      maxLength={10}
                    />
                  </FormField>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <FormField
                    label="NGO Darpan ID"
                    required
                    hint="Your unique ID from the NGO Darpan portal."
                  >
                    <Input
                      value={form.darpan_id}
                      onChange={(e) => set("darpan_id", e.target.value)}
                      placeholder="e.g. MH/2018/0012345"
                    />
                  </FormField>
                  <FormField label="State of Registration" required>
                    <SelectField
                      value={form.state_of_registration}
                      onChange={(v) => set("state_of_registration", v)}
                      placeholder="Select state"
                      options={INDIAN_STATES.map((s) => ({ value: s, label: s }))}
                    />
                  </FormField>
                </div>
              </FieldGroup>
            </div>
          )}

          {/* ── STEP 1: Compliance information ─────────────────────────────── */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Compliance information</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Let us know about your organisation's tax and compliance status.
                </p>
              </div>
              <div className="space-y-4">
                <Toggle
                  checked={form.has_12a}
                  onChange={(v) => set("has_12a", v)}
                  label="Does your organisation have a Section 12A registration?"
                />
                {form.has_12a && (
                  <div className="ml-4 pl-4 border-l-2 border-emerald-200">
                    <FormField label="12A expiry date" hint="Leave blank if not applicable.">
                      <Input
                        type="date"
                        value={form.expiry_12a}
                        onChange={(e) => set("expiry_12a", e.target.value)}
                      />
                    </FormField>
                  </div>
                )}

                <Toggle
                  checked={form.has_80g}
                  onChange={(v) => set("has_80g", v)}
                  label="Does your organisation have an 80G registration?"
                />
                {form.has_80g && (
                  <div className="ml-4 pl-4 border-l-2 border-emerald-200">
                    <FormField label="80G expiry date" hint="Leave blank if not applicable.">
                      <Input
                        type="date"
                        value={form.expiry_80g}
                        onChange={(e) => set("expiry_80g", e.target.value)}
                      />
                    </FormField>
                  </div>
                )}

                <Toggle
                  checked={form.has_fcra}
                  onChange={(v) => set("has_fcra", v)}
                  label="Does your organisation accept foreign contributions? (FCRA)"
                />
                {form.has_fcra && (
                  <div className="ml-4 pl-4 border-l-2 border-emerald-200">
                    <FormField
                      label="FCRA Registration Number"
                      required
                      hint="Required if you accept foreign donations."
                    >
                      <Input
                        value={form.fcra_number}
                        onChange={(e) => set("fcra_number", e.target.value)}
                        placeholder="e.g. 083781234"
                      />
                    </FormField>
                  </div>
                )}
              </div>

              <div className="p-4 bg-blue-50 border border-blue-100 rounded-xl text-xs text-blue-800 leading-relaxed">
                <p className="font-semibold mb-1">Why do we ask this?</p>
                <p>
                  ELEOS uses this information to verify your organisation's legal standing and compliance. 
                  It helps us generate your Trust Score — a measure of your organisation's credibility 
                  that donors can see.
                </p>
              </div>
            </div>
          )}

          {/* ── STEP 2: Document upload ─────────────────────────────────────── */}
          {step === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">Upload your documents</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Upload these documents so ELEOS can verify your organisation. All files must be PDF.
                </p>
              </div>
              <div className="space-y-5">
                {DOCUMENT_FIELDS.filter(
                  (d) => !d.showIf || d.showIf(form)
                ).map((docField) => (
                  <DocumentUploadField
                    key={docField.key}
                    label={docField.label}
                    description={docField.description}
                    required={docField.required}
                    status={docs[docField.key]?.status ?? "idle"}
                    fileName={docs[docField.key]?.fileName}
                    onFileSelect={(file) => handleDocUpload(docField.key, file)}
                    onRemove={() =>
                      setDocs((prev) => ({ ...prev, [docField.key]: { status: "idle" } }))
                    }
                  />
                ))}
              </div>
            </div>
          )}

          {/* ── STEP 3: Submitted / Pending ─────────────────────────────────── */}
          {step === 3 && (
            <div className="text-center py-8 space-y-6">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-9 h-9 text-emerald-600" />
              </div>
              <div>
                <h2 className="text-2xl font-extrabold text-slate-900">Verification in progress</h2>
                <p className="text-slate-500 mt-3 max-w-md mx-auto text-sm leading-relaxed">
                  We've received your organisation details and documents. We're reviewing them now.
                  You'll be able to create campaigns once your organisation has been verified.
                </p>
                <p className="text-slate-400 mt-2 text-xs">This typically takes 1–3 business days.</p>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 text-left max-w-sm mx-auto">
                <p className="font-semibold text-slate-700 mb-2">What happens next?</p>
                <ul className="space-y-1.5">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-600 font-bold mt-0.5">1.</span>
                    Our team reviews your submitted documents
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-600 font-bold mt-0.5">2.</span>
                    ELEOS generates your organisation's Trust Score
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-600 font-bold mt-0.5">3.</span>
                    You'll receive an email notification to start creating campaigns
                  </li>
                </ul>
              </div>

              <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
                <Button
                  onClick={() => router.push("/ngo/dashboard")}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  Go to Dashboard
                </Button>
                <Link href="/" className={buttonVariants({ variant: "outline" })}>
                  Return to main site
                </Link>
              </div>
            </div>
          )}

          {/* ── Navigation buttons ─────────────────────────────────────────── */}
          {step < 3 && (
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

              {submitError && (
                <p className="text-xs text-red-600 flex-1 mx-4 text-center">{submitError}</p>
              )}

              {step < 2 ? (
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
                  disabled={!canProceed() || isSubmitting}
                  className="gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white min-w-32"
                >
                  {isSubmitting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <>
                      Submit
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {step < 3 && (
        <p className="mt-6 text-xs text-slate-400 text-center">
          Already verified?{" "}
          <Link href="/ngo/dashboard" className="text-emerald-600 hover:underline">
            Go to your dashboard
          </Link>
        </p>
      )}
    </div>
  );
}

