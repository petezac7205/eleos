"use client";

import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  MapPin, 
  Clock, 
  Search, 
  Filter, 
  Users, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle,
  Award,
  ExternalLink,
  HeartHandshake,
  Send,
  Loader2,
  X,
  Cpu
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { 
  volunteerApi, 
  VolunteerOpportunity, 
  VolunteerApplication, 
  VolunteerCredential 
} from "@/lib/api";

const triggerClass =
  "relative group bg-transparent data-active:bg-transparent data-active:shadow-none data-active:text-emerald-700 text-slate-600 hover:text-emerald-700 transition-colors text-sm font-semibold py-3 px-5 rounded-none";

export default function VolunteerPage() {
  const { user } = useAuth();
  const [opportunities, setOpportunities] = useState<VolunteerOpportunity[]>([]);
  const [myApplications, setMyApplications] = useState<VolunteerApplication[]>([]);
  const [myCredentials, setMyCredentials] = useState<VolunteerCredential[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedTier, setSelectedTier] = useState<string>("All");

  // Application Modal state
  const [selectedOpp, setSelectedOpp] = useState<VolunteerOpportunity | null>(null);
  const [hoursCommitted, setHoursCommitted] = useState<number>(10);
  const [appMessage, setAppMessage] = useState<string>("");
  const [isApplying, setIsApplying] = useState<boolean>(false);
  const [applySuccess, setApplySuccess] = useState<boolean>(false);
  const [applyError, setApplyError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [opps, apps, creds] = await Promise.all([
        volunteerApi.getOpportunities(selectedTier !== "All" ? { safety_tier: selectedTier } : undefined).catch(() => []),
        volunteerApi.getMyApplications().catch(() => []),
        volunteerApi.getMyCredentials().catch(() => []),
      ]);
      setOpportunities(opps);
      setMyApplications(apps);
      setMyCredentials(creds);
    } catch (err) {
      console.error("Failed to load volunteer data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedTier]);

  const handleApplySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOpp) return;
    setIsApplying(true);
    setApplyError(null);

    try {
      await volunteerApi.apply(selectedOpp.id, appMessage, hoursCommitted);
      setApplySuccess(true);
      fetchData();
    } catch (err: any) {
      setApplyError(err.message || "Failed to submit volunteer application.");
    } finally {
      setIsApplying(false);
    }
  };

  const filteredOpportunities = opportunities.filter((opp) => {
    const matchesSearch =
      opp.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (opp.campaign_title || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      (opp.location_city || "").toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      {/* Hero Section */}
      <section className="bg-slate-950 text-white py-16 px-4 relative overflow-hidden border-b border-slate-800">
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-950/40 via-slate-950 to-teal-950/40" />
        <div className="max-w-6xl mx-auto relative z-10 text-center">
          <Badge className="mb-4 bg-emerald-500/20 text-emerald-300 border-emerald-500/40 text-xs py-1">
            <HeartHandshake className="w-3.5 h-3.5 mr-1" /> On-Ground & Remote Impact Network
          </Badge>
          <h1 className="text-3xl md:text-5xl font-extrabold mb-4 tracking-tight leading-tight">
            Donate your time. <span className="text-emerald-400">Earn On-Chain Credentials.</span>
          </h1>
          <p className="text-slate-300 max-w-2xl mx-auto text-sm md:text-base leading-relaxed">
            Execute mission-critical tasks for NGOs and receive Immutable Blockchain Volunteer Certificates!
          </p>
        </div>
      </section>

      {/* Main Container */}
      <div className="max-w-6xl mx-auto px-4 -mt-6 relative z-20">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden mb-8">
          <Tabs defaultValue="browse" className="w-full">
            <TabsList
              variant="plain"
              className="w-full justify-start items-center border-b border-slate-200 bg-slate-50/60 px-2 py-0 gap-0"
            >
              <TabsTrigger value="browse" className={triggerClass}>
                <span>Browse Opportunities</span>
              </TabsTrigger>
              <TabsTrigger value="applications" className={triggerClass}>
                <span>My Applications ({myApplications.length})</span>
              </TabsTrigger>
              <TabsTrigger value="credentials" className={triggerClass}>
                <span>Verified Credentials ({myCredentials.length})</span>
              </TabsTrigger>
            </TabsList>

            {/* TAB 1: BROWSE OPPORTUNITIES */}
            <TabsContent value="browse" className="p-6 space-y-6 m-0">
              {/* Search & Filter Bar */}
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-grow">
                  <Search className="absolute left-3.5 inset-y-0 my-auto text-slate-400 h-4 w-4" />
                  <Input
                    type="text"
                    placeholder="Search roles by skill, title, location..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 text-sm bg-slate-50"
                  />
                </div>

                <div className="flex gap-2">
                  {["All", "open", "trained_only"].map((tier) => (
                    <button
                      key={tier}
                      type="button"
                      onClick={() => setSelectedTier(tier)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize border transition-all ${
                        selectedTier === tier
                          ? "bg-emerald-600 border-emerald-600 text-white shadow-sm"
                          : "bg-white border-slate-200 text-slate-700 hover:bg-slate-50"
                      }`}
                    >
                      {tier === "All" ? "All Safety Tiers" : tier.replace("_", " ")}
                    </button>
                  ))}
                </div>
              </div>

              {/* Opportunities Grid */}
              {isLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[1, 2, 3, 4].map((i) => (
                    <div key={i} className="h-48 bg-slate-100 animate-pulse rounded-xl" />
                  ))}
                </div>
              ) : filteredOpportunities.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {filteredOpportunities.map((opp) => (
                    <Card key={opp.id} className="border border-slate-200 shadow-sm rounded-xl hover:shadow-md transition-all flex flex-col justify-between">
                      <CardHeader className="pb-2">
                        <div className="flex justify-between items-start mb-1">
                          <Badge 
                            variant="outline" 
                            className={`text-[10px] uppercase font-semibold ${
                              opp.safety_tier === "open"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : opp.safety_tier === "trained_only"
                                ? "bg-amber-50 text-amber-700 border-amber-200"
                                : "bg-red-50 text-red-700 border-red-200"
                            }`}
                          >
                            {opp.safety_tier.replace("_", " ")}
                          </Badge>

                          <span className="text-xs text-slate-500 capitalize">
                            {opp.location_type.replace("_", " ")}
                          </span>
                        </div>

                        <CardTitle className="text-lg font-bold text-slate-900">{opp.title}</CardTitle>
                        <p className="text-xs text-slate-500 font-medium">
                          for {opp.campaign_title || "Verified Campaign"}
                        </p>
                      </CardHeader>

                      <CardContent className="space-y-4 pt-1">
                        <p className="text-xs text-slate-600 line-clamp-2">{opp.description}</p>

                        <div className="flex flex-wrap gap-4 text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                          <div className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5 text-slate-400" />
                            <span>{opp.estimated_hours} hrs needed</span>
                          </div>
                          <div className="flex items-center gap-1">
                            <Users className="w-3.5 h-3.5 text-slate-400" />
                            <span>{opp.spots_available} spots open</span>
                          </div>
                          {opp.location_city && (
                            <div className="flex items-center gap-1">
                              <MapPin className="w-3.5 h-3.5 text-slate-400" />
                              <span>{opp.location_city}</span>
                            </div>
                          )}
                        </div>

                        <Button
                          onClick={() => {
                            setSelectedOpp(opp);
                            setApplySuccess(false);
                            setApplyError(null);
                          }}
                          className="w-full bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-2 rounded-lg"
                        >
                          Apply for Assignment
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500 text-sm">
                  No volunteer opportunities match your filter.
                </div>
              )}
            </TabsContent>

            {/* TAB 2: MY APPLICATIONS */}
            <TabsContent value="applications" className="p-6 space-y-4 m-0">
              <h3 className="text-lg font-bold text-slate-900">Your Volunteer Applications</h3>
              {myApplications.length > 0 ? (
                <div className="space-y-3">
                  {myApplications.map((app) => (
                    <div key={app.id} className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="font-bold text-sm text-slate-900">{app.opportunity_title || "Volunteer Assignment"}</h4>
                          <Badge 
                            variant="outline" 
                            className={`text-[10px] uppercase font-semibold ${
                              app.status === "completed"
                                ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                                : app.status === "approved"
                                ? "bg-blue-100 text-blue-800 border-blue-300"
                                : "bg-slate-200 text-slate-700"
                            }`}
                          >
                            {app.status}
                          </Badge>
                        </div>
                        <p className="text-xs text-slate-500 mt-1">
                          Campaign: {app.campaign_title || "General"} | Hours logged: {app.hours_logged} hrs
                        </p>
                      </div>

                      {app.credential_issued && (
                        <Badge className="bg-purple-600 text-white text-xs gap-1 py-1">
                          <Award className="w-3.5 h-3.5" /> Credential Claimed
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-slate-50 rounded-xl border border-slate-200 text-slate-500 text-sm">
                  You have not applied for any volunteer roles yet. Explore opportunities in the first tab!
                </div>
              )}
            </TabsContent>

            {/* TAB 3: VERIFIED CREDENTIALS */}
            <TabsContent value="credentials" className="p-6 space-y-4 m-0">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-slate-900">On-Chain Volunteer Credentials</h3>
                  <p className="text-xs text-slate-500">Cryptographically issued & verifiable on Polygon Amoy.</p>
                </div>
                <Badge variant="outline" className="text-purple-700 border-purple-300 bg-purple-50 text-xs">
                  <Cpu className="w-3.5 h-3.5 mr-1" /> ERC-721 Proof
                </Badge>
              </div>

              {myCredentials.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {myCredentials.map((cred) => (
                    <div key={cred.id} className="p-5 bg-gradient-to-br from-slate-900 to-slate-950 text-white rounded-xl border border-purple-900/40 shadow-sm space-y-3">
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2">
                          <div className="w-9 h-9 bg-purple-500/20 text-purple-400 rounded-lg flex items-center justify-center">
                            <Award className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="font-bold text-sm text-white">{cred.volunteer_name}</div>
                            <div className="text-[11px] text-purple-300">{cred.campaign_title || "Eleos Verified Work"}</div>
                          </div>
                        </div>
                        <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/40 text-[10px]">
                          {cred.hours_served} Hours Verified
                        </Badge>
                      </div>

                      {cred.blockchain_tx_hash && (
                        <div className="pt-2 border-t border-slate-800">
                          <div className="text-[10px] text-slate-400 mb-1">Polygon Amoy Proof:</div>
                          <a
                            href={`https://amoy.polygonscan.com/tx/${cred.blockchain_tx_hash}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[11px] font-mono text-purple-400 hover:text-purple-300 underline break-all flex items-center gap-1"
                          >
                            <span>{cred.blockchain_tx_hash.slice(0, 24)}...</span>
                            <ExternalLink className="w-3 h-3 shrink-0" />
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-slate-50 rounded-xl border border-slate-200 text-slate-500 text-sm">
                  Complete volunteer assignments to receive immutable on-chain impact credentials.
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Application Modal */}
      {selectedOpp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
            <div className="bg-slate-900 text-white p-5 relative">
              <button
                onClick={() => setSelectedOpp(null)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
              <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/40 text-[10px] mb-2">
                APPLICATION
              </Badge>
              <h3 className="text-lg font-bold line-clamp-1">{selectedOpp.title}</h3>
              <p className="text-xs text-slate-400 mt-0.5">Campaign: {selectedOpp.campaign_title || "Verified Campaign"}</p>
            </div>

            <div className="p-6">
              {applySuccess ? (
                <div className="text-center py-4 space-y-3">
                  <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                    <CheckCircle2 className="w-8 h-8" />
                  </div>
                  <h4 className="text-lg font-bold text-slate-900">Application Submitted!</h4>
                  <p className="text-xs text-slate-600">
                    The NGO team will review your application. You will be notified once assigned.
                  </p>
                  <Button onClick={() => setSelectedOpp(null)} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white mt-2">
                    Done
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleApplySubmit} className="space-y-4">
                  {applyError && (
                    <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-lg">
                      {applyError}
                    </div>
                  )}

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                      Committed Hours
                    </label>
                    <Input
                      type="number"
                      value={hoursCommitted}
                      onChange={(e) => setHoursCommitted(parseInt(e.target.value) || 0)}
                      min="1"
                      className="text-sm"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 uppercase mb-1">
                      Message / Relevant Experience
                    </label>
                    <textarea
                      value={appMessage}
                      onChange={(e) => setAppMessage(e.target.value)}
                      placeholder="Share your background or why you want to support this cause..."
                      rows={3}
                      className="w-full p-2.5 text-xs rounded-lg border border-slate-300 focus:ring-emerald-500 focus:border-emerald-500"
                    />
                  </div>

                  <Button
                    type="submit"
                    disabled={isApplying}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-xl gap-2 text-sm"
                  >
                    {isApplying ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Submitting...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-4 h-4" />
                        <span>Confirm & Submit Application</span>
                      </>
                    )}
                  </Button>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
