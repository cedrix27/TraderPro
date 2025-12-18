"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, TrendingDown, LineChart } from "lucide-react";
import { cn } from "@/lib/utils";

interface MovingAverage {
  name: string;
  period: number;
  value: number;
  signal: "bullish" | "bearish";
}

interface MovingAveragesCardProps {
  currentPrice: number;
  movingAverages: MovingAverage[];
}

export function MovingAveragesCard({ currentPrice, movingAverages }: MovingAveragesCardProps) {
  const bullishCount = movingAverages.filter((ma) => ma.signal === "bullish").length;
  const bearishCount = movingAverages.filter((ma) => ma.signal === "bearish").length;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <LineChart className="h-5 w-5" />
            Moyennes Mobiles
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-green-500 border-green-500/50">
              {bullishCount} Haussier
            </Badge>
            <Badge variant="outline" className="text-red-500 border-red-500/50">
              {bearishCount} Baissier
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {movingAverages.map((ma) => {
            const isBullish = ma.signal === "bullish";
            const percentDiff = ((currentPrice - ma.value) / ma.value) * 100;

            return (
              <div
                key={ma.name}
                className={cn(
                  "flex items-center justify-between p-3 rounded-lg",
                  isBullish ? "bg-green-500/5" : "bg-red-500/5"
                )}
              >
                <div className="flex items-center gap-3">
                  {isBullish ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-500" />
                  )}
                  <div>
                    <p className="text-sm font-medium">{ma.name}</p>
                    <p className="text-xs text-muted-foreground">{ma.period} périodes</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm font-medium">
                    ${ma.value.toLocaleString()}
                  </p>
                  <p
                    className={cn(
                      "text-xs",
                      isBullish ? "text-green-500" : "text-red-500"
                    )}
                  >
                    {isBullish ? "Prix au-dessus" : "Prix en-dessous"} ({percentDiff > 0 ? "+" : ""}
                    {percentDiff.toFixed(2)}%)
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-4 p-3 bg-muted rounded-lg">
          <h4 className="text-sm font-medium mb-2">Interprétation</h4>
          <p className="text-xs text-muted-foreground">
            {bullishCount > bearishCount
              ? "La majorité des moyennes mobiles indiquent une tendance haussière. Le prix est au-dessus de la plupart des MAs, ce qui est un signal positif."
              : bullishCount < bearishCount
              ? "La majorité des moyennes mobiles indiquent une tendance baissière. Le prix est en-dessous de la plupart des MAs, ce qui est un signal négatif."
              : "Les moyennes mobiles sont partagées, indiquant une phase de consolidation ou d'indécision du marché."}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
