"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Info, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Indicator } from "@/lib/types";

interface IndicatorsPanelProps {
  indicators: Indicator[];
}

const signalConfig = {
  bullish: {
    color: "text-green-500",
    bg: "bg-green-500/10",
    icon: TrendingUp,
    label: "Haussier",
  },
  bearish: {
    color: "text-red-500",
    bg: "bg-red-500/10",
    icon: TrendingDown,
    label: "Baissier",
  },
  neutral: {
    color: "text-yellow-500",
    bg: "bg-yellow-500/10",
    icon: Minus,
    label: "Neutre",
  },
};

export function IndicatorsPanel({ indicators }: IndicatorsPanelProps) {
  const bullishCount = indicators.filter((i) => i.signal === "bullish").length;
  const bearishCount = indicators.filter((i) => i.signal === "bearish").length;
  const neutralCount = indicators.filter((i) => i.signal === "neutral").length;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Indicateurs Techniques</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-green-500 border-green-500/50">
              {bullishCount} Haussier
            </Badge>
            <Badge variant="outline" className="text-red-500 border-red-500/50">
              {bearishCount} Baissier
            </Badge>
            <Badge variant="outline" className="text-yellow-500 border-yellow-500/50">
              {neutralCount} Neutre
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <TooltipProvider>
            {indicators.map((indicator) => {
              const config = signalConfig[indicator.signal];
              const Icon = config.icon;

              return (
                <Tooltip key={indicator.name}>
                  <TooltipTrigger asChild>
                    <div
                      className={cn(
                        "rounded-lg p-3 cursor-help transition-colors",
                        config.bg,
                        "hover:opacity-80"
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium">{indicator.name}</span>
                        <Icon className={cn("h-4 w-4", config.color)} />
                      </div>
                      <p className={cn("text-lg font-mono font-bold", config.color)}>
                        {typeof indicator.value === "number"
                          ? indicator.value.toFixed(2)
                          : indicator.value}
                      </p>
                      <p className={cn("text-xs", config.color)}>{config.label}</p>
                    </div>
                  </TooltipTrigger>
                  <TooltipContent side="bottom" className="max-w-xs">
                    <p className="text-sm">{indicator.description}</p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </TooltipProvider>
        </div>
      </CardContent>
    </Card>
  );
}
