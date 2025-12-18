"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { TrendingUp, TrendingDown, Minus, Target, ShieldAlert, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import type { TradingSignal } from "@/lib/types";

interface SignalCardProps {
  signal: TradingSignal;
}

export function SignalCard({ signal }: SignalCardProps) {
  const getSignalColor = (action: string) => {
    switch (action) {
      case "BUY":
        return "bg-green-500 hover:bg-green-600";
      case "SELL":
        return "bg-red-500 hover:bg-red-600";
      default:
        return "bg-yellow-500 hover:bg-yellow-600";
    }
  };

  const getSignalIcon = (action: string) => {
    switch (action) {
      case "BUY":
        return TrendingUp;
      case "SELL":
        return TrendingDown;
      default:
        return Minus;
    }
  };

  const SignalIcon = getSignalIcon(signal.action);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Signal IA</CardTitle>
          <Badge className={cn("text-white", getSignalColor(signal.action))}>
            <SignalIcon className="h-3 w-3 mr-1" />
            {signal.action}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-muted-foreground">Confiance</span>
            <span className="text-sm font-medium">{signal.confidence}%</span>
          </div>
          <Progress value={signal.confidence} className="h-2" />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="bg-muted rounded-lg p-3 text-center">
            <Target className="h-4 w-4 mx-auto mb-1 text-blue-500" />
            <p className="text-xs text-muted-foreground">Entry</p>
            <p className="text-sm font-mono font-medium">${signal.entry.toLocaleString()}</p>
          </div>
          <div className="bg-muted rounded-lg p-3 text-center">
            <ShieldAlert className="h-4 w-4 mx-auto mb-1 text-red-500" />
            <p className="text-xs text-muted-foreground">Stop Loss</p>
            <p className="text-sm font-mono font-medium text-red-500">
              ${signal.stopLoss.toLocaleString()}
            </p>
          </div>
          <div className="bg-muted rounded-lg p-3 text-center">
            <Trophy className="h-4 w-4 mx-auto mb-1 text-green-500" />
            <p className="text-xs text-muted-foreground">Take Profit</p>
            <p className="text-sm font-mono font-medium text-green-500">
              ${signal.takeProfit.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="bg-muted rounded-lg p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Risk/Reward</span>
            <Badge variant="outline">1:{signal.riskReward.toFixed(1)}</Badge>
          </div>
          <div className="space-y-1">
            {signal.reasoning.slice(0, 3).map((reason, index) => (
              <p key={index} className="text-xs text-muted-foreground flex items-start gap-2">
                <span className="text-primary">•</span>
                {reason}
              </p>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
