import type { DailyMetrics, AnomalyDetection } from "@/types";

interface AnomalyConfig {
  /** Number of standard deviations to trigger a warning */
  warningThreshold: number;
  /** Number of standard deviations to trigger a critical alert */
  criticalThreshold: number;
  /** Minimum number of data points needed for analysis */
  minDataPoints: number;
}

const DEFAULT_CONFIG: AnomalyConfig = {
  warningThreshold: 2,
  criticalThreshold: 3,
  minDataPoints: 7,
};

function calculateStats(values: number[]): {
  mean: number;
  stdDev: number;
} {
  const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
  const squaredDiffs = values.map((v) => Math.pow(v - mean, 2));
  const variance =
    squaredDiffs.reduce((sum, v) => sum + v, 0) / values.length;
  return { mean, stdDev: Math.sqrt(variance) };
}

/**
 * Detect anomalies in daily metrics using z-score analysis.
 * Compares the most recent day's metrics against the historical baseline.
 */
export function detectAnomalies(
  metrics: DailyMetrics[],
  clientId: string,
  clientName: string,
  config: AnomalyConfig = DEFAULT_CONFIG
): AnomalyDetection[] {
  if (metrics.length < config.minDataPoints) {
    return [];
  }

  const anomalies: AnomalyDetection[] = [];
  const latest = metrics[metrics.length - 1];
  const historical = metrics.slice(0, -1);

  const metricsToCheck: {
    key: keyof DailyMetrics;
    label: string;
  }[] = [
    { key: "cost", label: "Cost" },
    { key: "conversions", label: "Conversions" },
    { key: "clicks", label: "Clicks" },
    { key: "ctr", label: "CTR" },
    { key: "cpc", label: "CPC" },
    { key: "conversionRate", label: "Conversion Rate" },
  ];

  for (const metric of metricsToCheck) {
    const values = historical.map((m) => m[metric.key] as number);
    const { mean, stdDev } = calculateStats(values);

    if (stdDev === 0) continue;

    const currentValue = latest[metric.key] as number;
    const zScore = (currentValue - mean) / stdDev;
    const absZScore = Math.abs(zScore);

    if (absZScore >= config.warningThreshold) {
      const deviationPercent = Math.round(((currentValue - mean) / mean) * 100);
      const severity =
        absZScore >= config.criticalThreshold ? "critical" : "warning";

      const direction = currentValue > mean ? "above" : "below";
      const description = `${metric.label} is ${Math.abs(deviationPercent)}% ${direction} the ${historical.length}-day average. Current: ${formatMetricValue(metric.key, currentValue)}, Average: ${formatMetricValue(metric.key, mean)}.`;

      anomalies.push({
        id: `anomaly-${clientId}-${metric.key}-${latest.date}`,
        clientId,
        clientName,
        metric: metric.label,
        expectedValue: Math.round(mean * 100) / 100,
        actualValue: Math.round(currentValue * 100) / 100,
        deviationPercent,
        severity,
        detectedAt: new Date().toISOString(),
        description,
      });
    }
  }

  // Sort by severity (critical first) then by absolute deviation
  return anomalies.sort((a, b) => {
    if (a.severity !== b.severity) {
      return a.severity === "critical" ? -1 : 1;
    }
    return Math.abs(b.deviationPercent) - Math.abs(a.deviationPercent);
  });
}

function formatMetricValue(key: string, value: number): string {
  switch (key) {
    case "cost":
    case "cpc":
      return `$${value.toFixed(2)}`;
    case "ctr":
    case "conversionRate":
      return `${value.toFixed(2)}%`;
    default:
      return value.toFixed(0);
  }
}

/**
 * Calculate a health score (0-100) based on recent anomalies and metrics trends.
 */
export function calculateHealthScore(
  metrics: DailyMetrics[],
  anomalies: AnomalyDetection[]
): number {
  let score = 100;

  // Deduct points for anomalies
  for (const anomaly of anomalies) {
    if (anomaly.severity === "critical") {
      score -= 25;
    } else if (anomaly.severity === "warning") {
      score -= 10;
    }
  }

  // Check recent trends (last 7 days vs previous 7)
  if (metrics.length >= 14) {
    const recent = metrics.slice(-7);
    const previous = metrics.slice(-14, -7);

    const recentConvRate =
      recent.reduce((s, m) => s + m.conversionRate, 0) / 7;
    const prevConvRate =
      previous.reduce((s, m) => s + m.conversionRate, 0) / 7;

    if (recentConvRate < prevConvRate * 0.8) {
      score -= 15; // Significant conversion rate decline
    }

    const recentCost = recent.reduce((s, m) => s + m.cost, 0);
    const prevCost = previous.reduce((s, m) => s + m.cost, 0);

    if (recentCost > prevCost * 1.3) {
      score -= 10; // Significant cost increase
    }
  }

  return Math.max(0, Math.min(100, score));
}
