"use client";

import Header from "@/components/layout/Header";
import Card from "@/components/ui/Card";
import StatusBadge from "@/components/ui/StatusBadge";
import { mockAnomalies } from "@/lib/mock-data";
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Clock,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";

export default function AnomaliesPage() {
  const criticalCount = mockAnomalies.filter(
    (a) => a.severity === "critical"
  ).length;
  const warningCount = mockAnomalies.filter(
    (a) => a.severity === "warning"
  ).length;

  return (
    <div>
      <Header
        title="Anomaly Detection"
        subtitle="AI-powered monitoring for unusual account activity"
      />

      <div className="p-8">
        {/* Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/10">
                <AlertTriangle className="w-5 h-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  Critical Anomalies
                </p>
                <p className="text-2xl font-bold text-red-400">
                  {criticalCount}
                </p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-500/10">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  Warnings
                </p>
                <p className="text-2xl font-bold text-amber-400">
                  {warningCount}
                </p>
              </div>
            </div>
          </Card>
          <Card>
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-emerald-500/10">
                <Clock className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-muted font-medium uppercase tracking-wide">
                  Last Scan
                </p>
                <p className="text-lg font-bold text-foreground">
                  2 hours ago
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Anomaly list */}
        <div className="space-y-4">
          {mockAnomalies.map((anomaly) => (
            <Card key={anomaly.id}>
              <div className="flex items-start gap-4">
                <div
                  className={`flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg ${
                    anomaly.severity === "critical"
                      ? "bg-red-500/10"
                      : anomaly.severity === "warning"
                        ? "bg-amber-500/10"
                        : "bg-blue-500/10"
                  }`}
                >
                  {anomaly.deviationPercent > 0 ? (
                    <TrendingUp
                      className={`w-5 h-5 ${
                        anomaly.severity === "critical"
                          ? "text-red-400"
                          : anomaly.severity === "warning"
                            ? "text-amber-400"
                            : "text-blue-400"
                      }`}
                    />
                  ) : (
                    <TrendingDown
                      className={`w-5 h-5 ${
                        anomaly.severity === "critical"
                          ? "text-red-400"
                          : anomaly.severity === "warning"
                            ? "text-amber-400"
                            : "text-blue-400"
                      }`}
                    />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <StatusBadge
                      label={anomaly.severity.toUpperCase()}
                      variant="severity"
                      status={anomaly.severity}
                    />
                    <span className="text-xs text-muted">
                      {anomaly.metric}
                    </span>
                    <span className="text-xs text-muted">
                      {new Date(anomaly.detectedAt).toLocaleDateString()}
                    </span>
                  </div>

                  <Link
                    href={`/clients/${anomaly.clientId}`}
                    className="text-sm font-medium text-foreground hover:text-accent transition-colors"
                  >
                    {anomaly.clientName}
                  </Link>

                  <p className="text-sm text-foreground/70 mt-1">
                    {anomaly.description}
                  </p>

                  {/* Metrics comparison */}
                  <div className="flex items-center gap-6 mt-3">
                    <div>
                      <p className="text-xs text-muted">Expected</p>
                      <p className="text-sm font-medium text-foreground">
                        {anomaly.metric === "Cost" || anomaly.metric === "CPC"
                          ? `$${anomaly.expectedValue.toFixed(2)}`
                          : `${anomaly.expectedValue}%`}
                      </p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-muted" />
                    <div>
                      <p className="text-xs text-muted">Actual</p>
                      <p
                        className={`text-sm font-medium ${
                          anomaly.severity === "critical"
                            ? "text-red-400"
                            : anomaly.severity === "warning"
                              ? "text-amber-400"
                              : "text-blue-400"
                        }`}
                      >
                        {anomaly.metric === "Cost" || anomaly.metric === "CPC"
                          ? `$${anomaly.actualValue.toFixed(2)}`
                          : `${anomaly.actualValue}%`}
                      </p>
                    </div>
                    <div className="ml-2">
                      <p className="text-xs text-muted">Deviation</p>
                      <p
                        className={`text-sm font-bold ${
                          anomaly.deviationPercent > 0
                            ? "text-red-400"
                            : "text-emerald-400"
                        }`}
                      >
                        {anomaly.deviationPercent > 0 ? "+" : ""}
                        {anomaly.deviationPercent}%
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
