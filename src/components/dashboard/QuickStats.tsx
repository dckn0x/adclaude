"use client";

import Card from "@/components/ui/Card";
import { DollarSign, Target } from "lucide-react";

interface QuickStatsProps {
  avgCpc: number;
  conversionRate: number;
}

export default function QuickStats({ avgCpc, conversionRate }: QuickStatsProps) {
  return (
    <Card>
      <h3 className="text-sm font-medium text-foreground mb-4">Quick Stats</h3>
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-500/10">
            <DollarSign className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <p className="text-xs text-muted">Avg CPC</p>
            <p className="text-lg font-semibold text-foreground">
              ${avgCpc.toFixed(2)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-emerald-500/10">
            <Target className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs text-muted">Conversion Rate</p>
            <p className="text-lg font-semibold text-foreground">
              {conversionRate.toFixed(1)}%
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
