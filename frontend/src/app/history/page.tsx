"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertCircle, History, Loader2, Play, RefreshCw, ShieldCheck, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ApiError, demoTradingApi, DemoHistoryResponse } from "@/lib/api";

const money = (value: number | null | undefined) =>
  value === null || value === undefined ? "—" : `${value >= 0 ? "+" : ""}${value.toLocaleString("en-US", { maximumFractionDigits: 2 })} USDT`;
const price = (value: number | null | undefined) =>
  value === null || value === undefined ? "—" : `$${value.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
const date = (value: string | null) => value ? new Date(value).toLocaleString("fr-FR") : "—";

export default function HistoryPage() {
  const [history, setHistory] = useState<DemoHistoryResponse | null>(null);
  const [symbol, setSymbol] = useState("BTCUSDT");
  const [amount, setAmount] = useState("25");
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setHistory(await demoTradingApi.getHistory());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger l'historique.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void loadHistory(); }, [loadHistory]);

  const execute = async () => {
    const amountValue = Number(amount);
    if (!Number.isFinite(amountValue) || amountValue <= 0) {
      setError("Saisissez un montant USDT supérieur à zéro.");
      return;
    }
    try {
      setExecuting(true);
      setError(null);
      setNotice(null);
      const decision = await demoTradingApi.execute(symbol.trim().toUpperCase(), amountValue);
      setNotice(
        decision.status === "executed"
          ? `Décision ${decision.action} exécutée sur Binance Testnet.`
          : decision.status === "recorded"
            ? "Décision HOLD enregistrée : aucun ordre n'a été envoyé."
            : `Décision refusée : ${decision.rejection_reason ?? "raison inconnue"}`,
      );
      await loadHistory();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible d'exécuter la décision.");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div><h1 className="text-2xl font-bold">Mode démo Futures & historique</h1><p className="text-muted-foreground">Décisions IA, positions BTCUSDT USDT-M et gains/pertes réalisés.</p></div>
        <Badge variant="outline" className="w-fit border-emerald-600 text-emerald-500"><ShieldCheck className="mr-2 h-4 w-4" />Futures Testnet · isolé · 1×</Badge>
      </div>

      <Alert><AlertCircle className="h-4 w-4" /><AlertDescription>Cette fonction n&apos;utilise jamais le compte réel. Configurez les clés Futures Testnet dans <code>backend/.env</code> ; les signaux BUY ouvrent un LONG et les SELL un SHORT ou ferment la position opposée.</AlertDescription></Alert>
      {error ? <Alert variant="destructive"><AlertCircle className="h-4 w-4" /><AlertDescription>{error}</AlertDescription></Alert> : null}
      {notice ? <Alert><AlertDescription>{notice}</AlertDescription></Alert> : null}

      <Card>
        <CardHeader><CardTitle>Tester la décision courante</CardTitle><CardDescription>L&apos;analyse technique choisit BUY, SELL ou HOLD. Un ordre n&apos;est tenté que pour BUY/SELL.</CardDescription></CardHeader>
        <CardContent className="flex flex-col gap-4 md:flex-row md:items-end">
          <div className="space-y-2"><label htmlFor="symbol" className="text-sm font-medium">Paire</label><Input id="symbol" value={symbol} onChange={(event) => setSymbol(event.target.value)} className="uppercase" /></div>
          <div className="space-y-2"><label htmlFor="amount" className="text-sm font-medium">Montant (USDT)</label><Input id="amount" inputMode="decimal" value={amount} onChange={(event) => setAmount(event.target.value)} /></div>
          <Button onClick={() => void execute()} disabled={executing}>{executing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}{executing ? "Analyse…" : "Analyser et tenter"}</Button>
          <Button variant="outline" onClick={() => void loadHistory()} disabled={loading}><RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />Actualiser</Button>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader className="pb-2"><CardDescription>P&L réalisé</CardDescription><CardTitle className={history && history.realized_pnl_usdt < 0 ? "text-red-500" : "text-emerald-500"}>{money(history?.realized_pnl_usdt)}</CardTitle></CardHeader></Card>
        <Card><CardHeader className="pb-2"><CardDescription>Positions ouvertes</CardDescription><CardTitle>{history?.open_positions.length ?? 0}</CardTitle></CardHeader></Card>
        <Card><CardHeader className="pb-2"><CardDescription>Décisions enregistrées</CardDescription><CardTitle>{history?.decisions.length ?? 0}</CardTitle></CardHeader></Card>
      </div>

      <Card><CardHeader><CardTitle className="flex items-center gap-2"><Wallet className="h-5 w-5" />Positions ouvertes</CardTitle></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[720px] text-sm"><thead className="border-b text-left text-muted-foreground"><tr><th className="p-3">Paire</th><th className="p-3">Quantité</th><th className="p-3">Entrée</th><th className="p-3">Cours actuel</th><th className="p-3">P&L latent</th><th className="p-3">Ouverte le</th></tr></thead><tbody>{history?.open_positions.length ? history.open_positions.map((position) => <tr key={position.id} className="border-b"><td className="p-3 font-medium">{position.symbol}</td><td className="p-3">{position.quantity}</td><td className="p-3">{price(position.entry_price)}</td><td className="p-3">{price(position.current_price)}</td><td className={`p-3 font-medium ${(position.unrealized_pnl_usdt ?? 0) < 0 ? "text-red-500" : "text-emerald-500"}`}>{money(position.unrealized_pnl_usdt)}</td><td className="p-3">{date(position.opened_at)}</td></tr>) : <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">Aucune position ouverte.</td></tr>}</tbody></table></CardContent></Card>

      <Card><CardHeader><CardTitle className="flex items-center gap-2"><History className="h-5 w-5" />Décisions IA</CardTitle></CardHeader><CardContent className="space-y-3">{history?.decisions.length ? history.decisions.map((decision) => <div key={decision.id} className="rounded-lg border p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2"><Badge variant={decision.action === "BUY" ? "default" : "secondary"}>{decision.action === "BUY" ? <TrendingUp className="mr-1 h-3 w-3" /> : decision.action === "SELL" ? <TrendingDown className="mr-1 h-3 w-3" /> : null}{decision.action}</Badge><span className="font-medium">{decision.symbol}</span><Badge variant="outline">{decision.status}</Badge></div><span className="text-xs text-muted-foreground">{date(decision.created_at)} · confiance {decision.confidence.toFixed(0)}%</span></div><p className="mt-3 text-sm text-muted-foreground">{decision.reasoning.join(" · ")}</p>{decision.rejection_reason ? <p className="mt-2 text-sm text-red-500">Refus : {decision.rejection_reason}</p> : null}</div>) : <p className="py-6 text-center text-muted-foreground">Aucune décision enregistrée.</p>}</CardContent></Card>

      <Card><CardHeader><CardTitle>Historique des positions</CardTitle><CardDescription>Résultats nets enregistrés après une vente Testnet.</CardDescription></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[720px] text-sm"><thead className="border-b text-left text-muted-foreground"><tr><th className="p-3">Paire</th><th className="p-3">Entrée</th><th className="p-3">Sortie</th><th className="p-3">Montant</th><th className="p-3">P&L</th><th className="p-3">Statut</th></tr></thead><tbody>{history?.trades.length ? history.trades.map((trade) => <tr key={trade.id} className="border-b"><td className="p-3 font-medium">{trade.symbol}</td><td className="p-3">{price(trade.entry_price)}</td><td className="p-3">{price(trade.exit_price)}</td><td className="p-3">{money(trade.amount_usdt)}</td><td className={`p-3 font-medium ${(trade.pnl_usdt ?? 0) < 0 ? "text-red-500" : "text-emerald-500"}`}>{money(trade.pnl_usdt)}</td><td className="p-3"><Badge variant="outline">{trade.status}</Badge></td></tr>) : <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">Aucune position enregistrée.</td></tr>}</tbody></table></CardContent></Card>
    </div>
  );
}
