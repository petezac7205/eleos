/**
 * DocumentUploadField — drag-and-drop + file picker for PDF document upload.
 *
 * Deliberately avoids all backend/hash/blockchain terminology.
 * The NGO simply sees: document name → upload → status indicator.
 */

"use client";

import React, { useRef, useState, useCallback } from "react";
import { UploadCloud, FileText, CheckCircle2, Clock, AlertCircle, X } from "lucide-react";

export type DocumentStatus = "idle" | "uploading" | "uploaded" | "under_review" | "verified" | "rejected";

interface DocumentUploadFieldProps {
  label: string;
  description?: string;
  required?: boolean;
  status?: DocumentStatus;
  fileName?: string;
  onFileSelect: (file: File) => Promise<void>;
  onRemove?: () => void;
  disabled?: boolean;
}

const STATUS_CONFIG: Record<
  Exclude<DocumentStatus, "idle" | "uploading">,
  { icon: React.ReactNode; label: string; className: string }
> = {
  uploaded: {
    icon: <Clock className="w-3.5 h-3.5" />,
    label: "Uploaded — pending review",
    className: "text-amber-700 bg-amber-50 border-amber-200",
  },
  under_review: {
    icon: <Clock className="w-3.5 h-3.5" />,
    label: "Under review",
    className: "text-blue-700 bg-blue-50 border-blue-200",
  },
  verified: {
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
    label: "Verified",
    className: "text-emerald-700 bg-emerald-50 border-emerald-200",
  },
  rejected: {
    icon: <AlertCircle className="w-3.5 h-3.5" />,
    label: "Rejected — please re-upload",
    className: "text-red-700 bg-red-50 border-red-200",
  },
};

export function DocumentUploadField({
  label,
  description,
  required = false,
  status = "idle",
  fileName,
  onFileSelect,
  onRemove,
  disabled = false,
}: DocumentUploadFieldProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleFile = useCallback(
    async (file: File) => {
      setLocalError(null);
      if (!file.type.includes("pdf")) {
        setLocalError("Please upload a PDF file.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setLocalError("File must be under 10 MB.");
        return;
      }
      try {
        await onFileSelect(file);
      } catch {
        setLocalError("Upload failed. Please try again.");
      }
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const hasFile = status !== "idle" && fileName;
  const statusCfg = hasFile && status !== "uploading" ? STATUS_CONFIG[status as Exclude<DocumentStatus, "idle" | "uploading">] : null;

  return (
    <div className="space-y-1.5">
      {/* Label */}
      <div className="flex items-center gap-1.5">
        <span className="text-sm font-semibold text-slate-800">{label}</span>
        {required && <span className="text-xs text-red-500 font-medium">Required</span>}
      </div>
      {description && <p className="text-xs text-slate-500">{description}</p>}

      {/* Upload zone or file display */}
      {hasFile ? (
        <div className={`flex items-center justify-between p-3 rounded-lg border text-xs font-medium ${statusCfg?.className ?? "text-slate-700 bg-slate-50 border-slate-200"}`}>
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="w-4 h-4 shrink-0" />
            <span className="truncate">{fileName}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0 ml-2">
            {status === "uploading" ? (
              <span className="flex items-center gap-1 text-slate-500">
                <span className="w-3 h-3 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                Uploading…
              </span>
            ) : (
              <span className="flex items-center gap-1">
                {statusCfg?.icon}
                {statusCfg?.label}
              </span>
            )}
            {onRemove && status !== "verified" && status !== "uploading" && (
              <button
                type="button"
                onClick={onRemove}
                className="ml-1 text-slate-400 hover:text-red-500 transition-colors"
                aria-label="Remove document"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      ) : (
        <div
          className={`relative border-2 border-dashed rounded-xl p-5 flex flex-col items-center justify-center gap-2 text-center transition-all cursor-pointer ${
            disabled
              ? "border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed"
              : isDragging
              ? "border-emerald-400 bg-emerald-50"
              : "border-slate-200 bg-slate-50 hover:border-emerald-300 hover:bg-emerald-50/40"
          }`}
          onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={disabled ? undefined : handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          role="button"
          tabIndex={disabled ? -1 : 0}
          onKeyDown={(e) => e.key === "Enter" && !disabled && inputRef.current?.click()}
          aria-label={`Upload ${label}`}
        >
          <UploadCloud className={`w-8 h-8 ${isDragging ? "text-emerald-500" : "text-slate-400"}`} />
          <div>
            <p className="text-sm font-medium text-slate-700">
              <span className="text-emerald-600 underline underline-offset-2">Click to upload</span>
              {" "}or drag and drop
            </p>
            <p className="text-xs text-slate-400 mt-0.5">PDF only · max 10 MB</p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,application/pdf"
            className="sr-only"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
              e.target.value = "";
            }}
            disabled={disabled}
          />
        </div>
      )}

      {localError && (
        <p className="text-xs text-red-600 flex items-center gap-1">
          <AlertCircle className="w-3.5 h-3.5 shrink-0" />
          {localError}
        </p>
      )}
    </div>
  );
}

