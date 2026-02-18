"use client";

import Link from "next/link";
import { Client } from "@/types";
import StatusBadge from "@/components/ui/StatusBadge";
import {
  formatCurrency,
  getBudgetPacingColor,
  getBudgetPacingLabel,
} from "@/lib/utils";
import { ChevronRight } from "lucide-react";

interface ClientTableProps {
  clients: Client[];
}

function getAlertLabel(client: Client): { label: string; type: string } {
  const unresolvedAlerts = client.alerts.filter((a) => !a.resolved);
  if (unresolvedAlerts.length === 0) return { label: "None", type: "none" };

  const hasCritical = unresolvedAlerts.some((a) => a.severity === "critical");
  const type = unresolvedAlerts[0].type;
  const labels: Record<string, string> = {
    budget: "Budget Alert",
    performance: "Performance Alert",
    campaign: "Campaign Alert",
    anomaly: "Anomaly Alert",
  };

  return {
    label: labels[type] || "Alert",
    type: hasCritical ? "critical" : "warning",
  };
}

export default function ClientTable({ clients }: ClientTableProps) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-sm font-medium text-foreground">
          Client Priority List
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                Client
              </th>
              <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                Health Status
              </th>
              <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                Alerts
              </th>
              <th className="text-left text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                Budget Pacing
              </th>
              <th className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                CPA (30d)
              </th>
              <th className="text-right text-xs font-medium text-muted uppercase tracking-wide px-5 py-3">
                ROAS
              </th>
              <th className="px-3 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {clients.map((client) => {
              const alertInfo = getAlertLabel(client);

              return (
                <tr
                  key={client.id}
                  className="border-b border-border/50 hover:bg-card-hover transition-colors"
                >
                  <td className="px-5 py-4">
                    <Link
                      href={`/clients/${client.id}`}
                      className="text-sm font-medium text-foreground hover:text-accent transition-colors"
                    >
                      {client.name}
                    </Link>
                    {client.industry && (
                      <p className="text-xs text-muted mt-0.5">
                        {client.industry}
                      </p>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <StatusBadge
                      label={client.healthStatus.toUpperCase()}
                      variant="health"
                      status={client.healthStatus}
                    />
                  </td>
                  <td className="px-5 py-4">
                    {alertInfo.type !== "none" ? (
                      <StatusBadge
                        label={alertInfo.label}
                        variant="severity"
                        status={alertInfo.type}
                      />
                    ) : (
                      <span className="text-xs text-muted">None</span>
                    )}
                  </td>
                  <td className="px-5 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-background rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            client.budgetPacing > 110
                              ? "bg-red-500"
                              : client.budgetPacing >= 85
                                ? "bg-emerald-500"
                                : "bg-amber-500"
                          }`}
                          style={{
                            width: `${Math.min(client.budgetPacing, 100)}%`,
                          }}
                        />
                      </div>
                      <span
                        className={`text-xs font-medium ${getBudgetPacingColor(client.budgetPacing)}`}
                      >
                        {client.budgetPacing}%
                      </span>
                      <span className="text-xs text-muted hidden lg:inline">
                        {getBudgetPacingLabel(client.budgetPacing)}
                      </span>
                    </div>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span className="text-sm text-foreground">
                      {formatCurrency(client.cpa30d)}
                    </span>
                  </td>
                  <td className="px-5 py-4 text-right">
                    <span
                      className={`text-sm font-medium ${
                        client.roas >= 3
                          ? "text-emerald-400"
                          : client.roas >= 2
                            ? "text-amber-400"
                            : "text-red-400"
                      }`}
                    >
                      {client.roas}x
                    </span>
                  </td>
                  <td className="px-3 py-4">
                    <Link href={`/clients/${client.id}`}>
                      <ChevronRight className="w-4 h-4 text-muted" />
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
