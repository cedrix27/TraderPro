"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  BookOpen,
  CheckCircle,
  AlertCircle,
  Clock,
  Target,
  TrendingUp,
  TrendingDown,
  BarChart2,
} from "lucide-react";
import type { TradingPlan } from "@/lib/types";

interface PlanDetailsProps {
  plan: TradingPlan;
}

const planStrategies: Record<string, {
  rules: { type: "entry" | "exit" | "management"; rule: string }[];
  tips: string[];
  warnings: string[];
}> = {
  scalping: {
    rules: [
      { type: "entry", rule: "RSI < 30 (survendu) avec rebond sur support" },
      { type: "entry", rule: "RSI > 70 (suracheté) avec rejet sur résistance" },
      { type: "entry", rule: "Croisement MACD avec confirmation de volume" },
      { type: "exit", rule: "Prendre profit à 0.5-1% de gain" },
      { type: "exit", rule: "Stop loss serré à 0.3-0.5%" },
      { type: "management", rule: "Maximum 3 trades simultanés" },
      { type: "management", rule: "Ne pas trader pendant les annonces majeures" },
    ],
    tips: [
      "Tradez uniquement pendant les heures de forte liquidité",
      "Utilisez des timeframes courts (1m, 5m, 15m)",
      "La rapidité d'exécution est cruciale",
    ],
    warnings: [
      "Requiert une attention constante",
      "Les frais peuvent impacter significativement les profits",
      "Non recommandé pour les débutants",
    ],
  },
  swing: {
    rules: [
      { type: "entry", rule: "Prix au-dessus de la MA50 pour les longs" },
      { type: "entry", rule: "Rebond sur zone de support avec volume croissant" },
      { type: "entry", rule: "Pattern de retournement (double bottom, etc.)" },
      { type: "exit", rule: "Take profit sur zone de résistance majeure" },
      { type: "exit", rule: "Stop loss sous le dernier swing low" },
      { type: "management", rule: "Risquer max 2% du capital par trade" },
      { type: "management", rule: "Ratio Risk/Reward minimum de 1:2" },
    ],
    tips: [
      "Analysez en daily puis affinez en 4H",
      "Soyez patient, les setups prennent du temps",
      "Gardez un journal de trading",
    ],
    warnings: [
      "Les positions peuvent rester ouvertes plusieurs jours",
      "Nécessite de gérer le stress des fluctuations",
      "Le marché peut aller contre vous avant de se retourner",
    ],
  },
  position: {
    rules: [
      { type: "entry", rule: "Tendance confirmée sur timeframe weekly" },
      { type: "entry", rule: "Prix au-dessus de la MA200" },
      { type: "entry", rule: "Accumulation sur des niveaux de support historiques" },
      { type: "exit", rule: "Take profit progressif par paliers" },
      { type: "exit", rule: "Stop loss large (10-15%) sous zone d'accumulation" },
      { type: "management", rule: "DCA (Dollar Cost Average) pour les entrées" },
      { type: "management", rule: "Ne jamais investir plus que ce qu'on peut perdre" },
    ],
    tips: [
      "Focalisez-vous sur les fondamentaux",
      "Ignorez le bruit à court terme",
      "Révisez votre position mensuellement",
    ],
    warnings: [
      "Capital immobilisé sur longue période",
      "Nécessite une forte conviction",
      "Le marché crypto est très volatil",
    ],
  },
};

export function PlanDetails({ plan }: PlanDetailsProps) {
  const planId = plan.id as keyof typeof planStrategies;
  const strategy = planStrategies[planId] || planStrategies.swing;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Détails du Plan: {plan.name}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="rules">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="rules">Règles</TabsTrigger>
            <TabsTrigger value="tips">Conseils</TabsTrigger>
            <TabsTrigger value="warnings">Avertissements</TabsTrigger>
          </TabsList>

          <TabsContent value="rules" className="mt-4">
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
                    <TrendingUp className="h-4 w-4 text-green-500" />
                    Règles d'Entrée
                  </h4>
                  <div className="space-y-2">
                    {strategy.rules
                      .filter((r) => r.type === "entry")
                      .map((rule, index) => (
                        <div
                          key={index}
                          className="flex items-start gap-2 p-2 bg-green-500/5 rounded-lg"
                        >
                          <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{rule.rule}</span>
                        </div>
                      ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
                    <TrendingDown className="h-4 w-4 text-red-500" />
                    Règles de Sortie
                  </h4>
                  <div className="space-y-2">
                    {strategy.rules
                      .filter((r) => r.type === "exit")
                      .map((rule, index) => (
                        <div
                          key={index}
                          className="flex items-start gap-2 p-2 bg-red-500/5 rounded-lg"
                        >
                          <Target className="h-4 w-4 text-red-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{rule.rule}</span>
                        </div>
                      ))}
                  </div>
                </div>

                <div>
                  <h4 className="text-sm font-medium flex items-center gap-2 mb-2">
                    <BarChart2 className="h-4 w-4 text-blue-500" />
                    Gestion du Risque
                  </h4>
                  <div className="space-y-2">
                    {strategy.rules
                      .filter((r) => r.type === "management")
                      .map((rule, index) => (
                        <div
                          key={index}
                          className="flex items-start gap-2 p-2 bg-blue-500/5 rounded-lg"
                        >
                          <Clock className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
                          <span className="text-sm">{rule.rule}</span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="tips" className="mt-4">
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                {strategy.tips.map((tip, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-3 bg-primary/5 rounded-lg"
                  >
                    <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                    <span className="text-sm">{tip}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="warnings" className="mt-4">
            <ScrollArea className="h-[300px] pr-4">
              <div className="space-y-2">
                {strategy.warnings.map((warning, index) => (
                  <div
                    key={index}
                    className="flex items-start gap-2 p-3 bg-yellow-500/10 rounded-lg"
                  >
                    <AlertCircle className="h-4 w-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-yellow-500">{warning}</span>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
