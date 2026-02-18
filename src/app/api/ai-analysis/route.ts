import { NextRequest, NextResponse } from "next/server";
import type { DailyMetrics, Campaign } from "@/types";

/**
 * AI Analysis API route.
 * In production, this would call the Gemini API for intelligent analysis.
 * Currently returns rule-based recommendations as a scaffold.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const {
      clientName,
      metrics,
      campaigns,
    }: {
      clientName: string;
      metrics: DailyMetrics[];
      campaigns: Campaign[];
    } = body;

    const recommendations = generateRecommendations(metrics, campaigns);

    return NextResponse.json({
      summary: `Analysis complete for ${clientName}. Found ${recommendations.length} optimization opportunities.`,
      recommendations,
      generatedAt: new Date().toISOString(),
    });
  } catch (error) {
    console.error("AI analysis error:", error);
    return NextResponse.json(
      { error: "Analysis failed" },
      { status: 500 }
    );
  }
}

function generateRecommendations(
  metrics: DailyMetrics[],
  campaigns: Campaign[]
) {
  const recommendations: { priority: "high" | "medium" | "low"; category: string; description: string; estimatedImpact: string }[] = [];

  if (metrics.length < 7) return recommendations;

  // Analyze recent vs previous performance
  const recent = metrics.slice(-7);
  const previous = metrics.slice(-14, -7);

  const recentCost = recent.reduce((s, m) => s + m.cost, 0);
  const prevCost =
    previous.length > 0
      ? previous.reduce((s, m) => s + m.cost, 0)
      : recentCost;
  const costChange = ((recentCost - prevCost) / prevCost) * 100;

  const recentConvRate =
    recent.reduce((s, m) => s + m.conversionRate, 0) / recent.length;
  const prevConvRate =
    previous.length > 0
      ? previous.reduce((s, m) => s + m.conversionRate, 0) / previous.length
      : recentConvRate;

  // Cost increase without conversion improvement
  if (costChange > 15 && recentConvRate <= prevConvRate) {
    recommendations.push({
      priority: "high" as const,
      category: "Budget Management",
      description: `Cost has increased ${costChange.toFixed(0)}% week-over-week without a corresponding increase in conversion rate. Review search terms for wasteful spend and consider tightening keyword match types.`,
      estimatedImpact: `Save ~$${Math.round(recentCost * 0.15)}/week`,
    });
  }

  // Campaign-level analysis
  for (const campaign of campaigns) {
    if (campaign.status !== "enabled") continue;

    // Low CTR campaigns
    if (campaign.ctr < 2 && campaign.impressions > 1000) {
      recommendations.push({
        priority: "medium" as const,
        category: "Ad Copy",
        description: `Campaign "${campaign.name}" has a below-average CTR of ${campaign.ctr.toFixed(1)}%. Consider testing new ad copy with stronger calls-to-action and more relevant headlines.`,
        estimatedImpact: `+${Math.round(campaign.ctr * 0.5 * 10) / 10}% CTR improvement`,
      });
    }

    // High CPC campaigns
    if (campaign.cpc > 5 && campaign.type === "search") {
      recommendations.push({
        priority: "medium" as const,
        category: "Bidding Strategy",
        description: `Campaign "${campaign.name}" has a high CPC of $${campaign.cpc.toFixed(2)}. Consider switching to automated bidding (Target CPA or Target ROAS) to optimize bid efficiency.`,
        estimatedImpact: `-15-20% CPC reduction`,
      });
    }

    // Budget-limited campaigns with good ROAS
    if (
      campaign.roas >= 3 &&
      campaign.spend >= campaign.budget * 0.9
    ) {
      recommendations.push({
        priority: "high" as const,
        category: "Budget Allocation",
        description: `Campaign "${campaign.name}" is budget-limited with a strong ROAS of ${campaign.roas}x. Increasing budget could capture additional profitable conversions.`,
        estimatedImpact: `+${Math.round(campaign.conversions * 0.2)} conversions/month`,
      });
    }
  }

  return recommendations.slice(0, 6); // Limit to top 6 recommendations
}
