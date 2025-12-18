"use client";

import { useState } from "react";
import { PriceCard, SignalCard, IndicatorsPanel, MarketOverview } from "@/components/dashboard";
import { TradingChart } from "@/components/charts";
import { useMarketData, useAnalysis, useApiHealth, useKlines } from "@/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, WifiOff } from "lucide-react";

// Fonction pour formater les grands nombres
function formatNumber(num: number): string {
  if (num >= 1e9) return (num / 1e9).toFixed(1) + "B";
  if (num >= 1e6) return (num / 1e6).toFixed(1) + "M";
  if (num >= 1e3) return (num / 1e3).toFixed(1) + "K";
  return num.toFixed(2);
}

// Fonction pour formater le prix
function formatPrice(price: number): string {
  return price.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export default function DashboardPage() {
  const [chartTimeframe, setChartTimeframe] = useState("1h");
  const { isConnected, isChecking } = useApiHealth();
  const { data: marketData, isLoading: marketLoading, error: marketError } = useMarketData({
    refreshInterval: 10000,
  });
  const { analysis, isLoading: analysisLoading, error: analysisError } = useAnalysis({
    timeframe: "1h",
  });
  const { data: klines, isLoading: klinesLoading } = useKlines({
    symbol: "BTCUSDT",
    interval: chartTimeframe,
    limit: 100,
  });

  // Si le backend n'est pas connecté
  if (!isChecking && !isConnected) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">Vue d'ensemble du marché Bitcoin</p>
        </div>
        <Alert variant="destructive">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            <strong>Backend non connecté.</strong> Lancez le serveur avec :{" "}
            <code className="bg-muted px-1 rounded">cd backend && source venv/bin/activate && uvicorn main:app --reload</code>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Préparer les données pour les composants
  const signal = analysis?.signal
    ? {
        action: analysis.signal.action,
        confidence: analysis.signal.confidence,
        entry: analysis.signal.entry,
        stopLoss: analysis.signal.stop_loss,
        takeProfit: analysis.signal.take_profit,
        riskReward: analysis.signal.risk_reward,
        reasoning: analysis.signal.reasoning,
      }
    : null;

  const indicators = analysis?.indicators.map((ind) => ({
    name: ind.name,
    value: ind.value,
    signal: ind.signal,
    description: ind.description,
  })) || [];

  // Extraire les niveaux de S/R
  const supportLevels = analysis?.support_resistance
    .filter((sr) => sr.type === "support")
    .map((sr) => sr.price) || [95500, 93000];
  const resistanceLevels = analysis?.support_resistance
    .filter((sr) => sr.type === "resistance")
    .map((sr) => sr.price) || [98500, 100000];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">Vue d'ensemble du marché Bitcoin</p>
      </div>

      {(marketError || analysisError) && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {marketError || analysisError}
          </AlertDescription>
        </Alert>
      )}

      {/* Price Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {marketLoading ? (
          <>
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </>
        ) : marketData ? (
          <>
            <PriceCard
              title="Prix BTC"
              value={formatPrice(marketData.price)}
              change={marketData.change_24h}
              changePercent={marketData.change_percent_24h}
              icon="price"
            />
            <PriceCard
              title="Plus Haut 24h"
              value={formatPrice(marketData.high_24h)}
              icon="high"
            />
            <PriceCard
              title="Plus Bas 24h"
              value={formatPrice(marketData.low_24h)}
              icon="low"
            />
            <PriceCard
              title="Volume 24h"
              value={formatNumber(marketData.volume_24h)}
              icon="volume"
            />
          </>
        ) : null}
      </div>

      {/* Chart + Signal + Market Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {klinesLoading ? (
          <Skeleton className="h-[450px] col-span-2" />
        ) : (
          <TradingChart
            symbol="BTC/USDT"
            ohlcvData={klines}
            supportLevels={supportLevels}
            resistanceLevels={resistanceLevels}
            onTimeframeChange={setChartTimeframe}
          />
        )}
        <div className="space-y-6">
          {analysisLoading ? (
            <>
              <Skeleton className="h-64" />
              <Skeleton className="h-48" />
            </>
          ) : (
            <>
              {signal && <SignalCard signal={signal} />}
              <MarketOverview
                fearGreedIndex={analysis?.trend === "bullish" ? 65 : analysis?.trend === "bearish" ? 35 : 50}
                marketPhase={
                  analysis?.trend === "bullish"
                    ? "Accumulation"
                    : analysis?.trend === "bearish"
                    ? "Distribution"
                    : "Consolidation"
                }
                dominance={52.3}
                lastUpdate={new Date()}
              />
            </>
          )}
        </div>
      </div>

      {/* Indicators Panel */}
      {analysisLoading ? (
        <Skeleton className="h-64" />
      ) : indicators.length > 0 ? (
        <IndicatorsPanel indicators={indicators} />
      ) : null}
    </div>
  );
}
