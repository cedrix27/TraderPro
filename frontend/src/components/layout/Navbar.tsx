"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bitcoin, LayoutDashboard, LineChart, BookOpen, Bot, Brain } from "lucide-react";
import { cn } from "@/lib/utils";
import { useMarketData } from "@/hooks";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/analysis", label: "Analyse", icon: LineChart },
  { href: "/prediction", label: "Prediction", icon: Brain },
  { href: "/plans", label: "Plans", icon: BookOpen },
  { href: "/assistant", label: "Assistant IA", icon: Bot },
];

export function Navbar() {
  const pathname = usePathname();
  const { data: marketData } = useMarketData({ refreshInterval: 5000 });

  const formatPrice = (price: number) => {
    return price.toLocaleString("en-US", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  };

  const isPositive = (marketData?.change_percent_24h ?? 0) >= 0;

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center px-4">
        <Link href="/dashboard" className="flex items-center gap-2 font-bold text-xl mr-8">
          <Bitcoin className="h-8 w-8 text-orange-500" />
          <span>TraderPro</span>
        </Link>

        <div className="flex items-center gap-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors",
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
        </div>

        <div className="ml-auto flex items-center gap-4">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">BTC/USDT</span>
            <span className={cn("font-mono font-bold", isPositive ? "text-green-500" : "text-red-500")}>
              {marketData ? `$${formatPrice(marketData.price)}` : "..."}
            </span>
          </div>
        </div>
      </div>
    </nav>
  );
}
