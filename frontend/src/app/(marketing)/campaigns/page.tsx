"use client";

import React, { useState, useEffect } from "react";
import { CampaignCard } from "@/components/campaigns/CampaignCard";
import { Campaign, campaignsApi } from "@/lib/api";
import { Search, Filter, Flame, ShieldAlert, Sparkles, RefreshCw } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [isDisasterOnly, setIsDisasterOnly] = useState<boolean>(false);
  const [selectedSafetyTier, setSelectedSafetyTier] = useState<string>("All");

  const categories = [
    "All",
    "disaster_relief",
    "education",
    "healthcare",
    "food_security",
    "environment",
    "livelihood",
  ];

  const safetyTiers = [
    { value: "All", label: "All Tiers" },
    { value: "open", label: "Open Volunteer (Low Risk)" },
    { value: "trained_only", label: "Trained Only (Medium Risk)" },
    { value: "no_volunteers", label: "No Volunteers (High Risk)" },
  ];

  const loadCampaigns = async () => {
    setIsLoading(true);
    try {
      const params: any = { status: "active" };
      if (selectedCategory !== "All") params.category = selectedCategory;
      if (isDisasterOnly) params.is_disaster_relief = true;
      if (selectedSafetyTier !== "All") params.safety_tier = selectedSafetyTier;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const data = await campaignsApi.list(params);
      if (data && data.length > 0) {
        setCampaigns(data);
      } else {
        // Fallback mock data if backend isn't available
        setCampaigns([
          {
            id: "c1",
            ngo_id: "NGO_00002",
            title: "Rural Tech Education Drive",
            description: "Providing laptops and internet access to 5 remote schools.",
            category: "education",
            target_amount: 100000,
            raised_amount: 45000,
            funding_percentage: 45,
            is_disaster_relief: false,
            status: "active"
          },
          {
            id: "c2",
            ngo_id: "NGO_00002",
            title: "Flood Relief Checkpoint",
            description: "Emergency shelter and food supplies for flood victims.",
            category: "disaster_relief",
            target_amount: 120000,
            raised_amount: 120000,
            funding_percentage: 100,
            is_disaster_relief: true,
            status: "active"
          }
        ]);
      }
    } catch (err) {
      console.warn("Failed to load campaigns.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCampaigns();
  }, [selectedCategory, isDisasterOnly, selectedSafetyTier]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCampaigns();
  };

  return (
    <div className="bg-slate-50 min-h-screen py-10">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <div className="mb-8">
         
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900">
            Explore Verified Campaigns
          </h1>
          <p className="text-slate-600 mt-2 max-w-2xl text-sm sm:text-base">
            Every campaign listed below has undergone automated regional price benchmarking and AI trust validation.
          </p>
        </div>

        {/* Search & Filter Bar */}
        <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200 mb-8 space-y-4">
          <form onSubmit={handleSearchSubmit} className="flex gap-3">
            <div className="relative flex-grow">
              <Search className="absolute left-3.5 inset-y-0 my-auto text-slate-400 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search by campaign title, cause, or NGO name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 text-sm bg-slate-50 border-slate-200 focus:bg-white"
              />
            </div>
            <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1 px-5">
              Search
            </Button>
            <Button 
              type="button" 
              variant="outline" 
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("All");
                setIsDisasterOnly(false);
                setSelectedSafetyTier("All");
              }}
              className="border-slate-200 text-slate-600 hover:bg-slate-100"
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          </form>

          {/* Filter Badges / Pills */}
          <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
            <span className="text-xs font-semibold text-slate-500 mr-2 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" /> Filter Category:
            </span>

            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1 rounded-full text-xs font-medium capitalize transition-all ${
                  selectedCategory === cat
                    ? "bg-emerald-600 text-white font-semibold shadow-sm"
                    : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                }`}
              >
                {cat.replace("_", " ")}
              </button>
            ))}

            <div className="h-4 w-px bg-slate-300 mx-2 hidden sm:block" />

            {/* Disaster Relief Toggle */}
            <button
              type="button"
              onClick={() => setIsDisasterOnly(!isDisasterOnly)}
              className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                isDisasterOnly
                  ? "bg-red-600 text-white shadow-sm"
                  : "bg-red-50 text-red-700 hover:bg-red-100 border border-red-200"
              }`}
            >
              <Flame className="w-3 h-3" />
              <span>Urgent Relief Only</span>
            </button>
          </div>
        </div>

        {/* Campaign Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="h-96 bg-slate-200 animate-pulse rounded-xl" />
            ))}
          </div>
        ) : campaigns.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((camp) => (
              <CampaignCard key={camp.id} campaign={camp} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-12 h-12 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">No campaigns found</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Try adjusting your category or search filters to explore other active causes.
            </p>
            <Button
              onClick={() => {
                setSearchQuery("");
                setSelectedCategory("All");
                setIsDisasterOnly(false);
                setSelectedSafetyTier("All");
              }}
              variant="outline"
              className="mt-2 text-xs"
            >
              Reset All Filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
