import { NextRequest, NextResponse } from "next/server";
import {
  listAccessibleCustomers,
  fetchAccountMetrics,
  fetchCampaigns,
  fetchBudgetInfo,
} from "@/lib/google-ads";
import type { GoogleAdsConfig } from "@/types";

function getConfig(): GoogleAdsConfig | null {
  const developerToken = process.env.GOOGLE_ADS_DEVELOPER_TOKEN;
  const clientId = process.env.GOOGLE_ADS_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_ADS_CLIENT_SECRET;
  const refreshToken = process.env.GOOGLE_ADS_REFRESH_TOKEN;
  const loginCustomerId = process.env.GOOGLE_ADS_LOGIN_CUSTOMER_ID;

  if (!developerToken || !clientId || !clientSecret || !refreshToken) {
    return null;
  }

  return {
    developerToken,
    clientId,
    clientSecret,
    refreshToken,
    loginCustomerId,
  };
}

export async function GET(request: NextRequest) {
  const config = getConfig();
  if (!config) {
    return NextResponse.json(
      { error: "Google Ads API not configured. Set environment variables." },
      { status: 500 }
    );
  }

  const { searchParams } = new URL(request.url);
  const action = searchParams.get("action");
  const customerId = searchParams.get("customerId");
  const startDate = searchParams.get("startDate");
  const endDate = searchParams.get("endDate");

  try {
    switch (action) {
      case "listCustomers": {
        const customers = await listAccessibleCustomers(config);
        return NextResponse.json({ customers });
      }

      case "metrics": {
        if (!customerId || !startDate || !endDate) {
          return NextResponse.json(
            { error: "Missing customerId, startDate, or endDate" },
            { status: 400 }
          );
        }
        const metrics = await fetchAccountMetrics(
          config,
          customerId,
          startDate,
          endDate
        );
        return NextResponse.json({ metrics });
      }

      case "campaigns": {
        if (!customerId) {
          return NextResponse.json(
            { error: "Missing customerId" },
            { status: 400 }
          );
        }
        const campaigns = await fetchCampaigns(config, customerId);
        return NextResponse.json({ campaigns });
      }

      case "budget": {
        if (!customerId) {
          return NextResponse.json(
            { error: "Missing customerId" },
            { status: 400 }
          );
        }
        const budget = await fetchBudgetInfo(config, customerId);
        return NextResponse.json(budget);
      }

      default:
        return NextResponse.json(
          { error: "Invalid action. Use: listCustomers, metrics, campaigns, budget" },
          { status: 400 }
        );
    }
  } catch (error) {
    console.error("Google Ads API error:", error);
    return NextResponse.json(
      {
        error: "Google Ads API request failed",
        details: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 }
    );
  }
}
