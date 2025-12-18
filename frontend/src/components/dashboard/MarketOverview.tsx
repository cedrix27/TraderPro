"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Clock, Globe, Flame, Snowflake } from "lucide-react";

interface MarketOverviewProps {
  fearGreedIndex: number;
  marketPhase: string;
  dominance: number;
  lastUpdate: Date;
}

export function MarketOverview({
  fearGreedIndex,
  marketPhase,
  dominance,
  lastUpdate,
}: MarketOverviewProps) {
  const getFearGreedColor = (value: number) => {
    if (value <= 25) return { color: "text-red-500", label: "Extreme Fear", bg: "bg-red-500" };
    if (value <= 45) return { color: "text-orange-500", label: "Fear", bg: "bg-orange-500" };
    if (value <= 55) return { color: "text-yellow-500", label: "Neutral", bg: "bg-yellow-500" };
    if (value <= 75) return { color: "text-lime-500", label: "Greed", bg: "bg-lime-500" };
    return { color: "text-green-500", label: "Extreme Greed", bg: "bg-green-500" };
  };

  const fearGreed = getFearGreedColor(fearGreedIndex);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg">Aperçu du Marché</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Fear & Greed Index</span>
            <Badge className={fearGreed.bg}>{fearGreed.label}</Badge>
          </div>
          <div className="relative h-3 bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full">
            <div
              className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-white border-2 border-gray-800 rounded-full shadow-lg"
              style={{ left: `calc(${fearGreedIndex}% - 8px)` }}
            />
          </div>
          <div className="flex justify-between mt-1 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Snowflake className="h-3 w-3" /> 0
            </span>
            <span className={`font-bold ${fearGreed.color}`}>{fearGreedIndex}</span>
            <span className="flex items-center gap-1">
              100 <Flame className="h-3 w-3" />
            </span>
          </div>
        </div>

        <Separator />

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Phase du Marché</p>
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-primary" />
              <span className="font-medium">{marketPhase}</span>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Dominance BTC</p>
            <p className="font-medium font-mono">{dominance.toFixed(1)}%</p>
          </div>
        </div>

        <Separator />

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>
            Dernière mise à jour: {lastUpdate.toLocaleTimeString("fr-FR")}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
