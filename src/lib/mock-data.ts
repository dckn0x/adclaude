import {
  Client,
  Alert,
  Campaign,
  DailyMetrics,
  AnomalyDetection,
} from "@/types";

export const mockAlerts: Alert[] = [
  {
    id: "a1",
    clientId: "1",
    type: "budget",
    severity: "critical",
    message: "Monthly budget exceeded by 42% — spending $28,400 of $20,000",
    createdAt: "2026-02-18T08:00:00Z",
    resolved: false,
  },
  {
    id: "a2",
    clientId: "2",
    type: "campaign",
    severity: "warning",
    message:
      'Campaign "Summer Sale" CPA increased 35% week-over-week',
    createdAt: "2026-02-17T14:30:00Z",
    resolved: false,
  },
  {
    id: "a3",
    clientId: "3",
    type: "performance",
    severity: "warning",
    message: "Conversion rate dropped below 2% threshold",
    createdAt: "2026-02-16T10:15:00Z",
    resolved: false,
  },
  {
    id: "a4",
    clientId: "2",
    type: "anomaly",
    severity: "info",
    message: "Unusual spike in impression share detected",
    createdAt: "2026-02-15T16:00:00Z",
    resolved: true,
  },
];

export const mockClients: Client[] = [
  {
    id: "1",
    name: "Law Firm of Smith & Co",
    customerId: "123-456-7890",
    healthStatus: "error",
    alerts: mockAlerts.filter((a) => a.clientId === "1"),
    budgetPacing: 142,
    monthlyBudget: 20000,
    monthlySpend: 28400,
    cpa30d: 78.5,
    roas: 1.8,
    industry: "Legal",
    createdAt: "2025-06-15T00:00:00Z",
  },
  {
    id: "2",
    name: "Apex Outdoor Gear",
    customerId: "234-567-8901",
    healthStatus: "active",
    alerts: mockAlerts.filter((a) => a.clientId === "2"),
    budgetPacing: 95,
    monthlyBudget: 15000,
    monthlySpend: 13904,
    cpa30d: 32.11,
    roas: 4.2,
    industry: "E-Commerce",
    createdAt: "2025-08-01T00:00:00Z",
  },
  {
    id: "3",
    name: "TechFlow SaaS",
    customerId: "345-678-9012",
    healthStatus: "warning",
    alerts: mockAlerts.filter((a) => a.clientId === "3"),
    budgetPacing: 67,
    monthlyBudget: 25000,
    monthlySpend: 12970,
    cpa30d: 45.3,
    roas: 3.1,
    industry: "Technology",
    createdAt: "2025-09-20T00:00:00Z",
  },
];

export function generateDailyMetrics(days: number = 30): DailyMetrics[] {
  const metrics: DailyMetrics[] = [];
  const now = new Date();

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);

    const baseCost = 400 + Math.random() * 200;
    const baseConversions = 10 + Math.random() * 20;
    const baseClicks = 150 + Math.random() * 100;
    const baseImpressions = 5000 + Math.random() * 3000;

    metrics.push({
      date: date.toISOString().split("T")[0],
      cost: Math.round(baseCost * 100) / 100,
      conversions: Math.round(baseConversions),
      clicks: Math.round(baseClicks),
      impressions: Math.round(baseImpressions),
      ctr: Math.round((baseClicks / baseImpressions) * 10000) / 100,
      cpc: Math.round((baseCost / baseClicks) * 100) / 100,
      conversionRate:
        Math.round((baseConversions / baseClicks) * 10000) / 100,
    });
  }

  return metrics;
}

export const mockCampaigns: Campaign[] = [
  {
    id: "c1",
    clientId: "2",
    name: "Brand Search - Apex Outdoor",
    status: "enabled",
    type: "search",
    budget: 100,
    spend: 89.5,
    impressions: 12500,
    clicks: 890,
    conversions: 45,
    cost: 2685,
    ctr: 7.12,
    cpc: 3.02,
    conversionRate: 5.06,
    roas: 6.8,
  },
  {
    id: "c2",
    clientId: "2",
    name: "Non-Brand - Camping Gear",
    status: "enabled",
    type: "search",
    budget: 200,
    spend: 178.3,
    impressions: 45000,
    clicks: 1200,
    conversions: 32,
    cost: 5349,
    ctr: 2.67,
    cpc: 4.46,
    conversionRate: 2.67,
    roas: 3.9,
  },
  {
    id: "c3",
    clientId: "2",
    name: "Shopping - All Products",
    status: "enabled",
    type: "shopping",
    budget: 150,
    spend: 132.8,
    impressions: 89000,
    clicks: 2100,
    conversions: 78,
    cost: 3984,
    ctr: 2.36,
    cpc: 1.9,
    conversionRate: 3.71,
    roas: 5.2,
  },
  {
    id: "c4",
    clientId: "2",
    name: "Performance Max - Summer",
    status: "enabled",
    type: "pmax",
    budget: 80,
    spend: 62.4,
    impressions: 120000,
    clicks: 950,
    conversions: 22,
    cost: 1872,
    ctr: 0.79,
    cpc: 1.97,
    conversionRate: 2.32,
    roas: 3.4,
  },
  {
    id: "c5",
    clientId: "2",
    name: "Display - Retargeting",
    status: "paused",
    type: "display",
    budget: 50,
    spend: 0,
    impressions: 0,
    clicks: 0,
    conversions: 0,
    cost: 0,
    ctr: 0,
    cpc: 0,
    conversionRate: 0,
    roas: 0,
  },
];

export const mockAnomalies: AnomalyDetection[] = [
  {
    id: "an1",
    clientId: "1",
    clientName: "Law Firm of Smith & Co",
    metric: "Cost",
    expectedValue: 650,
    actualValue: 1420,
    deviationPercent: 118,
    severity: "critical",
    detectedAt: "2026-02-18T06:00:00Z",
    description:
      "Daily spend is 118% above expected levels. Possible cause: broad match keywords triggering on irrelevant queries.",
  },
  {
    id: "an2",
    clientId: "2",
    clientName: "Apex Outdoor Gear",
    metric: "Conversion Rate",
    expectedValue: 3.5,
    actualValue: 5.8,
    deviationPercent: 66,
    severity: "info",
    detectedAt: "2026-02-17T12:00:00Z",
    description:
      "Conversion rate significantly above baseline. Likely driven by seasonal demand for outdoor gear.",
  },
  {
    id: "an3",
    clientId: "3",
    clientName: "TechFlow SaaS",
    metric: "CTR",
    expectedValue: 4.2,
    actualValue: 1.8,
    deviationPercent: -57,
    severity: "warning",
    detectedAt: "2026-02-16T18:00:00Z",
    description:
      "Click-through rate has dropped significantly. Ad fatigue or increased competition may be factors.",
  },
  {
    id: "an4",
    clientId: "1",
    clientName: "Law Firm of Smith & Co",
    metric: "CPC",
    expectedValue: 12.5,
    actualValue: 22.3,
    deviationPercent: 78,
    severity: "warning",
    detectedAt: "2026-02-15T09:00:00Z",
    description:
      "CPC has spiked well above historical average. New competitor may be bidding aggressively.",
  },
];
