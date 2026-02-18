"use client";

import { useState } from "react";
import Header from "@/components/layout/Header";
import Card from "@/components/ui/Card";
import StatusBadge from "@/components/ui/StatusBadge";
import { mockCampaigns, mockClients } from "@/lib/mock-data";
import { formatCurrency, formatPercent } from "@/lib/utils";
import {
  Search,
  Filter,
  ArrowUpDown,
  Pause,
  Play,
  BarChart3,
} from "lucide-react";
import { Campaign } from "@/types";

const typeLabels: Record<string, string> = {
  search: "Search",
  display: "Display",
  shopping: "Shopping",
  video: "Video",
  pmax: "Performance Max",
};

export default function CampaignsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortField, setSortField] = useState<keyof Campaign>("cost");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  // For now, show all campaigns across all clients
  const allCampaigns = mockCampaigns;

  const filteredCampaigns = allCampaigns
    .filter((c) => {
      if (searchQuery && !c.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (statusFilter !== "all" && c.status !== statusFilter) return false;
      return true;
    })
    .sort((a, b) => {
      const aVal = a[sortField] as number;
      const bVal = b[sortField] as number;
      return sortDir === "desc" ? bVal - aVal : aVal - bVal;
    });

  const totalSpend = allCampaigns.reduce((s, c) => s + c.cost, 0);
  const totalConversions = allCampaigns.reduce((s, c) => s + c.conversions, 0);
  const activeCampaigns = allCampaigns.filter(
    (c) => c.status === "enabled"
  ).length;

  function handleSort(field: keyof Campaign) {
    if (sortField === field) {
      setSortDir(sortDir === "desc" ? "asc" : "desc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
  }

  return (
    <div>
      <Header
        title="Campaigns"
        subtitle="Manage and monitor campaign performance"
      />

      <div className="p-8">
        {/* Summary row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <p className="text-xs text-muted font-medium uppercase tracking-wide">
              Active Campaigns
            </p>
            <p className="text-2xl font-bold text-foreground mt-1">
              {activeCampaigns}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted font-medium uppercase tracking-wide">
              Total Spend
            </p>
            <p className="text-2xl font-bold text-foreground mt-1">
              {formatCurrency(totalSpend)}
            </p>
          </Card>
          <Card>
            <p className="text-xs text-muted font-medium uppercase tracking-wide">
              Total Conversions
            </p>
            <p className="text-2xl font-bold text-foreground mt-1">
              {totalConversions.toLocaleString()}
            </p>
          </Card>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-card border border-border flex-1 max-w-sm">
            <Search className="w-4 h-4 text-muted" />
            <input
              type="text"
              placeholder="Search campaigns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-transparent text-sm text-foreground placeholder-muted outline-none w-full"
            />
          </div>

          <div className="flex items-center gap-1 px-3 py-2 rounded-lg bg-card border border-border">
            <Filter className="w-4 h-4 text-muted" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-sm text-foreground outline-none"
            >
              <option value="all">All Status</option>
              <option value="enabled">Enabled</option>
              <option value="paused">Paused</option>
            </select>
          </div>
        </div>

        {/* Campaigns table */}
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                    Campaign
                  </th>
                  <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                    Status
                  </th>
                  <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                    Type
                  </th>
                  <th
                    className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3 cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("cost")}
                  >
                    <span className="flex items-center justify-end gap-1">
                      Cost
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th
                    className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3 cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("conversions")}
                  >
                    <span className="flex items-center justify-end gap-1">
                      Conv.
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th
                    className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3 cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("ctr")}
                  >
                    <span className="flex items-center justify-end gap-1">
                      CTR
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th
                    className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3 cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("cpc")}
                  >
                    <span className="flex items-center justify-end gap-1">
                      CPC
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th
                    className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3 cursor-pointer hover:text-foreground"
                    onClick={() => handleSort("roas")}
                  >
                    <span className="flex items-center justify-end gap-1">
                      ROAS
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredCampaigns.map((campaign) => (
                  <tr
                    key={campaign.id}
                    className="border-b border-border/50 hover:bg-card-hover transition-colors"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        <BarChart3 className="w-4 h-4 text-muted" />
                        <span className="text-sm font-medium text-foreground">
                          {campaign.name}
                        </span>
                      </div>
                      <p className="text-xs text-muted mt-0.5 ml-6">
                        {
                          mockClients.find((c) => c.id === campaign.clientId)
                            ?.name
                        }
                      </p>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-1.5">
                        {campaign.status === "enabled" ? (
                          <Play className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <Pause className="w-3 h-3 text-gray-400" />
                        )}
                        <StatusBadge
                          label={campaign.status.toUpperCase()}
                          variant="health"
                          status={
                            campaign.status === "enabled" ? "active" : "paused"
                          }
                        />
                      </div>
                    </td>
                    <td className="px-5 py-4">
                      <span className="text-xs text-muted bg-background px-2 py-1 rounded">
                        {typeLabels[campaign.type]}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right text-sm text-foreground">
                      {formatCurrency(campaign.cost)}
                    </td>
                    <td className="px-5 py-4 text-right text-sm text-foreground">
                      {campaign.conversions}
                    </td>
                    <td className="px-5 py-4 text-right text-sm text-foreground">
                      {formatPercent(campaign.ctr)}
                    </td>
                    <td className="px-5 py-4 text-right text-sm text-foreground">
                      {formatCurrency(campaign.cpc)}
                    </td>
                    <td className="px-5 py-4 text-right">
                      <span
                        className={`text-sm font-medium ${
                          campaign.roas >= 4
                            ? "text-emerald-400"
                            : campaign.roas >= 2
                              ? "text-amber-400"
                              : campaign.roas > 0
                                ? "text-red-400"
                                : "text-muted"
                        }`}
                      >
                        {campaign.roas > 0 ? `${campaign.roas}x` : "—"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
