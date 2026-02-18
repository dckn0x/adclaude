import { GoogleAdsApi, enums } from "google-ads-api";
import type {
  Client,
  Campaign,
  DailyMetrics,
  GoogleAdsConfig,
} from "@/types";

let apiClient: GoogleAdsApi | null = null;

export function initializeGoogleAdsClient(config: GoogleAdsConfig) {
  apiClient = new GoogleAdsApi({
    client_id: config.clientId,
    client_secret: config.clientSecret,
    developer_token: config.developerToken,
  });
  return apiClient;
}

export function getClient(config: GoogleAdsConfig) {
  if (!apiClient) {
    apiClient = initializeGoogleAdsClient(config);
  }
  return apiClient;
}

export function getCustomer(
  config: GoogleAdsConfig,
  customerId: string
) {
  const client = getClient(config);
  return client.Customer({
    customer_id: customerId.replace(/-/g, ""),
    refresh_token: config.refreshToken,
    login_customer_id: config.loginCustomerId?.replace(/-/g, ""),
  });
}

/**
 * Fetch all accessible customer accounts (for MCC/manager accounts)
 */
export async function listAccessibleCustomers(
  config: GoogleAdsConfig
): Promise<string[]> {
  const client = getClient(config);
  const response = await client.listAccessibleCustomers(config.refreshToken);
  return response.resource_names ?? [];
}

/**
 * Fetch account-level metrics for a customer over a date range
 */
export async function fetchAccountMetrics(
  config: GoogleAdsConfig,
  customerId: string,
  startDate: string,
  endDate: string
): Promise<DailyMetrics[]> {
  const customer = getCustomer(config, customerId);

  const results = await customer.query(`
    SELECT
      segments.date,
      metrics.cost_micros,
      metrics.conversions,
      metrics.clicks,
      metrics.impressions,
      metrics.ctr,
      metrics.average_cpc,
      metrics.conversions_from_interactions_rate
    FROM customer
    WHERE segments.date BETWEEN '${startDate}' AND '${endDate}'
    ORDER BY segments.date ASC
  `);

  return results.map((row) => ({
    date: row.segments?.date || "",
    cost: (Number(row.metrics?.cost_micros) || 0) / 1_000_000,
    conversions: Number(row.metrics?.conversions) || 0,
    clicks: Number(row.metrics?.clicks) || 0,
    impressions: Number(row.metrics?.impressions) || 0,
    ctr: (Number(row.metrics?.ctr) || 0) * 100,
    cpc: (Number(row.metrics?.average_cpc) || 0) / 1_000_000,
    conversionRate:
      (Number(row.metrics?.conversions_from_interactions_rate) || 0) * 100,
  }));
}

/**
 * Fetch campaign data for a customer
 */
export async function fetchCampaigns(
  config: GoogleAdsConfig,
  customerId: string
): Promise<Campaign[]> {
  const customer = getCustomer(config, customerId);

  const results = await customer.query(`
    SELECT
      campaign.id,
      campaign.name,
      campaign.status,
      campaign.advertising_channel_type,
      campaign_budget.amount_micros,
      metrics.cost_micros,
      metrics.impressions,
      metrics.clicks,
      metrics.conversions,
      metrics.ctr,
      metrics.average_cpc,
      metrics.conversions_from_interactions_rate,
      metrics.all_conversions_value
    FROM campaign
    WHERE campaign.status != 'REMOVED'
    ORDER BY metrics.cost_micros DESC
  `);

  return results.map((row) => {
    const cost = (Number(row.metrics?.cost_micros) || 0) / 1_000_000;
    const clicks = Number(row.metrics?.clicks) || 0;
    const conversions = Number(row.metrics?.conversions) || 0;
    const convValue = Number(row.metrics?.all_conversions_value) || 0;

    const channelType = row.campaign?.advertising_channel_type;
    let type: Campaign["type"] = "search";
    if (channelType === enums.AdvertisingChannelType.DISPLAY) type = "display";
    else if (channelType === enums.AdvertisingChannelType.SHOPPING)
      type = "shopping";
    else if (channelType === enums.AdvertisingChannelType.VIDEO)
      type = "video";
    else if (channelType === enums.AdvertisingChannelType.PERFORMANCE_MAX)
      type = "pmax";

    return {
      id: String(row.campaign?.id || ""),
      clientId: customerId,
      name: row.campaign?.name || "",
      status:
        row.campaign?.status === enums.CampaignStatus.ENABLED
          ? "enabled"
          : row.campaign?.status === enums.CampaignStatus.PAUSED
            ? "paused"
            : "removed",
      type,
      budget:
        (Number(row.campaign_budget?.amount_micros) || 0) / 1_000_000,
      spend: cost,
      impressions: Number(row.metrics?.impressions) || 0,
      clicks,
      conversions,
      cost,
      ctr: (Number(row.metrics?.ctr) || 0) * 100,
      cpc: (Number(row.metrics?.average_cpc) || 0) / 1_000_000,
      conversionRate:
        (Number(row.metrics?.conversions_from_interactions_rate) || 0) *
        100,
      roas: cost > 0 ? Math.round((convValue / cost) * 10) / 10 : 0,
    };
  });
}

/**
 * Fetch budget information for pacing calculations
 */
export async function fetchBudgetInfo(
  config: GoogleAdsConfig,
  customerId: string
): Promise<{ totalBudget: number; totalSpend: number; pacing: number }> {
  const customer = getCustomer(config, customerId);

  // Get current month's date range
  const now = new Date();
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const startDate = startOfMonth.toISOString().split("T")[0];
  const endDate = now.toISOString().split("T")[0];

  // Fetch total spend this month
  const spendResults = await customer.query(`
    SELECT
      metrics.cost_micros
    FROM customer
    WHERE segments.date BETWEEN '${startDate}' AND '${endDate}'
  `);

  const totalSpend = spendResults.reduce(
    (sum, row) =>
      sum + (Number(row.metrics?.cost_micros) || 0) / 1_000_000,
    0
  );

  // Fetch campaign budgets
  const budgetResults = await customer.query(`
    SELECT
      campaign_budget.amount_micros
    FROM campaign_budget
    WHERE campaign.status = 'ENABLED'
  `);

  // Daily budgets * days in month = monthly budget estimate
  const daysInMonth = new Date(
    now.getFullYear(),
    now.getMonth() + 1,
    0
  ).getDate();
  const totalDailyBudget = budgetResults.reduce(
    (sum, row) =>
      sum +
      (Number(row.campaign_budget?.amount_micros) || 0) / 1_000_000,
    0
  );
  const totalBudget = totalDailyBudget * daysInMonth;

  // Calculate pacing: where we should be vs where we are
  const dayOfMonth = now.getDate();
  const expectedSpend = (totalBudget / daysInMonth) * dayOfMonth;
  const pacing =
    expectedSpend > 0 ? Math.round((totalSpend / expectedSpend) * 100) : 0;

  return { totalBudget, totalSpend, pacing };
}
