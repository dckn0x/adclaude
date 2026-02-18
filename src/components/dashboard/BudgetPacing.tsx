"use client";

import Card from "@/components/ui/Card";
import { formatCurrency, getBudgetPacingColor, getBudgetPacingLabel } from "@/lib/utils";
import { AlertTriangle, CheckCircle } from "lucide-react";

interface BudgetPacingProps {
  monthlyBudget: number;
  monthlySpend: number;
  pacing: number;
}

export default function BudgetPacing({
  monthlyBudget,
  monthlySpend,
  pacing,
}: BudgetPacingProps) {
  const progressWidth = Math.min(pacing, 150);
  const isOverBudget = pacing > 100;
  const remaining = monthlyBudget - monthlySpend;

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-foreground">
          Monthly Budget Pacing
        </h3>
        {isOverBudget ? (
          <div className="flex items-center gap-1.5 text-xs text-red-400">
            <AlertTriangle className="w-3.5 h-3.5" />
            Overspend Warning
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-xs text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5" />
            {getBudgetPacingLabel(pacing)}
          </div>
        )}
      </div>

      {/* Progress bar */}
      <div className="relative h-3 bg-background rounded-full overflow-hidden mb-3">
        <div
          className={`absolute left-0 top-0 h-full rounded-full transition-all ${
            isOverBudget ? "bg-red-500" : pacing >= 85 ? "bg-emerald-500" : "bg-amber-500"
          }`}
          style={{ width: `${Math.min(progressWidth, 100)}%` }}
        />
        {isOverBudget && (
          <div
            className="absolute top-0 h-full bg-red-500/40 rounded-r-full"
            style={{
              left: "100%",
              width: `${Math.min(progressWidth - 100, 50)}%`,
              marginLeft: "-1px",
            }}
          />
        )}
        {/* Budget line marker */}
        <div className="absolute right-0 top-0 w-0.5 h-full bg-foreground/30" />
      </div>

      {/* Labels */}
      <div className="flex items-center justify-between text-sm">
        <div>
          <span className="text-muted">Spent: </span>
          <span className="font-medium text-foreground">
            {formatCurrency(monthlySpend)}
          </span>
        </div>
        <div>
          <span className="text-muted">Budget: </span>
          <span className="font-medium text-foreground">
            {formatCurrency(monthlyBudget)}
          </span>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        <span className={getBudgetPacingColor(pacing)}>
          {pacing}% of budget used
        </span>
        <span className={remaining < 0 ? "text-red-400" : "text-muted"}>
          {remaining < 0
            ? `${formatCurrency(Math.abs(remaining))} over`
            : `${formatCurrency(remaining)} remaining`}
        </span>
      </div>
    </Card>
  );
}
