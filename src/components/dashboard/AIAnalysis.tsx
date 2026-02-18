"use client";

import { useState } from "react";
import Card from "@/components/ui/Card";
import { Sparkles, ChevronDown, ChevronUp, Zap } from "lucide-react";

interface Recommendation {
  priority: "high" | "medium" | "low";
  category: string;
  description: string;
  estimatedImpact: string;
}

interface AIAnalysisProps {
  clientName: string;
  recommendations?: Recommendation[];
}

const defaultRecommendations: Recommendation[] = [
  {
    priority: "high",
    category: "Bidding Strategy",
    description:
      "Switch 'Non-Brand - Camping Gear' campaign from manual CPC to Target ROAS. Current ROAS of 3.9x suggests the campaign can sustain automated bidding with a 350% target.",
    estimatedImpact: "+15-20% conversions",
  },
  {
    priority: "high",
    category: "Negative Keywords",
    description:
      "Add 23 identified negative keywords to the 'Non-Brand' campaign. Search term analysis shows 12% of spend going to irrelevant queries like 'free camping spots' and 'camping recipes'.",
    estimatedImpact: "Save ~$640/month",
  },
  {
    priority: "medium",
    category: "Ad Copy",
    description:
      "Refresh ad copy for 'Brand Search' campaign. Top-performing headlines have been running for 60+ days and CTR has declined 8% month-over-month.",
    estimatedImpact: "+5-8% CTR improvement",
  },
  {
    priority: "low",
    category: "Budget Allocation",
    description:
      "Consider reallocating $500/month from the paused Display Retargeting campaign to the high-performing Shopping campaign which is limited by budget.",
    estimatedImpact: "+12 conversions/month",
  },
];

const priorityColors = {
  high: "bg-red-400/10 text-red-400 border-red-400/20",
  medium: "bg-amber-400/10 text-amber-400 border-amber-400/20",
  low: "bg-blue-400/10 text-blue-400 border-blue-400/20",
};

export default function AIAnalysis({
  clientName,
  recommendations = defaultRecommendations,
}: AIAnalysisProps) {
  const [expanded, setExpanded] = useState(true);

  return (
    <Card>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-purple-500/10">
            <Sparkles className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-left">
            <h3 className="text-sm font-medium text-foreground">
              Gemini AI Optimization Analysis
            </h3>
            <p className="text-xs text-muted">
              {recommendations.length} recommendations for {clientName}
            </p>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-muted" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted" />
        )}
      </button>

      {expanded && (
        <div className="mt-4 space-y-3">
          {recommendations.map((rec, i) => (
            <div
              key={i}
              className="flex gap-3 p-3 rounded-lg bg-background border border-border"
            >
              <div className="flex-shrink-0 mt-0.5">
                <Zap className="w-4 h-4 text-purple-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${priorityColors[rec.priority]}`}
                  >
                    {rec.priority}
                  </span>
                  <span className="text-xs font-medium text-muted">
                    {rec.category}
                  </span>
                </div>
                <p className="text-sm text-foreground/80 leading-relaxed">
                  {rec.description}
                </p>
                <p className="text-xs text-emerald-400 mt-1.5 flex items-center gap-1">
                  <span className="font-medium">Impact:</span>{" "}
                  {rec.estimatedImpact}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
