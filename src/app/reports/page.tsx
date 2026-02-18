"use client";

import Header from "@/components/layout/Header";
import Card from "@/components/ui/Card";
import PerformanceChart from "@/components/charts/PerformanceChart";
import { mockClients, generateDailyMetrics } from "@/lib/mock-data";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { Download, Calendar, Filter } from "lucide-react";
import { useState } from "react";

export default function ReportsPage() {
  const [selectedClient, setSelectedClient] = useState<string>("all");
  const [dateRange, setDateRange] = useState("30d");

  const days =
    dateRange === "7d" ? 7 : dateRange === "14d" ? 14 : dateRange === "90d" ? 90 : 30;
  const dailyMetrics = generateDailyMetrics(days);

  const totalCost = dailyMetrics.reduce((s, d) => s + d.cost, 0);
  const totalConversions = dailyMetrics.reduce((s, d) => s + d.conversions, 0);
  const totalClicks = dailyMetrics.reduce((s, d) => s + d.clicks, 0);
  const totalImpressions = dailyMetrics.reduce((s, d) => s + d.impressions, 0);
  const avgCtr = (totalClicks / totalImpressions) * 100;
  const avgCpc = totalCost / totalClicks;

  return (
    <div>
      <Header title="Reports" subtitle="Analyze performance across accounts" />

      <div className="p-8">
        {/* Controls */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1 px-3 py-2 rounded-lg bg-card border border-border">
              <Filter className="w-4 h-4 text-muted" />
              <select
                value={selectedClient}
                onChange={(e) => setSelectedClient(e.target.value)}
                className="bg-transparent text-sm text-foreground outline-none"
              >
                <option value="all">All Clients</option>
                {mockClients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-1 px-3 py-2 rounded-lg bg-card border border-border">
              <Calendar className="w-4 h-4 text-muted" />
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="bg-transparent text-sm text-foreground outline-none"
              >
                <option value="7d">Last 7 days</option>
                <option value="14d">Last 14 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
              </select>
            </div>
          </div>

          <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors">
            <Download className="w-4 h-4" />
            Export CSV
          </button>
        </div>

        {/* KPI summary */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <Card>
            <p className="text-xs text-muted mb-1">Cost</p>
            <p className="text-lg font-bold text-foreground">
              {formatCurrency(totalCost)}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted mb-1">Conversions</p>
            <p className="text-lg font-bold text-foreground">
              {totalConversions.toLocaleString()}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted mb-1">Clicks</p>
            <p className="text-lg font-bold text-foreground">
              {totalClicks.toLocaleString()}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted mb-1">Impressions</p>
            <p className="text-lg font-bold text-foreground">
              {totalImpressions.toLocaleString()}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted mb-1">Avg CTR</p>
            <p className="text-lg font-bold text-foreground">
              {formatPercent(avgCtr)}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted mb-1">Avg CPC</p>
            <p className="text-lg font-bold text-foreground">
              {formatCurrency(avgCpc)}
            </p>
          </Card>
        </div>

        {/* Chart */}
        <Card>
          <h3 className="text-sm font-medium text-foreground mb-4">
            Performance Over Time
          </h3>
          <PerformanceChart data={dailyMetrics} />
        </Card>
      </div>
    </div>
  );
}
