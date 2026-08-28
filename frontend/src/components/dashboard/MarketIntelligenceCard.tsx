"use client";

import { Activity, Gauge, Layers3, TrendingDown, TrendingUp, Waves } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { MarketIntelligence } from "@/lib/api";

const regimeLabels = {
  trend_up: "Tendance haussière",
  trend_down: "Tendance baissière",
  range: "Marché latéral",
  high_volatility: "Volatilité élevée",
};

export function MarketIntelligenceCard({ intelligence }: { intelligence: MarketIntelligence }) {
  const isBullish = intelligence.bias === "bullish";
  const isBearish = intelligence.bias === "bearish";
  const BiasIcon = isBullish ? TrendingUp : isBearish ? TrendingDown : Activity;
  const tone = isBullish ? "text-green-500" : isBearish ? "text-red-500" : "text-yellow-500";

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg"><Gauge className="h-5 w-5 text-primary" />Intelligence Marché</CardTitle>
            <CardDescription>Contexte public USD-M Futures pour BTCUSDT</CardDescription>
          </div>
          <Badge variant="outline" className={tone}><BiasIcon className="mr-1 h-3 w-3" />{regimeLabels[intelligence.regime]}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-lg bg-muted p-3">
          <div className="mb-2 flex items-center justify-between text-sm"><span className="font-medium">Score de contexte</span><span className={`font-mono font-bold ${tone}`}>{intelligence.context_score}/100</span></div>
          <div className="h-2 overflow-hidden rounded-full bg-background"><div className={`h-full ${isBullish ? "bg-green-500" : isBearish ? "bg-red-500" : "bg-yellow-500"}`} style={{ width: `${intelligence.context_score}%` }} /></div>
          <p className="mt-2 text-xs text-muted-foreground">{intelligence.recommendation}</p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <Metric icon={TrendingUp} label="Variation 24h" value={`${intelligence.day_change_pct >= 0 ? "+" : ""}${intelligence.day_change_pct.toFixed(2)}%`} tone={intelligence.day_change_pct >= 0 ? "text-green-500" : "text-red-500"} />
          <Metric icon={Activity} label="Funding" value={`${intelligence.funding_rate_pct >= 0 ? "+" : ""}${intelligence.funding_rate_pct.toFixed(4)}%`} />
          <Metric icon={Layers3} label="Open interest" value={intelligence.open_interest_change_pct === null ? "Collecte..." : `${intelligence.open_interest_change_pct >= 0 ? "+" : ""}${intelligence.open_interest_change_pct.toFixed(2)}%`} />
          <Metric icon={Waves} label="Volatilité 24h" value={`${intelligence.volatility_pct.toFixed(2)}%`} />
        </div>
        <p className="text-xs text-muted-foreground">Source : {intelligence.sources.join(", ")} · Mise à jour {new Date(intelligence.timestamp).toLocaleTimeString("fr-FR")}</p>
      </CardContent>
    </Card>
  );
}

function Metric({ icon: Icon, label, value, tone = "text-foreground" }: { icon: typeof Activity; label: string; value: string; tone?: string }) {
  return <div className="rounded-lg border p-3"><div className="mb-1 flex items-center gap-1 text-xs text-muted-foreground"><Icon className="h-3 w-3" />{label}</div><p className={`font-mono font-semibold ${tone}`}>{value}</p></div>;
}
