"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowUp, ArrowDown, Target } from "lucide-react";
import { cn } from "@/lib/utils";
import type { SupportResistance } from "@/lib/types";

interface SupportResistanceCardProps {
  currentPrice: number;
  levels: SupportResistance[];
}

const strengthColors = {
  strong: "bg-primary text-primary-foreground",
  medium: "bg-secondary text-secondary-foreground",
  weak: "bg-muted text-muted-foreground",
};

export function SupportResistanceCard({ currentPrice, levels }: SupportResistanceCardProps) {
  const supports = levels
    .filter((l) => l.type === "support")
    .sort((a, b) => b.price - a.price);
  const resistances = levels
    .filter((l) => l.type === "resistance")
    .sort((a, b) => a.price - b.price);

  const nearestSupport = supports[0];
  const nearestResistance = resistances[0];

  const distanceToSupport = nearestSupport
    ? ((currentPrice - nearestSupport.price) / currentPrice) * 100
    : 0;
  const distanceToResistance = nearestResistance
    ? ((nearestResistance.price - currentPrice) / currentPrice) * 100
    : 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Target className="h-5 w-5" />
          Support & Résistance
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="bg-muted rounded-lg p-4 text-center">
          <p className="text-xs text-muted-foreground mb-1">Prix Actuel</p>
          <p className="text-2xl font-mono font-bold">${currentPrice.toLocaleString()}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <ArrowUp className="h-4 w-4 text-red-500" />
              <h4 className="text-sm font-medium">Résistances</h4>
            </div>
            <div className="space-y-2">
              {resistances.map((level, index) => (
                <div
                  key={index}
                  className={cn(
                    "rounded-lg p-3 border",
                    index === 0 ? "border-red-500/50 bg-red-500/5" : "border-transparent"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-sm font-medium">
                      ${level.price.toLocaleString()}
                    </span>
                    <Badge variant="outline" className={cn("text-xs", strengthColors[level.strength])}>
                      {level.strength === "strong" ? "Fort" : level.strength === "medium" ? "Moyen" : "Faible"}
                    </Badge>
                  </div>
                  {index === 0 && (
                    <p className="text-xs text-muted-foreground">
                      +{distanceToResistance.toFixed(2)}% du prix actuel
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-2 mb-3">
              <ArrowDown className="h-4 w-4 text-green-500" />
              <h4 className="text-sm font-medium">Supports</h4>
            </div>
            <div className="space-y-2">
              {supports.map((level, index) => (
                <div
                  key={index}
                  className={cn(
                    "rounded-lg p-3 border",
                    index === 0 ? "border-green-500/50 bg-green-500/5" : "border-transparent"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-mono text-sm font-medium">
                      ${level.price.toLocaleString()}
                    </span>
                    <Badge variant="outline" className={cn("text-xs", strengthColors[level.strength])}>
                      {level.strength === "strong" ? "Fort" : level.strength === "medium" ? "Moyen" : "Faible"}
                    </Badge>
                  </div>
                  {index === 0 && (
                    <p className="text-xs text-muted-foreground">
                      -{distanceToSupport.toFixed(2)}% du prix actuel
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
