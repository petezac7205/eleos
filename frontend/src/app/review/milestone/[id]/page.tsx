"use client";

import React, { useState, useEffect, use } from "react";
import { useSearchParams } from "next/navigation";
import { donorReviewApi, InvitationData } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { 
  ThumbsUp, 
  ThumbsDown, 
  CheckCircle2, 
  ShieldCheck, 
  Video, 
  Heart, 
  ExternalLink, 
  Loader2, 
  AlertCircle,
  Cpu,
  Sparkles
} from "lucide-react";
import Link from "next/link";

export default function DonorMilestoneReviewPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const milestoneId = resolvedParams.id;
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [invitation, setInvitation] = useState<InvitationData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [feedback, setFeedback] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [voteSuccess, setVoteSuccess] = useState<{
    vote: string;
    consensus_reached: boolean;
    tx_hash?: string;
    message: string;
  } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    donorReviewApi
      .getInvitationByToken(token)
      .then(setInvitation)
      .catch((err) => {
        setErrorMessage(err.message || "Invalid or expired review magic link.");
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  const handleVote = async (voteType: "approved" | "rejected") => {
    if (!token) return;
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const res = await donorReviewApi.submitVote(token, voteType, feedback);
      setVoteSuccess({
        vote: voteType,
        consensus_reached: res.consensus_reached || false,
        tx_hash: res.blockchain_tx_hash,
        message: res.message || "Your review vote has been registered on Polygon Amoy testnet.",
      });
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to record your vote.");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-400 mx-auto" />
          <p className="text-sm text-slate-400">Loading your verified donor review session...</p>
        </div>
      </div>
    );
  }

  if (!token || errorMessage) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-4">
        <div className="bg-slate-900 border border-slate-800 p-8 rounded-2xl max-w-md w-full text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-amber-400 mx-auto" />
          <h2 className="text-xl font-bold">Review Link Required</h2>
          <p className="text-xs text-slate-400">
            {errorMessage || "Please access this review page using the magic link sent to your registered email address."}
          </p>
          <Link href="/campaigns">
            <Button className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">
              Explore Active Campaigns
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-12 px-4">
      <div className="container mx-auto max-w-3xl space-y-6">
        {/* Header Badge */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-1.5 bg-purple-950/80 border border-purple-500/40 text-purple-300 px-3.5 py-1.5 rounded-full text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span>DONOR AS REVIEWER • DEMOCRATIZED CONSENSUS</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
            Verify Milestone Delivery Proof
          </h1>

          <p className="text-xs sm:text-sm text-slate-400 max-w-xl mx-auto">
            Because you contributed to <strong className="text-white">{invitation?.campaign_title || "this cause"}</strong>, your vote directly validates this milestone on the public blockchain.
          </p>
        </div>

        {/* Main Content Card */}
        <Card className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
          {/* Top Hearty Note from Charity */}
          {invitation?.hearty_note_top && (
            <div className="bg-emerald-950/40 border-b border-emerald-900/40 p-5 text-xs text-emerald-200 leading-relaxed flex items-start gap-3">
              <Heart className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <div>
                <strong className="block text-emerald-300 mb-1">Message from the NGO On-Ground Team:</strong>
                <p>{invitation.hearty_note_top}</p>
              </div>
            </div>
          )}

          <CardContent className="p-6 space-y-6">
            {/* Milestone & Video Section */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-[11px] text-slate-400 uppercase font-semibold">Milestone Name</span>
                  <h3 className="text-lg font-bold text-white">{invitation?.milestone_title || "Aid Distribution"}</h3>
                </div>

                <Badge variant="outline" className="bg-slate-800 text-slate-300 border-slate-700 text-xs gap-1">
                  <Video className="w-3.5 h-3.5 text-purple-400" /> Video Evidence
                </Badge>
              </div>

              {/* Video Player or Proof Mock Container */}
              <div className="w-full aspect-video bg-slate-950 rounded-xl border border-slate-800 flex flex-col items-center justify-center p-6 text-center overflow-hidden relative group">
                {invitation?.video_url && invitation.video_url.endsWith(".mp4") ? (
                  <video
                    src={invitation.video_url}
                    controls
                    className="w-full h-full object-cover rounded-lg"
                    poster="/volunteer-hero.jpg"
                  />
                ) : (
                  <div className="space-y-3">
                    <div className="w-16 h-16 bg-purple-500/20 text-purple-400 rounded-full flex items-center justify-center mx-auto">
                      <Video className="w-8 h-8" />
                    </div>
                    <div>
                      <p className="text-sm font-bold text-slate-200">On-Ground Delivery Proof Video</p>
                      <p className="text-xs text-slate-500 max-w-sm mt-1">
                        Footage recorded by field coordinators verifying distribution to targeted beneficiaries.
                      </p>
                    </div>
                    {invitation?.video_url && (
                      <a
                        href={invitation.video_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium underline pt-2"
                      >
                        <span>Open Raw Video Stream</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Bottom Hearty Note */}
            {invitation?.hearty_note_bottom && (
              <div className="text-xs text-slate-400 italic bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
                "{invitation.hearty_note_bottom}"
              </div>
            )}

            {/* Voting Form or Success State */}
            {voteSuccess ? (
              <div className="bg-emerald-950/30 border border-emerald-800/60 rounded-xl p-6 text-center space-y-4">
                <div className="w-12 h-12 bg-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h4 className="text-xl font-bold text-white">Vote Recorded on Polygon!</h4>
                <p className="text-xs text-slate-300 max-w-md mx-auto">
                  {voteSuccess.message}
                </p>

                {voteSuccess.tx_hash && (
                  <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px] font-mono text-purple-400 break-all">
                    <span>Polygon Tx: </span>
                    <a
                      href={`https://amoy.polygonscan.com/tx/${voteSuccess.tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="underline text-purple-300"
                    >
                      {voteSuccess.tx_hash}
                    </a>
                  </div>
                )}

                <div className="pt-2">
                  <Link href="/campaigns">
                    <Button className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs px-6">
                      Return to Campaigns
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="space-y-4 pt-2 border-t border-slate-800">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                    Optional Feedback for the Field Team
                  </label>
                  <textarea
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Share any comments or observations regarding this video evidence..."
                    rows={2}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 focus:border-purple-500 focus:ring-purple-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                  <Button
                    onClick={() => handleVote("approved")}
                    disabled={isSubmitting}
                    className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 text-sm rounded-xl gap-2 shadow-lg shadow-emerald-900/30"
                  >
                    <ThumbsUp className="w-4 h-4" />
                    <span>Approve (Thumbs Up 👍)</span>
                  </Button>

                  <Button
                    onClick={() => handleVote("rejected")}
                    disabled={isSubmitting}
                    variant="outline"
                    className="border-red-800/80 bg-red-950/20 text-red-300 hover:bg-red-900/40 hover:text-white font-bold py-3 text-sm rounded-xl gap-2"
                  >
                    <ThumbsDown className="w-4 h-4" />
                    <span>Flag Issue (Thumbs Down 👎)</span>
                  </Button>
                </div>

                <p className="text-[11px] text-slate-500 text-center">
                  Consensus Rule: $\ge 2$ Thumbs Up and $\ge 75\%$ positive ratio triggers automated milestone completion.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

