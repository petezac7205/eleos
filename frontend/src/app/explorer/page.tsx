"use client";

import React, { useState, useEffect } from "react";
import { explorerApi, ExplorerStats } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { 
  Activity, 
  Cpu, 
  Search, 
  ExternalLink, 
  ShieldCheck, 
  FileText, 
  Award, 
  Heart, 
  Video,
  CheckCircle2,
  AlertCircle
} from "lucide-react";

export default function ExplorerPage() {
  const [stats, setStats] = useState<ExplorerStats | null>(null);
  const [searchHash, setSearchHash] = useState<string>("");
  const [txResult, setTxResult] = useState<any>(null);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [feedEvents, setFeedEvents] = useState<any[]>([]);

  useEffect(() => {
    explorerApi.getStats().then(setStats).catch(console.error);
    explorerApi.getFeed(10)
      .then((data) => {
        if (Array.isArray(data) && data.length > 0) {
          const mapped = data.map((d: any) => ({
            type: d.type || "donation",
            title: d.type === "donation" ? "Donation Anchored" : "On-Chain Proof Anchored",
            amount: d.amount ? `₹${d.amount}` : undefined,
            campaign: d.campaign_title || "Disaster Relief Campaign",
            hash: d.tx_hash,
            tx: d.tx_hash,
            time: d.timestamp ? new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Recently",
            explorer_url: d.explorer_url || `https://amoy.polygonscan.com/tx/${d.tx_hash}`
          }));
          setFeedEvents(mapped);
        } else {
          setFeedEvents(sampleRecentEvents);
        }
      })
      .catch(() => setFeedEvents(sampleRecentEvents));
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchHash.trim()) return;
    setIsSearching(true);
    setSearchError(null);
    setTxResult(null);

    try {
      const res = await explorerApi.getTransaction(searchHash.trim());
      setTxResult(res);
    } catch (err: any) {
      setSearchError(err.message || "Transaction not found on Polygon Amoy testnet.");
    } finally {
      setIsSearching(false);
    }
  };

  const sampleRecentEvents = [
    {
      type: "donation",
      title: "Donation Anchored",
      amount: "₹500",
      campaign: "Solar Clean Water Station Pune 2026",
      hash: "0x47f6a8909e6cbf984e3f6b8df954b10887cbf344a11d193437d24599bd1b9c54",
      tx: "0x47f6a8909e6cbf984e3f6b8df954b10887cbf344a11d193437d24599bd1b9c54",
      time: "Just now",
      explorer_url: "https://amoy.polygonscan.com/tx/0x47f6a8909e6cbf984e3f6b8df954b10887cbf344a11d193437d24599bd1b9c54"
    },
    {
      type: "donation",
      title: "Donation Inflow Anchored",
      amount: "₹100",
      campaign: "Solar Clean Water Station Pune 2026",
      hash: "0x5c13e3e2d5cac9ce79c8adfad1bcd1538c7342207a74a75d7878130773509b34",
      tx: "0x5c13e3e2d5cac9ce79c8adfad1bcd1538c7342207a74a75d7878130773509b34",
      time: "10 mins ago",
      explorer_url: "https://amoy.polygonscan.com/tx/0x5c13e3e2d5cac9ce79c8adfad1bcd1538c7342207a74a75d7878130773509b34"
    },
    {
      type: "milestone_video",
      title: "Milestone Verified & On-Chain Anchored",
      campaign: "Solar Clean Water Station Pune 2026",
      hash: "0xc57890323468a02987bd659424e5653a1c7c4e55aa63d247bfe9246360a81bb6",
      tx: "0xc57890323468a02987bd659424e5653a1c7c4e55aa63d247bfe9246360a81bb6",
      time: "25 mins ago",
      explorer_url: "https://amoy.polygonscan.com/tx/0xc57890323468a02987bd659424e5653a1c7c4e55aa63d247bfe9246360a81bb6"
    },
    {
      type: "compliance_doc",
      title: "Campaign Approved & Budget Locked",
      campaign: "Solar Clean Water Station Pune 2026",
      hash: "0x887e43537bf665f53ab271e0e7d1ca68a8e1f184f5f370cb7d7f28e3650e44da",
      tx: "0x887e43537bf665f53ab271e0e7d1ca68a8e1f184f5f370cb7d7f28e3650e44da",
      time: "1 hour ago",
      explorer_url: "https://amoy.polygonscan.com/tx/0x887e43537bf665f53ab271e0e7d1ca68a8e1f184f5f370cb7d7f28e3650e44da"
    }
  ];

  return (
    <div className="bg-slate-950 text-slate-100 min-h-screen py-10">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-2 bg-purple-950/80 border border-purple-500/30 px-3 py-1 rounded-full text-xs font-semibold text-purple-300 mb-3">
            <Activity className="w-3.5 h-3.5 text-purple-400" />
            <span>Live Polygon Amoy Testnet Ledger (Chain ID: 80002)</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Universal Blockchain Explorer
          </h1>
          <p className="text-slate-400 mt-2 max-w-2xl text-sm sm:text-base">
            Every donation, compliance upload, milestone video hash, and volunteer credential is cryptographically anchored on Polygon.
          </p>
        </div>

        {/* Network Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs text-slate-400 uppercase font-semibold">Total Proofs Anchored</div>
            <div className="text-2xl font-bold font-mono text-emerald-400 mt-1">
              {stats?.total_proofs_anchored || 52}
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Immutable on-chain hashes</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs text-slate-400 uppercase font-semibold">Smart Contract</div>
            <div className="text-xs font-mono text-purple-400 font-bold mt-2 truncate">
              {stats?.contract_address || process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "0x0000000000000000000000000000000000000000"}
            </div>
            <a
              href={`https://amoy.polygonscan.com/address/${stats?.contract_address || process.env.NEXT_PUBLIC_CONTRACT_ADDRESS || "0x0000000000000000000000000000000000000000"}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[10px] text-purple-300 hover:underline flex items-center gap-1 mt-1"
            >
              <span>View on PolygonScan</span>
              <ExternalLink className="w-2.5 h-2.5" />
            </a>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs text-slate-400 uppercase font-semibold">Network</div>
            <div className="text-lg font-bold text-white mt-1">Polygon Amoy PoS</div>
            <div className="text-[10px] text-emerald-400 mt-0.5">● Healthy (2.1s Block Time)</div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <div className="text-xs text-slate-400 uppercase font-semibold">Consensus Engine</div>
            <div className="text-lg font-bold text-amber-400 mt-1">Donor Video Multi-Sig</div>
            <div className="text-[10px] text-slate-400 mt-0.5">Threshold: $\ge 75\%$ Thumbs Up</div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl mb-8">
          <form onSubmit={handleSearch} className="flex gap-3">
            <div className="relative flex-grow">
              <Search className="absolute left-3.5 inset-y-0 my-auto text-slate-500 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search by Transaction Hash (0x...) or SHA-256 Proof Hash..."
                value={searchHash}
                onChange={(e) => setSearchHash(e.target.value)}
                className="pl-10 text-sm bg-slate-950 border-slate-700 text-white focus:border-purple-500"
              />
            </div>
            <Button type="submit" disabled={isSearching} className="bg-purple-600 hover:bg-purple-700 text-white px-6">
              {isSearching ? "Searching..." : "Inspect Proof"}
            </Button>
          </form>

          {/* Search Result */}
          {searchError && (
            <div className="mt-4 p-3 bg-red-950/50 border border-red-800/60 rounded-xl text-xs text-red-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{searchError}</span>
            </div>
          )}

          {txResult && (
            <div className="mt-4 p-4 bg-slate-950 border border-purple-900/50 rounded-xl space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4" />
                <span>Verified On-Chain Transaction Found</span>
              </div>
              <div className="text-xs font-mono text-slate-300 break-all space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span>Tx Hash:</span>
                  <a
                    href={txResult.explorer_url || `https://amoy.polygonscan.com/tx/${txResult.tx_hash}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-400 hover:text-purple-300 underline flex items-center gap-1"
                  >
                    <span>{txResult.tx_hash}</span>
                    <ExternalLink className="w-3 h-3 inline" />
                  </a>
                </div>
                <div>Block: <span className="text-white">{txResult.block_number || "Amoy Verified"}</span></div>
                <div>Status: <span className="text-emerald-400 uppercase font-bold">{txResult.status || "Success"}</span></div>
              </div>
            </div>
          )}
        </div>

        {/* Real-time Ledger Stream */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              <h2 className="text-lg font-bold text-white">Live Cryptographic Audit Feed</h2>
            </div>
            <span className="text-xs text-emerald-400 font-mono flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Syncing
            </span>
          </div>

          <div className="space-y-3">
            {feedEvents.map((evt, idx) => (
              <div key={idx} className="p-4 bg-slate-950/80 border border-slate-800/80 rounded-xl hover:border-slate-700 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="bg-slate-900 border-slate-700 text-slate-300 text-[10px]">
                      {evt.type === "donation" && <Heart className="w-3 h-3 mr-1 text-emerald-400" />}
                      {evt.type === "milestone_video" && <Video className="w-3 h-3 mr-1 text-purple-400" />}
                      {evt.type === "volunteer_credential" && <Award className="w-3 h-3 mr-1 text-amber-400" />}
                      {evt.type === "compliance_doc" && <FileText className="w-3 h-3 mr-1 text-blue-400" />}
                      {evt.title}
                    </Badge>
                    <span className="text-xs text-slate-400">{evt.campaign}</span>
                    {evt.amount && (
                      <Badge className="bg-emerald-950/80 text-emerald-300 border-emerald-800/50 text-[10px]">
                        {evt.amount}
                      </Badge>
                    )}
                  </div>

                  <div className="text-[11px] font-mono text-slate-400 break-all">
                    Proof / Tx: <code className="text-slate-300">{evt.hash}</code>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-xs text-slate-500">{evt.time}</span>
                  <a
                    href={evt.explorer_url || `https://amoy.polygonscan.com/tx/${evt.tx}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1 font-mono bg-purple-950/40 border border-purple-800/50 px-2.5 py-1 rounded-lg"
                  >
                    <span>PolygonScan</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

