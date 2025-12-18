"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickData,
  Time,
  CandlestickSeries,
} from "lightweight-charts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, Maximize2, Settings } from "lucide-react";

interface OHLCVData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface TradingChartProps {
  symbol?: string;
  data?: CandlestickData<Time>[];
  ohlcvData?: OHLCVData[];
  supportLevels?: number[];
  resistanceLevels?: number[];
  onTimeframeChange?: (timeframe: string) => void;
}

const timeframes = ["1m", "5m", "15m", "1h", "4h", "1D", "1W"];

// Mock data for demonstration
const generateMockData = (): CandlestickData<Time>[] => {
  const data: CandlestickData<Time>[] = [];
  let basePrice = 97000;
  const now = Math.floor(Date.now() / 1000);

  for (let i = 100; i >= 0; i--) {
    const time = (now - i * 3600) as Time;
    const open = basePrice + (Math.random() - 0.5) * 500;
    const close = open + (Math.random() - 0.5) * 800;
    const high = Math.max(open, close) + Math.random() * 300;
    const low = Math.min(open, close) - Math.random() * 300;

    data.push({ time, open, high, low, close });
    basePrice = close;
  }

  return data;
};

// Convert OHLCV data from backend to CandlestickData format
const convertOHLCVToCandlestick = (ohlcvData: OHLCVData[]): CandlestickData<Time>[] => {
  return ohlcvData.map((item) => ({
    time: Math.floor(item.timestamp / 1000) as Time, // Convert ms to seconds
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
  }));
};

export function TradingChart({
  symbol = "BTC/USDT",
  data,
  ohlcvData,
  supportLevels = [],
  resistanceLevels = [],
  onTimeframeChange,
}: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState("1h");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "#1f2937" },
        horzLines: { color: "#1f2937" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: "#374151",
      },
      timeScale: {
        borderColor: "#374151",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderDownColor: "#ef4444",
      borderUpColor: "#22c55e",
      wickDownColor: "#ef4444",
      wickUpColor: "#22c55e",
    });

    // Use real OHLCV data if available, otherwise fall back to provided data or mock
    const chartData = ohlcvData && ohlcvData.length > 0
      ? convertOHLCVToCandlestick(ohlcvData)
      : data || generateMockData();
    candleSeries.setData(chartData);

    // Add support lines
    supportLevels.forEach((level) => {
      const supportLine = {
        price: level,
        color: "#22c55e",
        lineWidth: 1 as const,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `Support $${level.toLocaleString()}`,
      };
      candleSeries.createPriceLine(supportLine);
    });

    // Add resistance lines
    resistanceLevels.forEach((level) => {
      const resistanceLine = {
        price: level,
        color: "#ef4444",
        lineWidth: 1 as const,
        lineStyle: 2,
        axisLabelVisible: true,
        title: `Resistance $${level.toLocaleString()}`,
      };
      candleSeries.createPriceLine(resistanceLine);
    });

    chart.timeScale().fitContent();

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [data, ohlcvData, supportLevels, resistanceLevels]);

  const handleRefresh = () => {
    setIsLoading(true);
    setTimeout(() => {
      if (candleSeriesRef.current) {
        candleSeriesRef.current.setData(generateMockData());
        chartRef.current?.timeScale().fitContent();
      }
      setIsLoading(false);
    }, 500);
  };

  return (
    <Card className="col-span-2">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <CardTitle className="text-lg">{symbol}</CardTitle>
            <Badge variant="outline">Spot</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Tabs value={selectedTimeframe} onValueChange={(tf) => {
              setSelectedTimeframe(tf);
              onTimeframeChange?.(tf);
            }}>
              <TabsList className="h-8">
                {timeframes.map((tf) => (
                  <TabsTrigger key={tf} value={tf} className="text-xs px-2 h-6">
                    {tf}
                  </TabsTrigger>
                ))}
              </TabsList>
            </Tabs>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={handleRefresh}
              disabled={isLoading}
            >
              <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8">
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8">
              <Settings className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div ref={chartContainerRef} className="w-full" />
        <div className="flex items-center gap-4 mt-3 text-xs text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-green-500"></span>
            <span>Support</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-0.5 bg-red-500"></span>
            <span>Résistance</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
