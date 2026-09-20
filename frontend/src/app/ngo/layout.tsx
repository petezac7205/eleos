"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  FolderOpen,
  PlusCircle,
  ShieldCheck,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { ngoApi, NGOProfileData } from "@/lib/api";
import { CircularScore } from "@/components/ngo/CircularScore";

const NAV_ITEMS = [
  {
    label: "Dashboard",
    href: "/ngo/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Organisation",
    href: "/ngo/organisation",
    icon: Building2,
    sub: [
      { label: "Details & Documents", href: "/ngo/organisation" },
    ],
  },
  {
    label: "Campaigns",
    href: "/ngo/campaigns",
    icon: FolderOpen,
    sub: [
      { label: "All campaigns", href: "/ngo/campaigns" },
      { label: "Create campaign", href: "/ngo/campaigns/new" },
    ],
  },
];

export default function NgoPortalLayout({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [profile, setProfile] = useState<NGOProfileData | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    // Redirect unauthenticated users or non-NGO admins
    if (!user) {
      router.push("/");
      return;
    }
    if (user.role !== "ngo_admin") {
      router.push("/");
      return;
    }
    ngoApi.getMeProfile().catch(() => null).then(setProfile);
  }, [user, router]);

  const isVerified = profile?.verification_status === "verified";
  const isPending = profile?.verification_status === "pending";

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(href + "/");

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* ── Sidebar ── */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-slate-200 flex flex-col
          transition-transform duration-300 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
          md:translate-x-0 md:relative md:inset-auto md:block
        `}
      >
        {/* Brand */}
        <div className="p-5 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 bg-emerald-100 rounded-lg flex items-center justify-center shrink-0">
            <ShieldCheck className="w-5 h-5 text-emerald-700" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <span className="font-bold text-emerald-900 font-pixel text-sm uppercase tracking-tight">Eleos</span>
              <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-semibold">NGO</span>
            </div>
            <p className="text-[11px] text-slate-500 truncate mt-0.5">
              {profile?.name ?? user?.name ?? "Organisation Portal"}
            </p>
          </div>
        </div>

        {/* Trust Score — only when verified */}
        {isVerified && profile?.trust_score != null && (
          <div className="px-4 pt-4 pb-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Organisation score</p>
            <CircularScore score={profile.trust_score} variant="trust" size="sm" />
          </div>
        )}

        {/* Pending banner */}
        {isPending && (
          <div className="mx-4 mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
            <p className="text-[11px] text-amber-800 font-semibold leading-tight">Verification in progress</p>
            <p className="text-[10px] text-amber-700 mt-0.5">You'll be notified once approved.</p>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto mt-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <div key={item.href}>
                <Link
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? "bg-emerald-50 text-emerald-800 font-semibold"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${active ? "text-emerald-600" : "text-slate-400"}`} />
                  <span className="flex-1">{item.label}</span>
                  {item.sub && (
                    <ChevronRight className={`w-3.5 h-3.5 transition-transform ${active ? "rotate-90 text-emerald-500" : "text-slate-300"}`} />
                  )}
                </Link>

                {/* Sub-items — shown when parent active */}
                {item.sub && active && (
                  <div className="ml-9 mt-0.5 space-y-0.5">
                    {item.sub.map((sub) => (
                      <Link
                        key={sub.href}
                        href={sub.href}
                        onClick={() => setSidebarOpen(false)}
                        className={`block px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                          pathname === sub.href
                            ? "text-emerald-700 bg-emerald-50/80"
                            : "text-slate-500 hover:text-slate-800"
                        }`}
                      >
                        {sub.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Create Campaign CTA */}
          <div className="pt-3 mt-3 border-t border-slate-100">
            <Link
              href="/ngo/campaigns/new"
              onClick={() => setSidebarOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-colors"
            >
              <PlusCircle className="w-4 h-4 shrink-0" />
              Create Campaign
            </Link>
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-slate-100">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5" />
            Back to main site
          </Link>
        </div>
      </aside>

      {/* ── Mobile overlay ── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Main content ── */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Mobile topbar */}
        <div className="md:hidden flex items-center gap-3 p-4 bg-white border-b border-slate-200 sticky top-0 z-10">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="w-8 h-8 flex flex-col items-center justify-center gap-1 rounded-md hover:bg-slate-100"
            aria-label="Open navigation"
          >
            <span className="w-5 h-0.5 bg-slate-700 rounded" />
            <span className="w-5 h-0.5 bg-slate-700 rounded" />
            <span className="w-5 h-0.5 bg-slate-700 rounded" />
          </button>
          <span className="font-bold text-emerald-900 font-pixel text-sm uppercase">Eleos NGO</span>
        </div>

        <main className="flex-1 p-6 md:p-8 max-w-5xl mx-auto w-full">
          {children}
        </main>
      </div>
    </div>
  );
}

