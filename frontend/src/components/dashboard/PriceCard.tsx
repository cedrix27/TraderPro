"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, DollarSign, BarChart3, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface PriceCardProps {
  title: string;
  value: string;
  change?: number;
  changePercent?: number;
  icon?: "price" | "volume" | "high" | "low" | "activity";
  prefix?: string;
}

const iconMap = {
  price: DollarSign,
  volume: BarChart3,
  high: TrendingUp,
  low: TrendingDown,
  activity: Activity,
};

export function PriceCard({
  title,
  value,
  change,
  changePercent,
  icon = "price",
  prefix = "$",
}: PriceCardProps) {
  const Icon = iconMap[icon];
  const isPositive = (change ?? 0) >= 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold font-mono">
          {prefix}{value}
        </div>
        {(change !== undefined || changePercent !== undefined) && (
          <div className="flex items-center gap-1 mt-1">
            {isPositive ? (
              <TrendingUp className="h-3 w-3 text-green-500" />
            ) : (
              <TrendingDown className="h-3 w-3 text-red-500" />
            )}
            <span
              className={cn(
                "text-xs font-medium",
                isPositive ? "text-green-500" : "text-red-500"
              )}
            >
              {isPositive ? "+" : ""}{change?.toLocaleString()} ({changePercent?.toFixed(2)}%)
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
