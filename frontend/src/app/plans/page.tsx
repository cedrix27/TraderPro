"use client";

import { useState } from "react";
import { TradingPlanCard, PlanDetails } from "@/components/plans";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Info } from "lucide-react";
import type { TradingPlan } from "@/lib/types";

const tradingPlans: TradingPlan[] = [
  {
    id: "scalping",
    name: "Scalping",
    description:
      "Stratégie de trading à très court terme. Profitez des petits mouvements de prix en réalisant de nombreux trades rapides. Idéal pour les traders actifs qui peuvent surveiller le marché en permanence.",
    timeframe: "1m - 15m",
    riskLevel: "high",
    indicators: ["RSI", "MACD", "Volume", "BB"],
    icon: "zap",
  },
  {
    id: "swing",
    name: "Swing Trading",
    description:
      "Stratégie de trading à moyen terme. Capturez les mouvements de prix sur plusieurs jours à plusieurs semaines. Équilibre entre fréquence de trading et temps investi.",
    timeframe: "4H - 1D",
    riskLevel: "medium",
    indicators: ["MA50", "MA200", "RSI", "Fibonacci"],
    icon: "trending",
  },
  {
    id: "position",
    name: "Position Trading",
    description:
      "Stratégie de trading à long terme. Investissez sur des tendances de fond qui durent plusieurs semaines à plusieurs mois. Peu de maintenance requise, idéal pour les débutants.",
    timeframe: "1D - 1W",
    riskLevel: "low",
    indicators: ["MA200", "Support/Résistance", "Tendance"],
    icon: "target",
  },
];

export default function PlansPage() {
  const [selectedPlan, setSelectedPlan] = useState<TradingPlan | null>(
    tradingPlans[1]
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Plans de Trading</h1>
        <p className="text-muted-foreground">
          Sélectionnez un plan adapté à votre profil et suivez les règles pour
          trader efficacement
        </p>
      </div>

      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          Chaque plan de trading a ses propres règles et indicateurs. Choisissez
          celui qui correspond le mieux à votre disponibilité et votre tolérance
          au risque.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {tradingPlans.map((plan) => (
          <TradingPlanCard
            key={plan.id}
            plan={plan}
            isSelected={selectedPlan?.id === plan.id}
            onSelect={setSelectedPlan}
          />
        ))}
      </div>

      {selectedPlan && (
        <div className="mt-6">
          <PlanDetails plan={selectedPlan} />
        </div>
      )}
    </div>
  );
}
