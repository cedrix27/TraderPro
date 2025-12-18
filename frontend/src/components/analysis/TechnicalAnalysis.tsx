"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, TrendingDown, Minus, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface TechnicalAnalysisProps {
  trend: "bullish" | "bearish" | "neutral";
  trendStrength: number;
  summary: string;
  buySignals: number;
  sellSignals: number;
  neutralSignals: number;
}

const trendConfig = {
  bullish: {
    color: "text-green-500",
    bg: "bg-green-500",
    icon: TrendingUp,
    label: "Haussier",
  },
  bearish: {
    color: "text-red-500",
    bg: "bg-red-500",
    icon: TrendingDown,
    label: "Baissier",
  },
  neutral: {
    color: "text-yellow-500",
    bg: "bg-yellow-500",
    icon: Minus,
    label: "Neutre",
  },
};

export function TechnicalAnalysis({
  trend,
  trendStrength,
  summary,
  buySignals,
  sellSignals,
  neutralSignals,
}: TechnicalAnalysisProps) {
  const config = trendConfig[trend];
  const TrendIcon = config.icon;
  const totalSignals = buySignals + sellSignals + neutralSignals;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Analyse Technique
          </CardTitle>
          <Badge className={cn("text-white", config.bg)}>
            <TrendIcon className="h-3 w-3 mr-1" />
            {config.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Force de la tendance</span>
            <span className={cn("text-sm font-medium", config.color)}>
              {trendStrength}%
            </span>
          </div>
          <Progress value={trendStrength} className="h-2" />
        </div>

        <div className="bg-muted rounded-lg p-4">
          <h4 className="text-sm font-medium mb-2">Résumé</h4>
          <p className="text-sm text-muted-foreground">{summary}</p>
        </div>

        <div>
          <h4 className="text-sm font-medium mb-3">Distribution des Signaux</h4>
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground w-16">Achat</span>
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${(buySignals / totalSignals) * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium w-8 text-right">{buySignals}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground w-16">Vente</span>
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-red-500 transition-all"
                  style={{ width: `${(sellSignals / totalSignals) * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium w-8 text-right">{sellSignals}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-muted-foreground w-16">Neutre</span>
              <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-yellow-500 transition-all"
                  style={{ width: `${(neutralSignals / totalSignals) * 100}%` }}
                />
              </div>
              <span className="text-xs font-medium w-8 text-right">{neutralSignals}</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
