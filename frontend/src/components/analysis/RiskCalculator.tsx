"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Calculator, AlertTriangle, Target, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";

interface RiskCalculatorProps {
  currentPrice: number;
  suggestedEntry?: number;
  suggestedStopLoss?: number;
  suggestedTakeProfit?: number;
}

export function RiskCalculator({
  currentPrice,
  suggestedEntry,
  suggestedStopLoss,
  suggestedTakeProfit,
}: RiskCalculatorProps) {
  const [capital, setCapital] = useState<string>("1000");
  const [riskPercent, setRiskPercent] = useState<string>("2");
  const [entry, setEntry] = useState<string>(suggestedEntry?.toString() || currentPrice.toString());
  const [stopLoss, setStopLoss] = useState<string>(suggestedStopLoss?.toString() || "");
  const [takeProfit, setTakeProfit] = useState<string>(suggestedTakeProfit?.toString() || "");

  const capitalNum = parseFloat(capital) || 0;
  const riskPercentNum = parseFloat(riskPercent) || 0;
  const entryNum = parseFloat(entry) || 0;
  const stopLossNum = parseFloat(stopLoss) || 0;
  const takeProfitNum = parseFloat(takeProfit) || 0;

  const riskAmount = (capitalNum * riskPercentNum) / 100;
  const stopLossPercent = entryNum > 0 && stopLossNum > 0
    ? Math.abs((entryNum - stopLossNum) / entryNum) * 100
    : 0;
  const takeProfitPercent = entryNum > 0 && takeProfitNum > 0
    ? Math.abs((takeProfitNum - entryNum) / entryNum) * 100
    : 0;

  const positionSize = stopLossPercent > 0 ? riskAmount / (stopLossPercent / 100) : 0;
  const btcAmount = entryNum > 0 ? positionSize / entryNum : 0;
  const potentialProfit = positionSize * (takeProfitPercent / 100);
  const riskRewardRatio = stopLossPercent > 0 ? takeProfitPercent / stopLossPercent : 0;

  const getRRColor = (rr: number) => {
    if (rr >= 3) return "text-green-500";
    if (rr >= 2) return "text-lime-500";
    if (rr >= 1) return "text-yellow-500";
    return "text-red-500";
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Calculator className="h-5 w-5" />
          Calculateur de Risque
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Capital (USDT)</label>
            <Input
              type="number"
              value={capital}
              onChange={(e) => setCapital(e.target.value)}
              className="font-mono"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Risque (%)</label>
            <Input
              type="number"
              value={riskPercent}
              onChange={(e) => setRiskPercent(e.target.value)}
              className="font-mono"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Entry ($)</label>
            <Input
              type="number"
              value={entry}
              onChange={(e) => setEntry(e.target.value)}
              className="font-mono"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Stop Loss ($)</label>
            <Input
              type="number"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              className="font-mono text-red-500"
            />
          </div>
          <div>
            <label className="text-xs text-muted-foreground mb-1 block">Take Profit ($)</label>
            <Input
              type="number"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              className="font-mono text-green-500"
            />
          </div>
        </div>

        <div className="bg-muted rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-500" />
              <span className="text-sm">Risque Maximum</span>
            </div>
            <span className="font-mono font-medium text-yellow-500">
              ${riskAmount.toFixed(2)}
            </span>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-blue-500" />
              <span className="text-sm">Taille de Position</span>
            </div>
            <div className="text-right">
              <span className="font-mono font-medium">${positionSize.toFixed(2)}</span>
              <p className="text-xs text-muted-foreground">{btcAmount.toFixed(6)} BTC</p>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="h-4 w-4 text-green-500" />
              <span className="text-sm">Profit Potentiel</span>
            </div>
            <span className="font-mono font-medium text-green-500">
              +${potentialProfit.toFixed(2)}
            </span>
          </div>

          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-sm font-medium">Risk/Reward Ratio</span>
            <Badge
              variant="outline"
              className={cn("font-mono", getRRColor(riskRewardRatio))}
            >
              1:{riskRewardRatio.toFixed(2)}
            </Badge>
          </div>
        </div>

        {riskRewardRatio > 0 && riskRewardRatio < 2 && (
          <div className="flex items-start gap-2 p-3 bg-yellow-500/10 rounded-lg text-yellow-500">
            <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <p className="text-xs">
              Le ratio Risk/Reward est inférieur à 2. Il est recommandé de viser un ratio minimum de 1:2 pour un trading rentable à long terme.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
