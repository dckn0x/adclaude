import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: value < 10 ? 2 : 0,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(value);
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function getHealthColor(status: string): string {
  switch (status) {
    case "active":
      return "text-emerald-400";
    case "warning":
      return "text-amber-400";
    case "error":
      return "text-red-400";
    case "paused":
      return "text-gray-400";
    default:
      return "text-gray-400";
  }
}

export function getHealthBg(status: string): string {
  switch (status) {
    case "active":
      return "bg-emerald-400/10 text-emerald-400 border-emerald-400/20";
    case "warning":
      return "bg-amber-400/10 text-amber-400 border-amber-400/20";
    case "error":
      return "bg-red-400/10 text-red-400 border-red-400/20";
    case "paused":
      return "bg-gray-400/10 text-gray-400 border-gray-400/20";
    default:
      return "bg-gray-400/10 text-gray-400 border-gray-400/20";
  }
}

export function getSeverityColor(severity: string): string {
  switch (severity) {
    case "critical":
      return "text-red-400 bg-red-400/10 border-red-400/20";
    case "warning":
      return "text-amber-400 bg-amber-400/10 border-amber-400/20";
    case "info":
      return "text-blue-400 bg-blue-400/10 border-blue-400/20";
    default:
      return "text-gray-400 bg-gray-400/10 border-gray-400/20";
  }
}

export function getBudgetPacingColor(pacing: number): string {
  if (pacing > 110) return "text-red-400";
  if (pacing > 100) return "text-amber-400";
  if (pacing >= 85) return "text-emerald-400";
  if (pacing >= 70) return "text-amber-400";
  return "text-red-400";
}

export function getBudgetPacingLabel(pacing: number): string {
  if (pacing > 110) return "Over Budget";
  if (pacing > 100) return "Slightly Over";
  if (pacing >= 85) return "On Track";
  if (pacing >= 70) return "Under-pace";
  return "Significantly Under";
}
