import Link from "next/link";
import {
  ArrowUpRight,
  Bot,
  ChartNoAxesCombined,
  CircleAlert,
  FlaskConical,
  Gauge,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

// Vibe's own local UI/API server. It stays a separate process from TraderPro.
const challengerUrl = "http://127.0.0.1:8899";

export default function VibePage() {
  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="flex flex-col gap-4 border-b pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <div className="rounded-md bg-violet-600 p-1.5 text-white"><FlaskConical className="h-4 w-4" /></div>
            <Badge variant="outline" className="border-violet-300 text-violet-700 dark:border-violet-900 dark:text-violet-300">Bot indépendant</Badge>
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Vibe Challenger</h1>
          <p className="mt-1 text-sm text-muted-foreground">Un second trader expérimental, comparé à TraderPro sans influencer ses décisions.</p>
        </div>
        <Button asChild className="w-full lg:w-auto">
          <Link href={challengerUrl} target="_blank" rel="noreferrer">
            Ouvrir Vibe Trading <ArrowUpRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </header>

      <div className="grid gap-4 md:grid-cols-3">
        <StatusCard icon={Bot} label="État" value="Préparation requise" detail="Vibe n'est pas encore démarré localement." />
        <StatusCard icon={WalletCards} label="Compte Binance" value="À isoler" detail="Un second compte Demo est obligatoire." />
        <StatusCard icon={Gauge} label="Mode" value="Shadow avant trading" detail="Validation des signaux avant tout ordre Demo." />
      </div>

      <Card className="border-violet-200 bg-violet-50/40 dark:border-violet-900 dark:bg-violet-950/15">
        <CardHeader className="pb-3">
          <div className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 text-violet-600" />
            <div>
              <CardTitle className="text-base">Séparation stricte</CardTitle>
              <CardDescription className="mt-1">Vibe ne partagera ni clés API, ni positions, ni journal de décision avec le bot TraderPro.</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm md:grid-cols-3">
          <Rule label="TraderPro" value="Bot principal · compte Demo actuel" />
          <Rule label="Vibe" value="Challenger · second compte Demo" />
          <Rule label="Comparaison" value="Lecture seule : rendement, drawdown, taux de réussite" />
        </CardContent>
      </Card>

      <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><ChartNoAxesCombined className="h-5 w-5 text-violet-600" /><CardTitle>Tableau de comparaison</CardTitle></div>
            <CardDescription>Les chiffres apparaîtront dès que Vibe aura été installé et lancé en local.</CardDescription>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-[540px] text-sm">
              <thead className="border-b text-left text-muted-foreground"><tr><th className="pb-3 font-medium">Mesure</th><th className="pb-3 font-medium">TraderPro</th><th className="pb-3 font-medium">Vibe</th></tr></thead>
              <tbody className="divide-y">
                <Metric label="Rendement réalisé" primary="Disponible dans Démo & Historique" challenger="En attente de démarrage" />
                <Metric label="Trades clôturés" primary="Journal TraderPro" challenger="—" />
                <Metric label="Drawdown maximum" primary="Journal TraderPro" challenger="—" />
                <Metric label="Taux de réussite" primary="Journal TraderPro" challenger="—" />
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2"><CircleAlert className="h-5 w-5 text-amber-500" /><CardTitle>Étapes avant activation</CardTitle></div>
            <CardDescription>Le bouton ouvre Vibe dans un nouvel onglet lorsqu&apos;il tourne sur votre ordinateur.</CardDescription>
          </CardHeader>
          <CardContent>
            <ol className="space-y-4 text-sm">
              <Step number="1" text="Créer ou utiliser un deuxième compte Binance Futures Demo, distinct du compte TraderPro." />
              <Step number="2" text="Installer Vibe dans son propre dossier et lancer d'abord son mode shadow." />
              <Step number="3" text="Contrôler ses signaux et performances avant de l'autoriser à envoyer des ordres Demo." />
            </ol>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}

function StatusCard({ icon: Icon, label, value, detail }: { icon: typeof Bot; label: string; value: string; detail: string }) {
  return <Card><CardContent className="p-5"><div className="mb-3 flex items-center gap-2 text-muted-foreground"><Icon className="h-4 w-4" /><span className="text-xs font-medium uppercase tracking-wide">{label}</span></div><p className="font-semibold">{value}</p><p className="mt-1 text-sm text-muted-foreground">{detail}</p></CardContent></Card>;
}

function Rule({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg border border-violet-100 bg-background/70 p-3 dark:border-violet-950"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-medium">{value}</p></div>;
}

function Metric({ label, primary, challenger }: { label: string; primary: string; challenger: string }) {
  return <tr><td className="py-3 font-medium">{label}</td><td className="py-3 text-muted-foreground">{primary}</td><td className="py-3 text-muted-foreground">{challenger}</td></tr>;
}

function Step({ number, text }: { number: string; text: string }) {
  return <li className="flex gap-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-violet-100 text-xs font-bold text-violet-700 dark:bg-violet-950 dark:text-violet-300">{number}</span><span className="leading-6 text-muted-foreground">{text}</span></li>;
}
