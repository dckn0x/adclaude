"use client";

import Header from "@/components/layout/Header";
import Card from "@/components/ui/Card";
import ClientTable from "@/components/dashboard/ClientTable";
import { mockClients, mockAlerts } from "@/lib/mock-data";
import { formatCurrency } from "@/lib/utils";
import { AlertOctagon, TrendingDown, DollarSign, Plus } from "lucide-react";
import Link from "next/link";

export default function AgencyOverview() {
  const criticalIssues = mockAlerts.filter(
    (a) => a.severity === "critical" && !a.resolved
  ).length;
  const offPaceBudgets = mockClients.filter(
    (c) => c.budgetPacing > 110 || c.budgetPacing < 70
  ).length;
  const totalMonthlySpend = mockClients.reduce(
    (sum, c) => sum + c.monthlySpend,
    0
  );

  return (
    <div>
      <Header
        title="Agency Overview"
        subtitle="Monitor all client accounts at a glance"
      />

      <div className="p-8">
        {/* Summary cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/10">
                <AlertOctagon className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  Critical Issues
                </p>
                <p className="text-2xl font-bold text-red-400">
                  {criticalIssues}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-500/10">
                <TrendingDown className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  Off-Pace Budgets
                </p>
                <p className="text-2xl font-bold text-amber-400">
                  {offPaceBudgets}
                </p>
              </div>
            </div>
          </Card>

          <Card>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10">
                <DollarSign className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  Total Monthly Spend
                </p>
                <p className="text-2xl font-bold text-foreground">
                  {formatCurrency(totalMonthlySpend)}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Client table */}
        <ClientTable clients={mockClients} />

        {/* Add client button */}
        <div className="mt-4 flex justify-end">
          <Link
            href="/settings"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors"
          >
            <Plus className="w-4 h-4" />
            Connect Account
          </Link>
        </div>
      </div>
    </div>
  );
}
