"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  LineChart,
  BookOpen,
  Bot,
  Settings,
  Bell,
  TrendingUp,
  TrendingDown,
  Brain,
  History,
  CandlestickChart,
  FlaskConical,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const mainNavItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analysis", label: "Analyse Technique", icon: LineChart },
  { href: "/prediction", label: "Prediction IA", icon: Brain },
  { href: "/fincept", label: "Fincept Workspace", icon: CandlestickChart },
  { href: "/vibe", label: "Vibe Challenger", icon: FlaskConical },
  { href: "/plans", label: "Plans de Trading", icon: BookOpen },
  { href: "/assistant", label: "Assistant IA", icon: Bot },
  { href: "/history", label: "Démo & Historique", icon: History },
];

const bottomNavItems = [
  { href: "/settings", label: "Paramètres", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden lg:flex flex-col w-64 border-r bg-background h-[calc(100vh-4rem)]">
      <div className="flex-1 py-4">
        <div className="px-4 mb-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Navigation
          </h3>
          <nav className="space-y-1">
            {mainNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <Separator className="my-4" />

        <div className="px-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Signal Actuel
          </h3>
          <div className="bg-muted rounded-lg p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">BTC/USDT</span>
              <Badge variant="default" className="bg-green-500">
                <TrendingUp className="h-3 w-3 mr-1" />
                BUY
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <div className="flex justify-between">
                <span>Confiance</span>
                <span className="text-foreground">78%</span>
              </div>
              <div className="flex justify-between">
                <span>Entry</span>
                <span className="text-foreground">$97,100</span>
              </div>
              <div className="flex justify-between">
                <span>Stop Loss</span>
                <span className="text-red-500">$95,500</span>
              </div>
              <div className="flex justify-between">
                <span>Take Profit</span>
                <span className="text-green-500">$101,000</span>
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-4" />

        <div className="px-4">
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
            Alertes
          </h3>
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm">
              <Bell className="h-4 w-4 text-yellow-500" />
              <span className="text-muted-foreground">RSI en zone de surachat</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <TrendingDown className="h-4 w-4 text-red-500" />
              <span className="text-muted-foreground">Approche résistance $98K</span>
            </div>
          </div>
        </div>
      </div>

      <div className="p-4 border-t">
        <nav className="space-y-1">
          {bottomNavItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
