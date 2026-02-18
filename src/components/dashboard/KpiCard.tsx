"use client";

import Card from "@/components/ui/Card";
import SparkLine from "@/components/charts/SparkLine";

interface KpiCardProps {
  label: string;
  value: string;
  trend?: number[];
  trendColor?: string;
  change?: number;
}

export default function KpiCard({
  label,
  value,
  trend,
  trendColor = "#6366f1",
  change,
}: KpiCardProps) {
  return (
    <Card>
      <p className="text-xs text-muted font-medium uppercase tracking-wide mb-1">
        {label}
      </p>
      <div className="flex items-end justify-between">
        <div>
          <p className="text-2xl font-bold text-foreground">{value}</p>
          {change !== undefined && (
            <p
              className={`text-xs mt-1 ${change >= 0 ? "text-emerald-400" : "text-red-400"}`}
            >
              {change >= 0 ? "+" : ""}
              {change.toFixed(1)}% vs last period
            </p>
          )}
        </div>
        {trend && (
          <div className="w-24 h-10">
            <SparkLine data={trend} color={trendColor} />
          </div>
        )}
      </div>
    </Card>
  );
}
