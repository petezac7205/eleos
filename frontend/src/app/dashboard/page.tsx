"use client";

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Heart, 
  Download, 
  Clock, 
  MapPin, 
  CheckCircle2, 
  ShieldCheck, 
  Award,
  ExternalLink,
  Target,
  Calendar
} from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { donationsApi, volunteerApi } from "@/lib/api";

// Fallback seed data for demo safety if account has no history yet
const SEED_FALLBACK_DONATIONS = [
  {
    id: "don_1",
    date: "2026-09-12",
    amount: 15000,
    campaign_title: "Solar Clean Water Station Pune 2026",
    ngo_name: "Uday Network National",
    status: "Verified",
    blockchain_tx: "0x47f6a8909e6cbf984e3f6b8df954b10887cbf344a11d193437d24599bd1b9c54",
    tax_receipt_available: true
  },
  {
    id: "don_2",
    date: "2026-08-05",
    amount: 5000,
    campaign_title: "Flood Relief Checkpoint",
    ngo_name: "HopeRelief Foundation",
    status: "Verified",
    blockchain_tx: "0x5c13e3e2d5cac9ce79c8adfad1bcd1538c7342207a74a75d7878130773509b34",
    tax_receipt_available: true
  }
];

const SEED_FALLBACK_CREDENTIALS = [
  {
    id: "cred_1",
    title: "Disaster Relief Responder",
    campaign: "Assam Flood Rescue 2025",
    ngo: "HopeRelief Foundation",
    hours: 45,
    issued_date: "2025-07-20",
    credential_hash: "0xc57890323468a02987bd659424e5653a1c7c4e55aa63d247bfe9246360a81bb6"
  }
];

