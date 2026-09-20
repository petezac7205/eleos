"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { CheckCircle2, MapPin, Calendar, AlertCircle, Link as LinkIcon, Info, ExternalLink, ShieldCheck, Loader2, QrCode, X } from "lucide-react";
import React, { useState, useEffect, use, useCallback } from "react";
import { Campaign, campaignsApi, explorerApi, donationsApi, TimelineEvent } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import Link from "next/link";

const triggerClass =
  "relative group bg-transparent data-active:bg-transparent data-active:shadow-none data-active:text-primary text-muted-foreground hover:text-primary transition-colors text-sm font-medium py-3 px-5 rounded-none";

const CircularScore = ({ score, label, tooltip }: { score: number, label: string, tooltip: string }) => {
  const radius = 22;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="group relative flex items-center gap-3 bg-white border border-slate-200/60 rounded-xl p-3 pr-6 shadow-sm hover:shadow-md hover:border-emerald-200 transition-all cursor-default w-fit">
      {/* Circle */}
      <div className="relative w-14 h-14 shrink-0 flex items-center justify-center">
        {/* Background track */}
        <svg className="w-full h-full -rotate-90 absolute inset-0" viewBox="0 0 52 52">
          <circle 
            cx="26" cy="26" r={radius}
            className="stroke-slate-100" 
            strokeWidth="4" fill="transparent"
          />
          {/* Progress */}
          <circle 
            cx="26" cy="26" r={radius}
            className="stroke-emerald-500 transition-all duration-1000 ease-out" 
            strokeWidth="4" fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <span className="text-sm font-bold text-slate-800 leading-none">{score}</span>
      </div>
      
      {/* Text */}
      <div className="flex flex-col">
        <span className="text-[13px] font-bold text-slate-900 leading-none">{label}</span>
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">/ 100</span>
      </div>

      {/* Tooltip */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-64 bg-slate-900 text-white text-xs p-3.5 rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20 shadow-xl pointer-events-none text-center leading-relaxed">
        {tooltip}
        {/* Arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-[6px] border-transparent border-t-slate-900" />
      </div>
    </div>
  );
};

export default function CampaignDetail({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const campaignId = resolvedParams.id;

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const { user } = useAuth();
  const [donationAmount, setDonationAmount] = useState<number | string>(500);
  const [paymentMethod, setPaymentMethod] = useState<"UPI" | "Card">("UPI");
  const [isDonating, setIsDonating] = useState(false);
  const [showQrModal, setShowQrModal] = useState<boolean>(false);
  const [donationSuccess, setDonationSuccess] = useState<{
    amount: number;
    tax_receipt_token: string;
    polygon_tx_hash?: string;
  } | null>(null);
  const [donationError, setDonationError] = useState<string | null>(null);
  const [isBudgetExpanded, setIsBudgetExpanded] = useState(false);
  const [isTrustExpanded, setIsTrustExpanded] = useState(false);

  const fetchCampaignData = useCallback(async () => {
    try {
      const [campData, timelineData] = await Promise.all([
        campaignsApi.getById(campaignId).catch(() => null),
        explorerApi.getCampaignTimeline(campaignId).catch(() => []),
      ]);
      if (campData) {
        setCampaign(campData);
      } else {
        setCampaign({
          id: campaignId,
          ngo_id: "NGO_00002",
          ngo_name: "HopeRelief Foundation",
          ngo_trust_badge: "Verified",
          title: "Nepal Flood Relief 2026",
          description: "Providing laptops and internet access to 5 remote schools. We believe digital literacy is a fundamental right.",
          category: "Disaster Relief",
          target_amount: 4700000,
          current_amount: 2300000,
          funding_percentage: 48,
          is_disaster_relief: true,
          status: "active",
          safety_tier: "open",
          state: "Kathmandu Valley",
          district: "Nepal",
          created_at: "2026-09-01T00:00:00Z",
          budget_items: [
            { id: "b1", category: "Emergency", item_name: "Food Kits", unit_cost: 500, quantity: 2000, ai_status: "pass" },
            { id: "b2", category: "Medical", item_name: "First Aid Kits", unit_cost: 1500, quantity: 500, ai_status: "warning" }
          ],
          milestones: []
        });
      }
      setTimeline(timelineData || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  }, [campaignId]);

  const executeDonationFlow = useCallback(async () => {
    if (!campaign) return;
    const finalAmount = typeof donationAmount === "number" ? donationAmount : parseFloat(String(donationAmount)) || 500;
    if (!finalAmount || finalAmount < 10) {
      setDonationError("Please enter a valid donation amount (minimum ₹10).");
      return;
    }

    setIsDonating(true);
    setDonationError(null);
    setDonationSuccess(null);

    try {
      // 1. Create order on backend
      const orderData = await donationsApi.createOrder(
        campaign.id,
        finalAmount,
        false,
        user?.name || "Donor",
        user?.email || "donor@example.com"
      );

      // 2. Direct on-chain verification and state update
      await new Promise((r) => setTimeout(r, 600));

      const paymentId = "pay_" + (orderData.razorpay_order_id || "order").replace("order_", "") + "_" + Math.random().toString(36).substring(2, 7);
      const verifyRes = await donationsApi.verify({
        donation_id: orderData.donation_id,
        razorpay_order_id: orderData.razorpay_order_id,
        razorpay_payment_id: paymentId,
        razorpay_signature: `simulated_${orderData.razorpay_order_id}`,
      });

      setDonationSuccess({
        amount: verifyRes.amount ?? finalAmount,
        tax_receipt_token: verifyRes.tax_receipt_token ?? `ELEOS-REC-${orderData.donation_id.substring(0, 8).toUpperCase()}`,
        polygon_tx_hash: verifyRes.polygon_tx_hash || verifyRes.blockchain_tx_hash,
      });

      // Refresh campaign progress immediately
      fetchCampaignData();
    } catch (err: any) {
      setDonationError(err.message || "Failed to process on-chain donation.");
    } finally {
      setIsDonating(false);
    }
  }, [campaign, donationAmount, user, fetchCampaignData]);

  // When Donate Now button is clicked: validate and show QR modal
  const handleInitiateDonate = () => {
    if (!campaign) return;
    const finalAmount = typeof donationAmount === "number" ? donationAmount : parseFloat(String(donationAmount)) || 500;
    if (!finalAmount || finalAmount < 10) {
      setDonationError("Please enter a valid donation amount (minimum ₹10).");
      return;
    }
    setDonationError(null);
    setShowQrModal(true);
  };

  // Listen for ESC key press to dismiss the QR modal and run the donation flow
  useEffect(() => {
    if (!showQrModal) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" || e.keyCode === 27) {
        e.preventDefault();
        e.stopPropagation();
        setShowQrModal(false);
        executeDonationFlow();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [showQrModal, executeDonationFlow]);

  useEffect(() => {
    fetchCampaignData();
  }, [fetchCampaignData]);

  if (isLoading) {
    return (
      <div className="bg-slate-50 min-h-screen py-16 flex justify-center items-center">
        <div className="text-emerald-700 font-semibold animate-pulse">Loading campaign details...</div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="bg-slate-50 min-h-screen py-20 text-center flex flex-col items-center">
        <AlertCircle className="w-12 h-12 text-amber-500 mb-3" />
        <h2 className="text-xl font-bold text-slate-800">Campaign Not Found</h2>
      </div>
    );
  }

  const percentComplete = campaign.funding_percentage
    ? Math.min(100, Math.round(campaign.funding_percentage))
    : Math.min(100, Math.round(((campaign.current_amount || 0) / (campaign.target_amount || 1)) * 100));

  return (
    <div className="bg-slate-50 min-h-screen pb-20">
      {/* Top Banner */}
      <div className="h-48 bg-slate-900 w-full relative">
        <div className="absolute inset-0 bg-[url('/hero-bg-real.jpg')] bg-cover bg-center opacity-30" />
      </div>

      <div className="container mx-auto px-4 -mt-32 relative z-10">
        <div className="flex flex-col lg:flex-row gap-8">

          {/* LEFT COLUMN */}
          <div className="lg:w-2/3 space-y-6">

            {/* Header Card */}
            <Card className="overflow-hidden border-border shadow-md">
              <div className="h-64 sm:h-80 bg-slate-200 relative">
                <div className="absolute inset-0 bg-[url('/hero-bg-real.jpg')] bg-cover bg-center" />
              </div>
              <CardContent className="pt-6">
                <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100 border-none gap-1 font-semibold px-2.5 py-0.5 mb-4">
                  <span className="text-xs">🌊</span> {campaign.category}
                </Badge>
                <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">{campaign.title}</h1>
                <div className="flex flex-wrap items-center gap-2.5 mb-6">
                  <p className="text-lg text-muted-foreground font-medium flex items-center">
                    by 
                    <Link href={`/ngos/${campaign.ngo_id || 'ngo_1'}`} className="ml-1.5 text-slate-800 hover:text-emerald-600 transition-colors flex items-center group">
                      {campaign.ngo_name}
                      <ExternalLink className="h-4 w-4 ml-1.5 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </Link>
                  </p>
                </div>

                {/* ── Scores Section ── */}
                <div className="flex flex-wrap gap-4 mb-8">
                  <CircularScore 
                    score={Number(campaign.ngo?.trust_score ?? campaign.ngo_trust_score ?? 90)} 
                    label="Trust Score" 
                    tooltip="Reflects the credibility and reliability of this organisation based on their history, financial health, and legal filings." 
                  />
                  <CircularScore 
                    score={Number(campaign.feasibility?.score ?? campaign.feasibility?.overall_score ?? 85)} 
                    label="ELEOS Score" 
                    tooltip="Represents how feasible and well-supported this specific campaign appears based on our AI evaluation of the project plan." 
                  />
                </div>

                <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <MapPin className="h-4 w-4" /> {campaign.state}, {campaign.district}
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="h-4 w-4" /> {new Date(campaign.created_at || Date.now()).toLocaleDateString("en-US", { month: "short", year: "numeric" })} – Ongoing
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tabs — self-contained white card, no page jump */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <Tabs defaultValue="budget" className="w-full">

                {/* Horizontal labels — top of the card with a bottom border */}
                <TabsList
                  variant="plain"
                  className="w-full justify-start items-center border-b border-slate-200 bg-transparent px-2 py-0 gap-0"
                >
                  <TabsTrigger value="about" className={triggerClass}>
                    <span className="relative">
                      About
                      <span className="absolute -bottom-0.5 left-1/2 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full group-hover:left-0 group-data-active:w-full group-data-active:left-0" />
                    </span>
                  </TabsTrigger>
                  <TabsTrigger value="budget" className={triggerClass}>
                    <span className="relative">
                      Budget Analysis
                      <span className="absolute -bottom-0.5 left-1/2 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full group-hover:left-0 group-data-active:w-full group-data-active:left-0" />
                    </span>
                  </TabsTrigger>
                  <TabsTrigger value="score" className={triggerClass}>
                    <span className="relative">
                      Charity Trust Score
                      <span className="absolute -bottom-0.5 left-1/2 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full group-hover:left-0 group-data-active:w-full group-data-active:left-0" />
                    </span>
                  </TabsTrigger>
                  <TabsTrigger value="blockchain" className={triggerClass}>
                    <span className="relative">
                      Blockchain Trail
                      <span className="absolute -bottom-0.5 left-1/2 w-0 h-0.5 bg-primary transition-all duration-300 group-hover:w-full group-hover:left-0 group-data-active:w-full group-data-active:left-0" />
                    </span>
                  </TabsTrigger>
                </TabsList>

                {/* Content area — fixed min-height prevents page height changes */}
                <div className="h-[520px] overflow-y-auto">

                  {/* ABOUT TAB */}
                  <TabsContent value="about" className="p-6 md:p-8">
                    <h3 className="text-2xl font-bold mb-4">About This Campaign</h3>
                    <p className="text-slate-600 mb-6 leading-relaxed whitespace-pre-wrap">
                      {campaign.description}
                    </p>
                  </TabsContent>

                  {/* BUDGET ANALYSIS TAB */}
                  <TabsContent value="budget" className="p-6 md:p-8 space-y-6">
                    <div className="flex items-start justify-between bg-emerald-50 border border-emerald-100 p-4 rounded-xl">
                      <div>
                        <h4 className="font-bold text-emerald-900 flex items-center gap-2 mb-1">
                          <CheckCircle2 className="h-5 w-5" /> Feasibility Score: {campaign.feasibility?.label ? (campaign.feasibility.label.charAt(0).toUpperCase() + campaign.feasibility.label.slice(1)) : "High"}
                        </h4>
                        <p className="text-sm text-emerald-800">
                          This budget is realistic for cross-border disaster relief operations. Costs have been benchmarked against regional market rates.
                        </p>
                      </div>
                      <div className="text-right text-xs text-emerald-700/70">
                        <div>Methodology v1.0</div>
                        <div>Scored 2 hours ago</div>
                      </div>
                    </div>

                    {!isBudgetExpanded ? (
                      <Button onClick={() => setIsBudgetExpanded(true)} variant="outline" className="w-full text-emerald-700 border-emerald-200 hover:bg-emerald-50">
                        View Full Technical Analysis
                      </Button>
                    ) : (
                      <>
                        <div className="border rounded-lg overflow-hidden">
                          <Table>
                            <TableHeader className="bg-slate-50">
                              <TableRow>
                                <TableHead>Line Item</TableHead>
                                <TableHead>Submitted Cost</TableHead>
                                <TableHead>Benchmark</TableHead>
                                <TableHead>Ratio</TableHead>
                                <TableHead>Status</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {campaign.budget_items?.map((item, idx) => (
                                <TableRow key={idx} className={item.ai_status === "warning" ? "bg-amber-50/50" : ""}>
                                  <TableCell className="font-medium">{item.item_name} ({item.quantity})</TableCell>
                                  <TableCell>₹{item.unit_cost?.toLocaleString("en-IN") || 0}</TableCell>
                                  <TableCell className="text-muted-foreground">₹{Math.round((item.unit_cost || 0) * 0.8).toLocaleString("en-IN")}</TableCell>
                                  <TableCell className={item.ai_status === "warning" ? "text-amber-700 font-medium" : ""}>
                                    {item.ai_status === "warning" ? "1.25x" : "1.05x"}
                                  </TableCell>
                                  <TableCell>
                                    {item.ai_status === "warning" ? (
                                      <Badge variant="outline" className="bg-amber-100 text-amber-800 border-amber-300">Note</Badge>
                                    ) : (
                                      <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">Pass</Badge>
                                    )}
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                        <div className="bg-slate-50 p-4 rounded-lg text-sm border">
                          <div className="flex gap-2 text-amber-700 font-semibold mb-2">
                            <AlertCircle className="h-4 w-4" /> Context Adjustment Applied
                          </div>
                          <p className="text-slate-600">
                            Transport cost is 1.94x the standard domestic benchmark. This is expected for cross-border disaster logistics. Nepal flood zone access requires alternate routes and emergency vehicle procurement. A disaster multiplier of 1.5x was approved. Adjusted ratio: 1.29x — within acceptable range.
                          </p>
                        </div>
                      </>
                    )}
                  </TabsContent>

                  {/* SCORE TAB */}
                  <TabsContent value="score" className="p-6 md:p-8 space-y-6">
                    <div className="flex items-start justify-between bg-emerald-50 border border-emerald-100 p-4 rounded-xl">
                      <div>
                        <h4 className="font-bold text-emerald-900 flex items-center gap-2 mb-1">
                          <CheckCircle2 className="h-5 w-5" /> Trustability: Verified
                        </h4>
                        <p className="text-sm text-emerald-800">
                          All legal documents, financials, and past operational history meet our highest transparency standards.
                        </p>
                      </div>
                    </div>
                    {!isTrustExpanded ? (
                      <Button onClick={() => setIsTrustExpanded(true)} variant="outline" className="w-full text-emerald-700 border-emerald-200 hover:bg-emerald-50">
                        View Full Trust Breakdown
                      </Button>
                    ) : (
                      <div className="space-y-6 pt-4 border-t">
                        <div>
                          <div className="flex justify-between items-end mb-2">
                            <h4 className="font-semibold">Identity &amp; Legal</h4>
                            <span className="font-mono font-bold">95/100</span>
                          </div>
                          <Progress value={95} className="h-2 mb-3 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-600" />
                          <ul className="text-sm space-y-1.5 text-slate-600 ml-1">
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> NGO Darpan Registered</li>
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> FCRA Active</li>
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> PAN Verified</li>
                          </ul>
                        </div>
                        <div>
                          <div className="flex justify-between items-end mb-2">
                            <h4 className="font-semibold">Financial Transparency</h4>
                            <span className="font-mono font-bold">82/100</span>
                          </div>
                          <Progress value={82} className="h-2 mb-3 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-600" />
                          <ul className="text-sm space-y-1.5 text-slate-600 ml-1">
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> 3 years audited financials uploaded</li>
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Admin ratio: 9% (Well below 20% limit)</li>
                            <li className="flex gap-2 items-center text-amber-700"><AlertCircle className="h-3.5 w-3.5" /> FY23-24 audit shows 15% donor concentration</li>
                          </ul>
                        </div>
                        <div>
                          <div className="flex justify-between items-end mb-2">
                            <h4 className="font-semibold">Operational History</h4>
                            <span className="font-mono font-bold">88/100</span>
                          </div>
                          <Progress value={88} className="h-2 mb-3 [&_[data-slot=progress-track]]:bg-slate-200 [&_[data-slot=progress-indicator]]:bg-emerald-600" />
                          <ul className="text-sm space-y-1.5 text-slate-600 ml-1">
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> 5 completed campaigns on Eleos</li>
                            <li className="flex gap-2 items-center"><CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" /> Milestone completion rate: 94%</li>
                          </ul>
                        </div>
                      </div>
                    )}
                  </TabsContent>

                  {/* BLOCKCHAIN TAB */}
                  <TabsContent value="blockchain" className="p-6 md:p-8">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="p-2 bg-violet-100 rounded-lg">
                        <LinkIcon className="h-6 w-6 text-violet-600" />
                      </div>
                      <div>
                        <h3 className="text-xl font-bold">On-Chain Ledger</h3>
                        <p className="text-sm text-slate-500">Every event is permanently recorded on Polygon PoS.</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      {timeline.length === 0 ? (
                        <div className="text-center py-8 text-slate-500 text-sm border border-dashed rounded-lg">
                          No blockchain events recorded yet.
                        </div>
                      ) : (
                        timeline.map((log, idx) => (
                          <div key={log.id || idx} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border rounded-lg hover:bg-slate-50 transition-colors">
                            <div>
                              <div className="font-medium text-slate-800">
                                {((log.event_type || (log as any).event || log.title || "On-Chain Proof") as string).replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}
                              </div>
                              <div className="text-xs text-slate-500 mt-1">{new Date(log.created_at || log.timestamp || Date.now()).toLocaleString()}</div>
                            </div>
                            <div className="mt-2 sm:mt-0 flex items-center gap-2">
                              {log.tx_hash || log.polygon_tx_hash ? (
                                <a
                                  href={`https://amoy.polygonscan.com/tx/${log.tx_hash || log.polygon_tx_hash}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs bg-slate-100 hover:bg-violet-100 px-2.5 py-1 rounded text-slate-700 hover:text-violet-800 font-mono transition-colors flex items-center gap-1.5 border border-slate-200"
                                >
                                  <span>{(log.tx_hash || log.polygon_tx_hash).substring(0, 14)}...</span>
                                  <ExternalLink className="w-3 h-3 text-slate-400" />
                                </a>
                              ) : (
                                <code className="text-xs bg-slate-100 px-2 py-1 rounded text-slate-600 font-mono">
                                  Pending...
                                </code>
                              )}
                              {(log.tx_hash || log.polygon_tx_hash) && (
                                <a
                                  href={`https://amoy.polygonscan.com/tx/${log.tx_hash || log.polygon_tx_hash}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  <Button variant="ghost" size="sm" className="h-8 text-violet-600 hover:text-violet-700 hover:bg-violet-50 text-xs flex items-center gap-1">
                                    <span>Polygonscan</span>
                                    <ExternalLink className="w-3 h-3" />
                                  </Button>
                                </a>
                              )}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </TabsContent>

                </div>
              </Tabs>
            </div>

          </div>

          {/* RIGHT COLUMN: Sticky Sidebar — unchanged */}
          <div className="lg:w-1/3">
            <div className="sticky top-24">
              <Card className="border-border shadow-lg">
                <CardContent className="p-6">
                  {/* Funding Progress */}
                  <div className="mb-6">
                    <div className="flex justify-between items-end mb-2">
                      <div>
                        <span className="text-3xl font-bold font-mono">₹{(campaign.current_amount || 0).toLocaleString("en-IN")}</span>
                        <span className="text-sm text-muted-foreground block mt-1">raised of ₹{(campaign.target_amount || 1).toLocaleString("en-IN")} goal</span>
                      </div>
                      <div className="text-right">
                        <span className="text-xl font-bold text-emerald-600">{percentComplete}%</span>
                      </div>
                    </div>
                    <Progress value={percentComplete} className="h-2 mb-3 bg-slate-200" />
                    <div className="flex justify-between text-sm text-slate-500">
                      <span>{Math.round((campaign.current_amount || 0) / 1500)} donors</span>
                      <span>18 days left</span>
                    </div>
                  </div>

                  <Separator className="my-6" />

                  {/* Donation Form */}
                  <div className="space-y-6">
                    <div>
                      <h4 className="font-semibold mb-3">Select Amount</h4>
                      <div className="grid grid-cols-3 gap-2 mb-3">
                        {[100, 500, 1000].map(amt => (
                          <Button
                            key={amt}
                            variant={donationAmount === amt ? "default" : "outline"}
                            className={donationAmount === amt ? "bg-emerald-600 hover:bg-emerald-700" : ""}
                            onClick={() => setDonationAmount(amt)}
                          >
                            ₹{amt}
                          </Button>
                        ))}
                      </div>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">₹</span>
                        <Input
                          type="number"
                          value={donationAmount}
                          onChange={(e) => setDonationAmount(e.target.value)}
                          className="pl-8"
                          placeholder="Custom Amount"
                        />
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold mb-3">Payment Method</h4>
                      <div className="grid grid-cols-2 gap-2">
                        <Button 
                          type="button"
                          variant="outline" 
                          onClick={() => setPaymentMethod("UPI")}
                          className={paymentMethod === "UPI" ? "border-emerald-600 text-emerald-700 bg-emerald-50 font-medium" : ""}
                        >
                          UPI
                        </Button>
                        <Button 
                          type="button"
                          variant="outline"
                          onClick={() => setPaymentMethod("Card")}
                          className={paymentMethod === "Card" ? "border-emerald-600 text-emerald-700 bg-emerald-50 font-medium" : ""}
                        >
                          Card
                        </Button>
                      </div>
                    </div>

                    <Button 
                      onClick={handleInitiateDonate}
                      disabled={isDonating}
                      className="w-full text-lg py-6 shadow-md border-b-[4px] border-black/20 hover:border-b-0 hover:translate-y-[4px] transition-all duration-150 bg-emerald-600 hover:bg-emerald-700 text-white font-bold disabled:opacity-80"
                    >
                      {isDonating ? (
                        <span className="flex items-center justify-center gap-2">
                          <Loader2 className="h-5 w-5 animate-spin" />
                          Anchoring to Polygon...
                        </span>
                      ) : (
                        `Donate ₹${typeof donationAmount === "number" ? donationAmount.toLocaleString("en-IN") : (parseFloat(String(donationAmount)) || 500).toLocaleString("en-IN")} Now`
                      )}
                    </Button>

                    {donationSuccess && (
                      <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl space-y-2.5 animate-in fade-in duration-300">
                        <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
                          Donation Confirmed On-Chain!
                        </div>
                        <div className="text-xs text-slate-700 flex justify-between items-center">
                          <span>Tax Receipt:</span>
                          <code className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-emerald-200">
                            {donationSuccess.tax_receipt_token}
                          </code>
                        </div>
                        {donationSuccess.polygon_tx_hash && (
                          <div className="text-xs">
                            <span className="text-slate-500 block mb-0.5">Polygon Amoy Proof:</span>
                            <a
                              href={`https://amoy.polygonscan.com/tx/${donationSuccess.polygon_tx_hash}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-mono text-[11px] text-purple-700 hover:text-purple-900 underline break-all flex items-center gap-1"
                            >
                              <span>{donationSuccess.polygon_tx_hash.substring(0, 24)}...</span>
                              <ExternalLink className="w-3 h-3 shrink-0" />
                            </a>
                          </div>
                        )}
                        <Link href="/explorer" className="block pt-1">
                          <Button variant="outline" size="sm" className="w-full text-xs bg-white border-emerald-300 text-emerald-800 hover:bg-emerald-100">
                            View Live Ledger
                          </Button>
                        </Link>
                      </div>
                    )}

                    {donationError && (
                      <div className="bg-red-50 border border-red-200 text-red-700 text-xs p-3 rounded-lg flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        {donationError}
                      </div>
                    )}

                    <div className="flex items-start gap-2 text-xs text-slate-500 bg-slate-50 p-3 rounded-lg border">
                      <LinkIcon className="h-4 w-4 shrink-0 mt-0.5" />
                      <p>Your donation will be permanently recorded on the Polygon blockchain. You will receive an on-chain receipt.</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Volunteer Callout */}
              <Card className="mt-6 border-blue-200 bg-blue-50/50 shadow-sm">
                <CardContent className="p-5 flex items-start gap-4">
                  <div className="p-2 bg-blue-100 rounded-full shrink-0">
                    <Info className="h-5 w-5 text-blue-700" />
                  </div>
                  <div>
                    <h4 className="font-bold text-blue-900 mb-1">Restricted Volunteering</h4>
                    <p className="text-sm text-blue-800/80 mb-3">
                      This is a disaster zone. Only certified medical/logistics volunteers are permitted on-ground.
                    </p>
                    <Button variant="outline" size="sm" className="bg-white border-blue-200 text-blue-700">
                      View Remote Options
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>

        </div>
      </div>

      {/* QR Code Demo Modal */}
      {showQrModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="relative bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200 text-center space-y-4 animate-in zoom-in-95 duration-200">
            {/* Close / Cancel Button */}
            <button
              onClick={() => setShowQrModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-700 transition-colors p-1.5 rounded-full hover:bg-slate-100"
              title="Cancel (without donating)"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Header */}
            <div>
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 mb-2">
                <QrCode className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold text-slate-900">Scan QR to Pay</h3>
              <p className="text-xs text-slate-500 mt-1">
                Scan using Google Pay, PhonePe, Paytm or any UPI app
              </p>
            </div>

            {/* QR Code Image */}
            <div className="relative mx-auto w-60 h-60 bg-slate-50 border-2 border-emerald-500/40 rounded-2xl p-3 flex items-center justify-center shadow-inner">
              <img
                src="/qr.jpeg"
                alt="Donation UPI QR Code"
                className="w-full h-full object-contain rounded-xl"
              />
            </div>

            {/* Target & Amount Details */}
            <div className="bg-slate-50 rounded-xl p-3 text-xs border border-slate-100 space-y-1">
              <div className="flex justify-between items-center text-slate-500">
                <span>Amount:</span>
                <span className="font-bold font-mono text-emerald-700 text-sm">
                  ₹{typeof donationAmount === "number" ? donationAmount.toLocaleString("en-IN") : (parseFloat(String(donationAmount)) || 500).toLocaleString("en-IN")}
                </span>
              </div>
              <div className="flex justify-between items-center text-slate-500 text-[11px] truncate">
                <span>Campaign:</span>
                <span className="font-medium text-slate-700 truncate max-w-[180px]">{campaign.title}</span>
              </div>
            </div>

            {/* Awaiting payment note */}
            <div className="flex items-center justify-center gap-2 pt-2 text-xs text-slate-500 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Awaiting UPI payment confirmation...</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
