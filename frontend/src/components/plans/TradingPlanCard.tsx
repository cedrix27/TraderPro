"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Clock, BarChart2, Shield, ChevronRight, Zap, TrendingUp, Target } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TradingPlan } from "@/lib/types";

interface TradingPlanCardProps {
  plan: TradingPlan;
  isSelected?: boolean;
  onSelect: (plan: TradingPlan) => void;
}

const riskColors = {
  low: { bg: "bg-green-500/10", text: "text-green-500", label: "Faible" },
  medium: { bg: "bg-yellow-500/10", text: "text-yellow-500", label: "Moyen" },
  high: { bg: "bg-red-500/10", text: "text-red-500", label: "Élevé" },
};

const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  zap: Zap,
  trending: TrendingUp,
  target: Target,
};

export function TradingPlanCard({ plan, isSelected, onSelect }: TradingPlanCardProps) {
  const riskConfig = riskColors[plan.riskLevel];
  const IconComponent = iconMap[plan.icon] || Target;

  return (
    <Card
      className={cn(
        "cursor-pointer transition-all hover:border-primary/50",
        isSelected && "border-primary ring-2 ring-primary/20"
      )}
      onClick={() => onSelect(plan)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={cn("p-2 rounded-lg", riskConfig.bg)}>
              <IconComponent className={cn("h-5 w-5", riskConfig.text)} />
            </div>
            <div>
              <CardTitle className="text-lg">{plan.name}</CardTitle>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="outline" className="text-xs">
                  <Clock className="h-3 w-3 mr-1" />
                  {plan.timeframe}
                </Badge>
                <Badge
                  variant="outline"
                  className={cn("text-xs", riskConfig.text)}
                >
                  <Shield className="h-3 w-3 mr-1" />
                  Risque {riskConfig.label}
                </Badge>
              </div>
            </div>
          </div>
          {isSelected && (
            <Badge className="bg-primary">Sélectionné</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">{plan.description}</p>

        <div>
          <p className="text-xs text-muted-foreground mb-2">Indicateurs utilisés:</p>
          <div className="flex flex-wrap gap-1">
            {plan.indicators.map((indicator) => (
              <Badge key={indicator} variant="secondary" className="text-xs">
                <BarChart2 className="h-3 w-3 mr-1" />
                {indicator}
              </Badge>
            ))}
          </div>
        </div>

        <Button className="w-full" variant={isSelected ? "default" : "outline"}>
          {isSelected ? "Plan Actif" : "Sélectionner ce plan"}
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </CardContent>
    </Card>
  );
}
