import { NextResponse } from "next/server";
import { detectAnomalies } from "@/lib/anomaly-detection";
import { mockClients, generateDailyMetrics } from "@/lib/mock-data";

export async function GET() {
  // In production, this would pull real metrics from the Google Ads API.
  // For now, demonstrate anomaly detection with generated metrics.
  const allAnomalies = [];

  for (const client of mockClients) {
    const metrics = generateDailyMetrics(30);
    const anomalies = detectAnomalies(metrics, client.id, client.name);
    allAnomalies.push(...anomalies);
  }

  // Sort by severity, then by detection time
  allAnomalies.sort((a, b) => {
    const severityOrder = { critical: 0, warning: 1, info: 2 };
    if (severityOrder[a.severity] !== severityOrder[b.severity]) {
      return severityOrder[a.severity] - severityOrder[b.severity];
    }
    return (
      new Date(b.detectedAt).getTime() - new Date(a.detectedAt).getTime()
    );
  });

  return NextResponse.json({ anomalies: allAnomalies });
}
