"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  HeartHandshake,
  Building2,
  ShieldCheck,
  UserCheck,
  Sliders,
  ExternalLink,
  Cpu
} from "lucide-react";

export function PersonaSwitcher() {
  const { user, switchPersona, isLoading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const personas = [
    {
      role: "donor" as const,
      label: "Donor",
      icon: HeartHandshake,
      dashboardUrl: "/",
      dashboardLabel: "Homepage",
    },
    {
      role: "ngo_admin" as const,
      label: "NGO Admin",
      icon: Building2,
      dashboardUrl: "/ngo/dashboard",
      dashboardLabel: "NGO Portal",
    }
  ];

  const currentPersona = personas.find((p) => p.role === user?.role) || personas[0];
  const CurrentIcon = currentPersona.icon;

  const handlePersonaSwitch = async (role: any, url: string) => {
    if (user?.role === role) return;
    setIsOpen(false); // Close immediately for snappy feel
    await switchPersona(role);
    router.push(url);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Avatar Button */}
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="focus:outline-none transition-transform hover:scale-105 active:scale-95 flex items-center justify-center"
        title="Switch Persona"
      >
        <Avatar className="h-9 w-9 border-2 border-emerald-100 ring-2 ring-emerald-500/20 bg-emerald-50">
          <AvatarFallback className="bg-emerald-100 text-emerald-700">
            <CurrentIcon className="w-5 h-5" />
          </AvatarFallback>
        </Avatar>
      </button>
      
      {/* Custom Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-white border border-slate-200 shadow-xl rounded-xl p-2 z-50 animate-in fade-in slide-in-from-top-2">
          
          <div className="px-2 py-1.5 text-xs text-slate-400 font-semibold uppercase tracking-wider">
            Switch Persona
          </div>
          
          {/* Persona List */}
          <div className="p-1 space-y-1">
            {personas.map((p) => {
              const Icon = p.icon;
              const isActive = user?.role === p.role;
              return (
                <button
                  key={p.role}
                  onClick={() => handlePersonaSwitch(p.role, p.dashboardUrl)}
                  disabled={isLoading || isActive}
                  className={`w-full flex items-center gap-2 px-2 py-2 text-sm rounded-md transition-colors text-left ${
                    isActive 
                      ? "bg-slate-100 text-slate-900 font-semibold pointer-events-none" 
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-emerald-600" : "text-slate-400"}`} />
                  <span>{p.label}</span>
                  {isActive && (
                    <span className="ml-auto w-2 h-2 rounded-full bg-emerald-500"></span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
