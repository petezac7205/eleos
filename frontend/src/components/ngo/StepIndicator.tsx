/**
 * StepIndicator — multi-step progress bar used by the registration
 * wizard and the campaign creation wizard.
 */

import React from "react";
import { CheckCircle2 } from "lucide-react";

interface Step {
  label: string;
}

interface StepIndicatorProps {
  steps: Step[];
  currentStep: number; // 0-indexed
}

export function StepIndicator({ steps, currentStep }: StepIndicatorProps) {
  return (
    <div className="w-full">
      {/* Desktop: horizontal with lines */}
      <div className="hidden sm:flex items-center w-full">
        {steps.map((step, idx) => {
          const isDone = idx < currentStep;
          const isActive = idx === currentStep;
          return (
            <React.Fragment key={idx}>
              <div className="flex flex-col items-center">
                {/* Dot */}
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 transition-all duration-300 ${
                    isDone
                      ? "bg-emerald-600 border-emerald-600 text-white"
                      : isActive
                      ? "bg-white border-emerald-600 text-emerald-700"
                      : "bg-white border-slate-300 text-slate-400"
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>
                {/* Label */}
                <span
                  className={`mt-1.5 text-[11px] font-semibold text-center max-w-[80px] leading-tight ${
                    isActive ? "text-emerald-700" : isDone ? "text-slate-700" : "text-slate-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {idx < steps.length - 1 && (
                <div className="flex-1 h-0.5 mb-5 mx-2 transition-all duration-300">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      idx < currentStep ? "bg-emerald-500" : "bg-slate-200"
                    }`}
                  />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Mobile: compact "Step X of N" */}
      <div className="sm:hidden flex items-center gap-3">
        <div className="flex gap-1.5">
          {steps.map((_, idx) => (
            <div
              key={idx}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                idx < currentStep
                  ? "w-4 bg-emerald-500"
                  : idx === currentStep
                  ? "w-6 bg-emerald-600"
                  : "w-4 bg-slate-200"
              }`}
            />
          ))}
        </div>
        <span className="text-xs text-slate-500 font-medium">
          Step {currentStep + 1} of {steps.length}
        </span>
      </div>
    </div>
  );
}

