"use client";

import { ShieldCheck, Activity } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/context/AuthContext";
import { PersonaSwitcher } from "@/components/PersonaSwitcher";

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const { user } = useAuth();
  const pathname = usePathname();
  const isHome = pathname === "/";

  useEffect(() => {
    // Reset visibility state whenever the route changes
    setIsVisible(false);
    setIsScrolled(false);

    const handleScroll = () => {
      const y = window.scrollY;
      setIsScrolled(y > 20);
      if (isHome) {
        // Show navbar once user has scrolled down a bit; hide again at the very top
        setIsVisible(y > 50);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    // Run once on mount so state reflects current scroll position on route change
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, [isHome]);

  // ── Inner content shared between both render modes ──────────────────────────
  const inner = (
    <div className="container mx-auto px-4 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2">
        <ShieldCheck className="text-emerald-600 h-6 w-6" />
        <span className="font-bold tracking-tight text-emerald-950 font-pixel uppercase text-lg">
          Eleos
        </span>
      </Link>

      <div className="hidden md:flex gap-6">
        <Link href="/" className="relative group text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors">
          Home
          <span className="absolute -bottom-1.5 left-1/2 w-0 h-0.5 bg-emerald-600 transition-all duration-300 group-hover:w-full group-hover:left-0" />
        </Link>
        <Link href="/campaigns" className="relative group text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors">
          Browse Campaigns
          <span className="absolute -bottom-1.5 left-1/2 w-0 h-0.5 bg-emerald-600 transition-all duration-300 group-hover:w-full group-hover:left-0" />
        </Link>
        <Link href="/volunteer" className="relative group text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors">
          Volunteer Hub
          <span className="absolute -bottom-1.5 left-1/2 w-0 h-0.5 bg-emerald-600 transition-all duration-300 group-hover:w-full group-hover:left-0" />
        </Link>
        {user && (
          <Link href={user.role === 'ngo_admin' ? '/ngo/dashboard' : user.role === 'reviewer' ? '/reviewer' : '/dashboard'} className="relative group text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors">
            My Dashboard
            <span className="absolute -bottom-1.5 left-1/2 w-0 h-0.5 bg-emerald-600 transition-all duration-300 group-hover:w-full group-hover:left-0" />
          </Link>
        )}
      </div>

      <div className="flex items-center gap-3">
        <Link href="/campaigns">
          <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-4">
            Donate Now
          </Button>
        </Link>
        <PersonaSwitcher />
      </div>
    </div>
  );

  // ── Home page: fixed, hidden at top, slides in on scroll ────────────────────
  if (isHome) {
    return (
      <nav
        className={[
          "fixed top-0 left-0 right-0 w-full z-40",
          "border-b bg-white/95 backdrop-blur-sm",
          "transition-all duration-300 ease-in-out",
          isVisible
            ? "translate-y-0 opacity-100 py-2 shadow-sm"
            : "-translate-y-full opacity-0 py-3 pointer-events-none",
        ].join(" ")}
      >
        {inner}
      </nav>
    );
  }

  // ── All other pages: existing sticky behaviour ───────────────────────────────
  return (
    <nav
      className={[
        "border-b bg-white/95 backdrop-blur-sm sticky top-0 z-40",
        "transition-all duration-300",
        isScrolled ? "py-2 shadow-sm" : "py-3",
      ].join(" ")}
    >
      {inner}
    </nav>
  );
}
