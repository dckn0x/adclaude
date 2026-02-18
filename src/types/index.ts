export interface Client {
  id: string;
  name: string;
  customerId: string; // Google Ads customer ID
  healthStatus: "active" | "warning" | "error" | "paused";
  alerts: Alert[];
  budgetPacing: number; // percentage 0-200+
  monthlyBudget: number;
  monthlySpend: number;
  cpa30d: number;
  roas: number;
  industry?: string;
  createdAt: string;
}

export interface Alert {
  id: string;
  clientId: string;
  type: "budget" | "performance" | "campaign" | "anomaly";
  severity: "critical" | "warning" | "info";
  message: string;
  createdAt: string;
  resolved: boolean;
}

export interface Campaign {
  id: string;
  clientId: string;
  name: string;
  status: "enabled" | "paused" | "removed";
  type: "search" | "display" | "shopping" | "video" | "pmax";
  budget: number;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  cost: number;
  ctr: number;
  cpc: number;
  conversionRate: number;
  roas: number;
}

export interface DailyMetrics {
  date: string;
  cost: number;
  conversions: number;
  clicks: number;
  impressions: number;
  ctr: number;
  cpc: number;
  conversionRate: number;
}

export interface ClientDashboard {
  client: Client;
  kpis: {
    totalCost: number;
    conversions: number;
    costPerConversion: number;
    ctr: number;
    avgCpc: number;
    conversionRate: number;
  };
  dailyMetrics: DailyMetrics[];
  campaigns: Campaign[];
  recentAlerts: Alert[];
}

export interface AnomalyDetection {
  id: string;
  clientId: string;
  clientName: string;
  metric: string;
  expectedValue: number;
  actualValue: number;
  deviationPercent: number;
  severity: "critical" | "warning" | "info";
  detectedAt: string;
  description: string;
}

export interface AIAnalysis {
  summary: string;
  recommendations: {
    priority: "high" | "medium" | "low";
    category: string;
    description: string;
    estimatedImpact: string;
  }[];
  generatedAt: string;
}

export interface GoogleAdsConfig {
  clientId: string;
  clientSecret: string;
  developerToken: string;
  refreshToken: string;
  loginCustomerId?: string;
}
