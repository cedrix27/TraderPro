"use client";

import { TradingChart } from "@/components/charts";
import {
  TechnicalAnalysis,
  SupportResistanceCard,
  MovingAveragesCard,
  RiskCalculator,
} from "@/components/analysis";
import { useAnalysis, useMarketData, useApiHealth } from "@/hooks";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle, WifiOff, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function AnalysisPage() {
  const { isConnected, isChecking } = useApiHealth();
  const { data: marketData } = useMarketData();
  const { analysis, isLoading, error, refresh } = useAnalysis({
    timeframe: "1h",
  });

  // Si le backend n'est pas connecté
  if (!isChecking && !isConnected) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Analyse Technique</h1>
          <p className="text-muted-foreground">
            Analyse détaillée du Bitcoin avec indicateurs et zones clés
          </p>
        </div>
        <Alert variant="destructive">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            <strong>Backend non connecté.</strong> Lancez le serveur avec :{" "}
            <code className="bg-muted px-1 rounded">uvicorn main:app --reload</code>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const currentPrice = marketData?.price || 0;

  // Préparer les données de S/R
  const levels = analysis?.support_resistance.map((sr) => ({
    type: sr.type,
    price: sr.price,
    strength: sr.strength,
  })) || [];

  // Préparer les moyennes mobiles
  const movingAverages = analysis?.moving_averages.map((ma) => ({
    name: ma.name,
    period: ma.period,
    value: ma.value,
    signal: ma.signal,
  })) || [];

  // Extraire les niveaux pour le chart
  const supportLevels = levels
    .filter((l) => l.type === "support")
    .map((l) => l.price);
  const resistanceLevels = levels
    .filter((l) => l.type === "resistance")
    .map((l) => l.price);

  // Compter les signaux
  const buySignals = (analysis?.indicators.filter((i) => i.signal === "bullish").length || 0) +
    (analysis?.moving_averages.filter((ma) => ma.signal === "bullish").length || 0);
  const sellSignals = (analysis?.indicators.filter((i) => i.signal === "bearish").length || 0) +
    (analysis?.moving_averages.filter((ma) => ma.signal === "bearish").length || 0);
  const neutralSignals = analysis?.indicators.filter((i) => i.signal === "neutral").length || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analyse Technique</h1>
          <p className="text-muted-foreground">
            Analyse détaillée du Bitcoin avec indicateurs et zones clés
          </p>
        </div>
        <Button variant="outline" onClick={refresh} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="h-[450px] col-span-2" />
            <Skeleton className="h-[450px]" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Skeleton className="h-64" />
            <Skeleton className="h-64" />
          </div>
        </div>
      ) : analysis ? (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <TradingChart
              symbol="BTC/USDT"
              supportLevels={supportLevels}
              resistanceLevels={resistanceLevels}
            />
            <TechnicalAnalysis
              trend={analysis.trend}
              trendStrength={analysis.trend_strength}
              summary={analysis.summary}
              buySignals={buySignals}
              sellSignals={sellSignals}
              neutralSignals={neutralSignals}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <SupportResistanceCard currentPrice={currentPrice} levels={levels} />
            <MovingAveragesCard
              currentPrice={currentPrice}
              movingAverages={movingAverages}
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <RiskCalculator
              currentPrice={currentPrice}
              suggestedEntry={analysis.signal.entry}
              suggestedStopLoss={analysis.signal.stop_loss}
              suggestedTakeProfit={analysis.signal.take_profit}
            />
          </div>
        </>
      ) : null}
    </div>
  );
}
