"use client";

import { use } from "react";
import Header from "@/components/layout/Header";
import KpiCard from "@/components/dashboard/KpiCard";
import PerformanceChart from "@/components/charts/PerformanceChart";
import BudgetPacing from "@/components/dashboard/BudgetPacing";
import AIAnalysis from "@/components/dashboard/AIAnalysis";
import QuickStats from "@/components/dashboard/QuickStats";
import Card from "@/components/ui/Card";
import { mockClients, generateDailyMetrics } from "@/lib/mock-data";
import { formatCurrency, formatPercent } from "@/lib/utils";

export default function ClientDashboard({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const client = mockClients.find((c) => c.id === id) || mockClients[1];
  const dailyMetrics = generateDailyMetrics(30);

  // Calculate KPIs from daily metrics
  const totalCost = dailyMetrics.reduce((sum, d) => sum + d.cost, 0);
  const totalConversions = dailyMetrics.reduce(
    (sum, d) => sum + d.conversions,
    0
  );
  const totalClicks = dailyMetrics.reduce((sum, d) => sum + d.clicks, 0);
  const totalImpressions = dailyMetrics.reduce(
    (sum, d) => sum + d.impressions,
    0
  );
  const avgCtr = (totalClicks / totalImpressions) * 100;
  const avgCpc = totalCost / totalClicks;
  const conversionRate = (totalConversions / totalClicks) * 100;
  const costPerConversion = totalCost / totalConversions;

  // Sparkline data
  const costTrend = dailyMetrics.map((d) => d.cost);
  const convTrend = dailyMetrics.map((d) => d.conversions);
  const cpcTrend = dailyMetrics.map((d) => d.cpc);
  const ctrTrend = dailyMetrics.map((d) => d.ctr);

  return (
    <div>
      <Header title={client.name} subtitle={`Customer ID: ${client.customerId}`} />

      <div className="p-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <KpiCard
            label="Total Cost"
            value={formatCurrency(totalCost)}
            trend={costTrend}
            trendColor="#6366f1"
            change={-3.2}
          />
          <KpiCard
            label="Conversions"
            value={totalConversions.toLocaleString()}
            trend={convTrend}
            trendColor="#22c55e"
            change={12.5}
          />
          <KpiCard
            label="Cost Per Conv."
            value={`$${costPerConversion.toFixed(2)}`}
            trend={cpcTrend}
            trendColor="#f59e0b"
            change={-8.1}
          />
          <KpiCard
            label="Click-Through Rate"
            value={formatPercent(avgCtr)}
            trend={ctrTrend}
            trendColor="#06b6d4"
            change={2.4}
          />
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - chart + budget */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <h3 className="text-sm font-medium text-foreground mb-4">
                Performance Trend
              </h3>
              <PerformanceChart data={dailyMetrics} />
            </Card>

            <BudgetPacing
              monthlyBudget={client.monthlyBudget}
              monthlySpend={client.monthlySpend}
              pacing={client.budgetPacing}
            />

            <AIAnalysis clientName={client.name} />
          </div>

          {/* Right column - quick stats */}
          <div className="space-y-6">
            <QuickStats avgCpc={avgCpc} conversionRate={conversionRate} />

            {/* Recent Alerts */}
            <Card>
              <h3 className="text-sm font-medium text-foreground mb-4">
                Recent Alerts
              </h3>
              <div className="space-y-3">
                {client.alerts.length > 0 ? (
                  client.alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`p-3 rounded-lg border text-sm ${
                        alert.severity === "critical"
                          ? "bg-red-400/5 border-red-400/20 text-red-300"
                          : alert.severity === "warning"
                            ? "bg-amber-400/5 border-amber-400/20 text-amber-300"
                            : "bg-blue-400/5 border-blue-400/20 text-blue-300"
                      }`}
                    >
                      {alert.message}
                      <p className="text-xs opacity-60 mt-1">
                        {new Date(alert.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted">No active alerts</p>
                )}
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