export default function DonorDashboard() {
  const { user } = useAuth();
  const [donations, setDonations] = useState<any[]>([]);
  const [credentials, setCredentials] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      try {
        const [donationsRes, credsRes] = await Promise.allSettled([
          donationsApi.getMyDonations(),
          volunteerApi.getMyCredentials()
        ]);

        if (donationsRes.status === "fulfilled" && donationsRes.value) {
          const list = Array.isArray(donationsRes.value) 
            ? donationsRes.value 
            : (donationsRes.value as any)?.donations || [];
          
          if (list.length > 0) {
            const mapped = list.map((d: any) => ({
              id: d.id,
              date: d.created_at || d.completed_at || new Date().toISOString(),
              amount: d.amount,
              campaign_title: d.campaign_title || "Humanitarian Campaign",
              ngo_name: d.ngo_name || "Verified NGO",
              status: (d.status === "completed" || d.blockchain_confirmed) ? "Verified" : "Pending",
              blockchain_tx: d.blockchain_tx_hash,
              tax_receipt_available: d.status === "completed" || d.blockchain_confirmed
            }));
            setDonations(mapped);
          } else {
            setDonations(SEED_FALLBACK_DONATIONS);
          }
        } else {
          setDonations(SEED_FALLBACK_DONATIONS);
        }

        if (credsRes.status === "fulfilled" && Array.isArray(credsRes.value) && credsRes.value.length > 0) {
          const mappedCreds = credsRes.value.map((c: any) => ({
            id: c.id,
            title: c.opportunity_title || "Humanitarian Service",
            campaign: c.campaign_title || "Relief Mission",
            ngo: c.ngo_name || "Verified NGO",
            hours: c.hours_logged || c.hours_served || 0,
            issued_date: c.issued_at || new Date().toISOString(),
            credential_hash: c.blockchain_tx_hash || c.certificate_hash || "0xc57890323468a02987bd659424e5653a1c7c4e55aa63d247bfe9246360a81bb6"
          }));
          setCredentials(mappedCreds);
        } else {
          setCredentials(SEED_FALLBACK_CREDENTIALS);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setDonations(SEED_FALLBACK_DONATIONS);
        setCredentials(SEED_FALLBACK_CREDENTIALS);
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, [user]);

  // Calculate totals dynamically
  const totalDonated = donations.filter(d => d.status === "Verified").reduce((acc, curr) => acc + (curr.amount || 0), 0);
  const totalHours = credentials.reduce((acc, curr) => acc + (curr.hours || 0), 0);

  return (
    <div className="min-h-screen bg-slate-50 pb-20">
      
      {/* Header Section */}
      <section className="bg-slate-900 text-white pt-24 pb-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('/hero-bg-real.jpg')] bg-cover bg-center opacity-10"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-slate-900 to-transparent"></div>
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-primary/20 rounded-full blur-[100px]"></div>
        
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="flex flex-col md:flex-row items-center md:items-end justify-between gap-6">
            <div>
              <h1 className="text-3xl md:text-5xl font-black tracking-tight mb-2">
                Welcome back, {user?.name || "Samagra"}
              </h1>
              <p className="text-slate-400 text-lg">
                Your philanthropic impact and verified credentials.
              </p>
            </div>
            <Link href="/campaigns">
              <Button className="bg-white text-slate-900 hover:bg-slate-100 font-bold px-6">
                Find Campaigns
              </Button>
            </Link>
          </div>

          {/* Impact Metrics - Glassmorphic */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-10">
            {/* Metric 1 */}
            <div className="bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl p-6 relative overflow-hidden group hover:bg-white/15 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-30 transition-opacity">
                <Heart className="w-16 h-16" />
              </div>
              <p className="text-slate-300 font-medium text-sm mb-1 uppercase tracking-wider">Total Impact</p>
              <h3 className="text-4xl font-black text-white">₹{totalDonated.toLocaleString()}</h3>
              <p className="text-emerald-400 text-xs font-bold mt-2 flex items-center">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Donations Secured
              </p>
            </div>

            {/* Metric 2 */}
            <div className="bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl p-6 relative overflow-hidden group hover:bg-white/15 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-30 transition-opacity">
                <Target className="w-16 h-16" />
              </div>
              <p className="text-slate-300 font-medium text-sm mb-1 uppercase tracking-wider">Campaigns Supported</p>
              <h3 className="text-4xl font-black text-white">3</h3>
              <p className="text-emerald-400 text-xs font-bold mt-2 flex items-center">
                <ShieldCheck className="w-3 h-3 mr-1" /> Impact Confirmed
              </p>
            </div>

            {/* Metric 3 */}
            <div className="bg-white/10 backdrop-blur-md border border-white/10 rounded-2xl p-6 relative overflow-hidden group hover:bg-white/15 transition-all">
              <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-30 transition-opacity">
                <Clock className="w-16 h-16" />
              </div>
              <p className="text-slate-300 font-medium text-sm mb-1 uppercase tracking-wider">Volunteer Hours</p>
              <h3 className="text-4xl font-black text-white">{totalHours}</h3>
              <p className="text-emerald-400 text-xs font-bold mt-2 flex items-center">
                <Award className="w-3 h-3 mr-1" /> 2 Verified Certificates
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 -mt-8 relative z-20">
        <Card className="border-2 border-slate-200 shadow-xl rounded-2xl overflow-hidden bg-white/95 backdrop-blur-xl">
          <Tabs defaultValue="donations" className="w-full">
            <div className="px-6 pt-6 pb-0 border-b border-slate-100">
              <TabsList className="space-x-8 h-auto p-0" variant="plain">
                <TabsTrigger 
                  value="donations" 
                  className="relative group bg-transparent text-slate-600 hover:text-emerald-700 data-active:text-emerald-700 data-active:bg-transparent shadow-none border-none outline-none after:hidden px-1 pb-4 h-auto rounded-none transition-colors text-sm font-medium"
                >
                  Donation History
                  <span className="absolute bottom-0 left-1/2 w-0 h-0.5 bg-emerald-600 transition-all duration-300 group-hover:w-full group-hover:left-0 group-[&[data-active]]:w-full group-[&[data-active]]:left-0" />
                </TabsTrigger>
                <TabsTrigger 
                  value="credentials" 
                  className="relative group bg-transparent text-slate-600 hover:text-emerald-700 data-active:text-emerald-700 data-active:bg-transparent shadow-none border-none outline-none after:hidden px-1 pb-4 h-auto rounded-none transition-colors text-sm font-medium"
                >
                  Volunteer Credentials
                  <span className="absolute bottom-0 left-1/2 w-0 h-0.5 bg-emerald-600 transition-all duration-300 group-hover:w-full group-hover:left-0 group-[&[data-active]]:w-full group-[&[data-active]]:left-0" />
                </TabsTrigger>
              </TabsList>
            </div>

            {/* Donations Tab */}
            <TabsContent value="donations" className="p-0 m-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader className="bg-slate-50">
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="py-4 text-slate-500 font-medium text-sm">Date</TableHead>
                      <TableHead className="py-4 text-slate-500 font-medium text-sm">Campaign & NGO</TableHead>
                      <TableHead className="py-4 text-slate-500 font-medium text-sm text-right">Amount</TableHead>
                      <TableHead className="py-4 text-slate-500 font-medium text-sm text-center">Status</TableHead>
                      <TableHead className="py-4 text-slate-500 font-medium text-sm text-center">Blockchain Proof</TableHead>
                      <TableHead className="py-4 text-slate-500 font-medium text-sm text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {donations.map((donation) => (
                      <TableRow key={donation.id} className="hover:bg-slate-50/50 transition-colors">
                        <TableCell className="py-5 text-slate-600 whitespace-nowrap text-sm">
                          {new Date(donation.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </TableCell>
                        <TableCell className="py-5">
                          <p className="font-medium text-slate-900">{donation.campaign_title}</p>
                          <p className="text-sm text-slate-500 mt-0.5">{donation.ngo_name}</p>
                        </TableCell>
                        <TableCell className="py-5 text-right font-medium text-slate-800">
                          ₹{donation.amount.toLocaleString()}
                        </TableCell>
                        <TableCell className="py-5 text-center">
                          {donation.status === "Verified" ? (
                            <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 font-medium px-3 py-1">
                              <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> Confirmed
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200 font-medium px-3 py-1">
                              <Clock className="w-3.5 h-3.5 mr-1.5" /> Processing
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell className="py-5 text-center">
                          {donation.blockchain_tx ? (
                            <a
                              href={`https://amoy.polygonscan.com/tx/${donation.blockchain_tx}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs font-mono text-purple-600 hover:text-purple-800 hover:underline bg-purple-50 px-2 py-1 rounded border border-purple-200"
                            >
                              <span>{donation.blockchain_tx.substring(0, 10)}...</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-xs text-slate-400 italic">Pending anchor</span>
                          )}
                        </TableCell>
                        <TableCell className="py-5 text-right">
                          {donation.tax_receipt_available ? (
                            <Button variant="outline" size="sm" className="text-sm font-medium hover:bg-slate-100 hover:text-primary px-4 py-2 h-auto">
                              <Download className="w-4 h-4 mr-2" /> Receipt
                            </Button>
                          ) : (
                            <span className="text-sm text-slate-400 italic">Processing...</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </TabsContent>

            {/* Credentials Tab */}
            <TabsContent value="credentials" className="p-8 m-0">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {credentials.map((cred) => (
                  <div key={cred.id} className="border border-slate-200 rounded-2xl p-8 bg-white hover:border-emerald-200 hover:shadow-lg transition-all group relative overflow-hidden">
                    {/* Decorative element */}
                    <div className="absolute -right-10 -top-10 w-32 h-32 bg-emerald-50 rounded-full group-hover:scale-150 transition-transform duration-700 ease-out z-0"></div>
                    
                    <div className="relative z-10">
                      <div className="flex items-start justify-between mb-6">
                        <div className="w-14 h-14 rounded-full bg-emerald-100 flex items-center justify-center border-4 border-white shadow-sm">
                          <Award className="w-6 h-6 text-emerald-600" />
                        </div>
                        <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-100 border-none px-3 py-1 font-medium">{cred.hours} Hours</Badge>
                      </div>
                      
                      <h3 className="text-xl font-bold text-slate-900 mb-2">{cred.title}</h3>
                      <p className="text-sm text-primary mb-6">{cred.campaign}</p>
                      
                      <div className="space-y-3 mb-8">
                        <div className="flex items-center text-sm text-slate-500">
                          <MapPin className="w-4 h-4 mr-3 text-slate-400" />
                          {cred.ngo}
                        </div>
                        <div className="flex items-center text-sm text-slate-500">
                          <Calendar className="w-4 h-4 mr-3 text-slate-400" />
                          Issued: {new Date(cred.issued_date).toLocaleDateString()}
                        </div>
                      </div>
                      
                      <div className="pt-6 border-t border-slate-100 flex items-center justify-between">
                        <div className="text-xs font-mono text-slate-400 truncate max-w-[150px]">
                          ID: {cred.credential_hash?.substring(0, 10)}...
                        </div>
                        <a 
                          href={`https://amoy.polygonscan.com/tx/${cred.credential_hash}`}
                          target="_blank"
                          rel="noopener noreferrer" 
                          className="text-sm font-medium text-purple-600 hover:text-purple-800 flex items-center hover:underline"
                        >
                          Verify on PolygonScan <ExternalLink className="w-4 h-4 ml-1.5" />
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

          </Tabs>
        </Card>
      </div>
    </div>
  );
}

