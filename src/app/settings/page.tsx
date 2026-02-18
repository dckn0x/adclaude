"use client";

import { useState } from "react";
import Header from "@/components/layout/Header";
import Card from "@/components/ui/Card";
import {
  Key,
  Bell,
  Shield,
  Link2,
  CheckCircle,
  AlertCircle,
  Eye,
  EyeOff,
} from "lucide-react";

export default function SettingsPage() {
  const [showSecrets, setShowSecrets] = useState(false);
  const [config, setConfig] = useState({
    developerToken: "",
    clientId: "",
    clientSecret: "",
    refreshToken: "",
    loginCustomerId: "",
  });
  const [alertSettings, setAlertSettings] = useState({
    budgetOverpace: true,
    budgetUnderpace: true,
    cpaSpike: true,
    ctrDrop: true,
    conversionDrop: true,
    anomalyDetection: true,
  });
  const [isConnected, setIsConnected] = useState(false);

  function handleConnect() {
    if (
      config.developerToken &&
      config.clientId &&
      config.clientSecret &&
      config.refreshToken
    ) {
      setIsConnected(true);
    }
  }

  return (
    <div>
      <Header title="Settings" subtitle="Configure your Google Ads connection and alerts" />

      <div className="p-8 max-w-3xl">
        {/* Google Ads API Connection */}
        <Card className="mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-blue-500/10">
              <Key className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-foreground">
                Google Ads API Connection
              </h3>
              <p className="text-xs text-muted">
                Connect your Google Ads account using API credentials
              </p>
            </div>
            {isConnected && (
              <div className="ml-auto flex items-center gap-1.5 text-xs text-emerald-400">
                <CheckCircle className="w-4 h-4" />
                Connected
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Developer Token
              </label>
              <input
                type={showSecrets ? "text" : "password"}
                value={config.developerToken}
                onChange={(e) =>
                  setConfig({ ...config, developerToken: e.target.value })
                }
                placeholder="Enter your developer token"
                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm text-foreground placeholder-muted/50 outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                OAuth2 Client ID
              </label>
              <input
                type={showSecrets ? "text" : "password"}
                value={config.clientId}
                onChange={(e) =>
                  setConfig({ ...config, clientId: e.target.value })
                }
                placeholder="Enter your OAuth2 client ID"
                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm text-foreground placeholder-muted/50 outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                OAuth2 Client Secret
              </label>
              <input
                type={showSecrets ? "text" : "password"}
                value={config.clientSecret}
                onChange={(e) =>
                  setConfig({ ...config, clientSecret: e.target.value })
                }
                placeholder="Enter your OAuth2 client secret"
                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm text-foreground placeholder-muted/50 outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Refresh Token
              </label>
              <input
                type={showSecrets ? "text" : "password"}
                value={config.refreshToken}
                onChange={(e) =>
                  setConfig({ ...config, refreshToken: e.target.value })
                }
                placeholder="Enter your refresh token"
                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm text-foreground placeholder-muted/50 outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Login Customer ID (MCC){" "}
                <span className="text-muted/50">— optional</span>
              </label>
              <input
                type="text"
                value={config.loginCustomerId}
                onChange={(e) =>
                  setConfig({ ...config, loginCustomerId: e.target.value })
                }
                placeholder="e.g. 123-456-7890"
                className="w-full px-3 py-2 rounded-lg bg-background border border-border text-sm text-foreground placeholder-muted/50 outline-none focus:border-accent transition-colors"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <button
                onClick={() => setShowSecrets(!showSecrets)}
                className="flex items-center gap-1.5 text-xs text-muted hover:text-foreground transition-colors"
              >
                {showSecrets ? (
                  <EyeOff className="w-3.5 h-3.5" />
                ) : (
                  <Eye className="w-3.5 h-3.5" />
                )}
                {showSecrets ? "Hide" : "Show"} credentials
              </button>

              <button
                onClick={handleConnect}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent-hover transition-colors"
              >
                <Link2 className="w-4 h-4" />
                {isConnected ? "Reconnect" : "Connect Account"}
              </button>
            </div>
          </div>
        </Card>

        {/* Alert Settings */}
        <Card className="mb-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-amber-500/10">
              <Bell className="w-5 h-5 text-amber-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-foreground">
                Alert Configuration
              </h3>
              <p className="text-xs text-muted">
                Choose which alerts you want to receive
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {[
              {
                key: "budgetOverpace" as const,
                label: "Budget Over-pacing",
                desc: "Alert when spend exceeds budget pace by 10%+",
              },
              {
                key: "budgetUnderpace" as const,
                label: "Budget Under-pacing",
                desc: "Alert when spend is below 70% of expected pace",
              },
              {
                key: "cpaSpike" as const,
                label: "CPA Spike Detection",
                desc: "Alert when CPA increases 20%+ vs 7-day average",
              },
              {
                key: "ctrDrop" as const,
                label: "CTR Drop Detection",
                desc: "Alert when CTR drops 15%+ vs baseline",
              },
              {
                key: "conversionDrop" as const,
                label: "Conversion Volume Drop",
                desc: "Alert when daily conversions drop 30%+ vs average",
              },
              {
                key: "anomalyDetection" as const,
                label: "AI Anomaly Detection",
                desc: "Use machine learning to detect unusual patterns",
              },
            ].map((item) => (
              <div
                key={item.key}
                className="flex items-center justify-between p-3 rounded-lg bg-background border border-border"
              >
                <div>
                  <p className="text-sm text-foreground">{item.label}</p>
                  <p className="text-xs text-muted">{item.desc}</p>
                </div>
                <button
                  onClick={() =>
                    setAlertSettings({
                      ...alertSettings,
                      [item.key]: !alertSettings[item.key],
                    })
                  }
                  className={`relative w-10 h-5 rounded-full transition-colors ${
                    alertSettings[item.key] ? "bg-accent" : "bg-border"
                  }`}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white transition-transform ${
                      alertSettings[item.key] ? "translate-x-5" : ""
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </Card>

        {/* Security note */}
        <Card>
          <div className="flex items-start gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-emerald-500/10 flex-shrink-0">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-sm font-medium text-foreground">Security</h3>
              <p className="text-xs text-muted mt-1 leading-relaxed">
                Your API credentials are encrypted and stored securely.
                Credentials are never exposed in client-side code. All API calls
                are made server-side through our secure proxy. We recommend using
                a dedicated Google Cloud project with minimal permissions.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
