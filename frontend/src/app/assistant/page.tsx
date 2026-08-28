"use client";

import { ChatWindow } from "@/components/ai-assistant";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, TrendingUp, Shield, Lightbulb } from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Analyse Intelligente",
    description: "L'IA analyse les tendances et patterns du marché en temps réel",
  },
  {
    icon: TrendingUp,
    title: "Signaux de Trading",
    description: "Recevez des recommandations d'achat/vente basées sur l'analyse technique",
  },
  {
    icon: Shield,
    title: "Gestion du Risque",
    description: "Suggestions de stop-loss et take-profit pour protéger votre capital",
  },
  {
    icon: Lightbulb,
    title: "Éducation",
    description: "Apprenez les concepts du trading à travers des explications simples",
  },
];

export default function AssistantPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Assistant IA</h1>
        <p className="text-muted-foreground">
          Posez vos questions sur le Bitcoin et recevez des analyses personnalisées
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ChatWindow />
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Capacités de l&apos;IA</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {features.map((feature) => {
                const Icon = feature.icon;
                return (
                  <div key={feature.title} className="flex gap-3">
                    <div className="p-2 rounded-lg bg-primary/10 h-fit">
                      <Icon className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <h4 className="text-sm font-medium">{feature.title}</h4>
                      <p className="text-xs text-muted-foreground">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Statut du Modèle</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Modèle</span>
                <Badge>TraderPro AI v1.0</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Statut</span>
                <Badge variant="outline" className="text-green-500 border-green-500">
                  En ligne
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Dernière MAJ</span>
                <span className="text-sm">Il y a 2h</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Données</span>
                <span className="text-sm">Temps réel</span>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-yellow-500/5 border-yellow-500/20">
            <CardContent className="pt-4">
              <p className="text-xs text-yellow-500">
                <strong>Avertissement :</strong> Les analyses et recommandations
                fournies par l&apos;IA sont à titre informatif uniquement. Le trading
                comporte des risques. Ne tradez jamais avec de l&apos;argent que vous
                ne pouvez pas vous permettre de perdre.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
