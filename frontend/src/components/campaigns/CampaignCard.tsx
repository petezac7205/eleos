import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { buttonVariants } from "@/components/ui/button";
import { CheckCircle2, ShieldCheck, Flame, Users, ArrowRight } from "lucide-react";
import Link from "next/link";
import React from "react";
import { Campaign } from "@/lib/api";

const categoryIcons: Record<string, string> = {
  "disaster_relief": "🌊",
  "education": "📚",
  "healthcare": "🏥",
  "food_security": "🍚",
  "environment": "🌱",
  "animal_welfare": "🐾",
  "livelihood": "💼",
};

export function CampaignCard({ campaign }: { campaign: Campaign }) {
  const percentComplete = campaign.funding_percentage 
    ? Math.min(100, Math.round(campaign.funding_percentage))
    : Math.min(100, Math.round(((campaign.current_amount || 0) / (campaign.target_amount || 1)) * 100));

  const categoryKey = campaign.category?.toLowerCase().replace(/\s+/g, "_") || "education";
  const icon = categoryIcons[categoryKey] || "🎯";

  return (
    <Card className="flex flex-col overflow-hidden border border-slate-200 transition-all duration-200 hover:shadow-lg bg-white rounded-xl hover:-translate-y-1">
      {/* Top Banner / Image */}
      <div className="h-44 bg-slate-100 relative overflow-hidden group">
        {campaign.cover_image_url ? (
          <img 
            src={campaign.cover_image_url} 
            alt={campaign.title} 
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-tr from-emerald-800 to-teal-950 flex items-center justify-center text-4xl">
            {icon}
          </div>
        )}

        {/* AI Score Badge overlay */}
        <div className="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-2.5 py-1 rounded-full shadow-sm flex items-center gap-1.5 border border-slate-200">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span className="text-[11px] font-bold text-slate-800">
            {campaign.ngo_trust_badge ? campaign.ngo_trust_badge.toUpperCase() : "VERIFIED"}
          </span>
        </div>

        {/* Disaster Relief Badge */}
        {campaign.is_disaster_relief && (
          <div className="absolute top-3 right-3 bg-red-600 text-white px-2.5 py-1 rounded-full text-[10px] font-bold flex items-center gap-1 shadow-sm uppercase tracking-wide">
            <Flame className="w-3 h-3" /> Urgent
          </div>
        )}
      </div>

      {/* Header Info */}
      <CardHeader className="pb-2 pt-4 px-5">
        <div className="flex justify-between items-center mb-1">
          <Badge variant="outline" className="bg-slate-50 text-slate-700 border-slate-200 gap-1 font-medium px-2 py-0.5 text-[11px]">
            <span>{icon}</span> {campaign.category}
          </Badge>

          {campaign.safety_tier && (
            <Badge 
              variant="outline" 
              className={`text-[10px] uppercase font-semibold ${
                campaign.safety_tier === "open"
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : campaign.safety_tier === "trained_only"
                  ? "bg-amber-50 text-amber-700 border-amber-200"
                  : "bg-red-50 text-red-700 border-red-200"
              }`}
            >
              {campaign.safety_tier.replace("_", " ")}
            </Badge>
          )}
        </div>

        <CardTitle className="text-lg font-bold text-slate-900 line-clamp-1 hover:text-emerald-600 transition-colors">
          <Link href={`/campaigns/${campaign.id}`}>{campaign.title}</Link>
        </CardTitle>

        <p className="text-xs text-slate-500 font-medium flex items-center gap-1 mt-0.5">
          by {campaign.ngo_name || "Verified NGO"} <CheckCircle2 className="h-3 w-3 text-emerald-600 inline" />
        </p>
      </CardHeader>

      {/* Content & Progress */}
      <CardContent className="flex-grow px-5 py-2">
        <p className="text-xs text-slate-600 line-clamp-2 mb-3">
          {campaign.description}
        </p>

        <div className="space-y-1.5 bg-slate-50 p-3 rounded-lg border border-slate-100">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-slate-900">₹{(campaign.current_amount || 0).toLocaleString("en-IN")}</span>
            <span className="text-slate-500">of ₹{(campaign.target_amount || 0).toLocaleString("en-IN")}</span>
          </div>
          <Progress value={percentComplete} className="h-2 bg-slate-200" />
          <div className="flex justify-between items-center text-[10px] text-slate-500 pt-0.5">
            <span>{percentComplete}% funded</span>
            <span>{campaign.state || "India"}</span>
          </div>
        </div>
      </CardContent>

      {/* Footer CTA */}
      <CardFooter className="px-5 pt-2 pb-4">
        <Link 
          href={`/campaigns/${campaign.id}`} 
          className={buttonVariants({ 
            className: "w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2 rounded-lg gap-1.5 shadow-sm text-sm" 
          })}
        >
          <span>View Campaign & Verify</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </CardFooter>
    </Card>
  );
}
