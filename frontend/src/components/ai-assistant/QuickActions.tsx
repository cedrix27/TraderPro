"use client";

import { Button } from "@/components/ui/button";
import { TrendingUp, Target, HelpCircle, BarChart2 } from "lucide-react";

interface QuickActionsProps {
  onAction: (action: string) => void;
}

const quickActions = [
  {
    label: "Tendance actuelle",
    query: "Quelle est la tendance actuelle du Bitcoin ?",
    icon: TrendingUp,
  },
  {
    label: "Supports/Résistances",
    query: "Quels sont les niveaux de support et résistance clés ?",
    icon: Target,
  },
  {
    label: "Dois-je acheter ?",
    query: "Est-ce un bon moment pour acheter du Bitcoin ?",
    icon: HelpCircle,
  },
  {
    label: "Analyse technique",
    query: "Peux-tu me faire une analyse technique complète du BTC ?",
    icon: BarChart2,
  },
];

export function QuickActions({ onAction }: QuickActionsProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {quickActions.map((action) => {
        const Icon = action.icon;
        return (
          <Button
            key={action.label}
            variant="outline"
            size="sm"
            className="text-xs"
            onClick={() => onAction(action.query)}
          >
            <Icon className="h-3 w-3 mr-1" />
            {action.label}
          </Button>
        );
      })}
    </div>
  );
}
