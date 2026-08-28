"use client";

import { useState } from "react";
import { Activity, BarChart3, Brain, CandlestickChart, Database, Radio, TrendingDown, TrendingUp } from "lucide-react";
import { TradingChart } from "@/components/charts";
import { MarketIntelligenceCard, SignalCard } from "@/components/dashboard";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAnalysis, useKlines, useMarketData, useMarketIntelligence } from "@/hooks";

const watchlist = [
  { symbol: "BTCUSDT", label: "Bitcoin", color: "text-orange-500" },
  { symbol: "ETHUSDT", label: "Ethereum", color: "text-blue-500" },
  { symbol: "BNBUSDT", label: "BNB", color: "text-yellow-500" },
];

function formatPrice(value: number) {
  return value.toLocaleString("en-US", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

export default function FinceptPage() {
  const [timeframe, setTimeframe] = useState("1h");
  const { data: market, isLoading: marketLoading } = useMarketData({ refreshInterval: 15_000 });
  const { analysis, isLoading: analysisLoading } = useAnalysis({ timeframe: "1h" });
  const { data: candles, isLoading: candlesLoading } = useKlines({ symbol: "BTCUSDT", interval: timeframe, limit: 160 });
  const { data: intelligence, isLoading: intelligenceLoading } = useMarketIntelligence();

  const supportLevels = analysis?.support_resistance.filter((level) => level.type === "support").map((level) => level.price) ?? [];
  const resistanceLevels = analysis?.support_resistance.filter((level) => level.type === "resistance").map((level) => level.price) ?? [];
  const signal = analysis?.signal ? {
    action: analysis.signal.action,
    confidence: analysis.signal.confidence,
    entry: analysis.signal.entry,
    stopLoss: analysis.signal.stop_loss,
    takeProfit: analysis.signal.take_profit,
    riskReward: analysis.signal.risk_reward,
    reasoning: analysis.signal.reasoning,
  } : null;

  return (
    <div className="space-y-5">
      <header className="flex flex-col gap-3 border-b pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <div className="rounded-md bg-primary p-1.5 text-primary-foreground"><CandlestickChart className="h-4 w-4" /></div>
            <Badge variant="outline">Workspace local</Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Fincept Workspace</h1>
          <p className="text-sm text-muted-foreground">Terminal d&apos;analyse TraderPro — données et décisions en lecture seule.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground"><Radio className="h-4 w-4 text-green-500" />Flux Futures Demo actif</div>
      </header>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Quote label="BTCUSDT" value={market ? `$${formatPrice(market.price)}` : "—"} delta={market?.change_percent_24h} icon={BarChart3} loading={marketLoading} />
        <Quote label="Funding" value={intelligence ? `${intelligence.funding_rate_pct >= 0 ? "+" : ""}${intelligence.funding_rate_pct.toFixed(4)}%` : "—"} icon={Activity} loading={intelligenceLoading} />
        <Quote label="Open Interest" value={intelligence ? `${(intelligence.open_interest / 1_000_000).toFixed(1)}M` : "—"} icon={Database} loading={intelligenceLoading} />
        <Quote label="Contexte" value={intelligence ? `${intelligence.context_score}/100` : "—"} icon={Brain} loading={intelligenceLoading} />
      </section>

      <section className="grid gap-5 xl:grid-cols-[220px_minmax(0,1fr)_340px]">
        <Card className="h-fit">
          <CardHeader className="pb-3"><CardTitle className="text-sm">Watchlist</CardTitle><CardDescription>Actifs suivis</CardDescription></CardHeader>
          <CardContent className="space-y-1">
            {watchlist.map((asset) => {
              const isBitcoin = asset.symbol === "BTCUSDT";
              return <div key={asset.symbol} className={`rounded-lg p-3 ${isBitcoin ? "bg-muted" : "opacity-60"}`}>
                <div className="flex items-center justify-between"><span className="font-mono text-sm font-semibold">{asset.symbol}</span>{isBitcoin && market ? <span className={market.change_percent_24h >= 0 ? "text-xs text-green-500" : "text-xs text-red-500"}>{market.change_percent_24h >= 0 ? "+" : ""}{market.change_percent_24h.toFixed(2)}%</span> : <span className="text-xs text-muted-foreground">Bientôt</span>}</div>
                <p className={`mt-1 text-xs ${asset.color}`}>{asset.label}</p>
              </div>;
            })}
          </CardContent>
        </Card>

        {candlesLoading ? <Skeleton className="h-[520px]" /> : <TradingChart symbol="BTC/USDT · Futures" ohlcvData={candles} supportLevels={supportLevels} resistanceLevels={resistanceLevels} onTimeframeChange={setTimeframe} />}

        <div className="space-y-5">
          {analysisLoading ? <Skeleton className="h-72" /> : signal ? <SignalCard signal={signal} /> : null}
          {intelligenceLoading ? <Skeleton className="h-72" /> : intelligence ? <MarketIntelligenceCard intelligence={intelligence} /> : null}
        </div>
      </section>

      <Card>
        <CardHeader className="pb-3"><CardTitle className="text-lg">Journal de décision</CardTitle><CardDescription>Le terminal explique le contexte ; les ordres restent exclusivement gérés par le bot autonome Testnet.</CardDescription></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-3">
          <Decision label="Régime marché" value={intelligence ? intelligence.regime.replace("_", " ") : "En attente"} />
          <Decision label="Signal technique" value={signal ? `${signal.action} · ${signal.confidence}%` : "En attente"} />
          <Decision label="Décision" value={intelligence?.recommendation ?? "Collecte du contexte Futures"} />
        </CardContent>
      </Card>
    </div>
  );
}

function Quote({ label, value, delta, icon: Icon, loading }: { label: string; value: string; delta?: number; icon: typeof Activity; loading: boolean }) {
  return (
    <Card>
      <CardContent className="p-4">
        {loading ? <Skeleton className="h-12" /> : <>
          <div className="mb-2 flex items-center justify-between text-xs text-muted-foreground"><span>{label}</span><Icon className="h-3.5 w-3.5" /></div>
          <p className="font-mono text-lg font-bold">{value}</p>
          {delta !== undefined && <p className={`mt-1 flex items-center gap-1 text-xs ${delta >= 0 ? "text-green-500" : "text-red-500"}`}>
            {delta >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {delta >= 0 ? "+" : ""}{delta.toFixed(2)}% 24h
          </p>}
        </>}
      </CardContent>
    </Card>
  );
}

function Decision({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border bg-muted/30 p-3"><p className="mb-1 text-xs text-muted-foreground">{label}</p><p className="text-sm font-medium capitalize">{value}</p></div>;
}
