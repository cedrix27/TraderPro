"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { usePrediction, usePredictionStatus, useApiHealth, useMarketData } from "@/hooks";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Calendar,
  Clock,
  AlertCircle,
  WifiOff,
  Brain,
  Target,
  ArrowUp,
  ArrowDown,
  Activity,
  Info,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  Eye,
  Hand
} from "lucide-react";

// Fonction pour formater le prix
function formatPrice(price: number): string {
  return price.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

// Fonction pour formater la date
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("fr-FR", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

// Composant pour le signal de direction
function DirectionSignal({
  direction,
  confidence,
  strength
}: {
  direction: "UP" | "DOWN";
  confidence: number;
  strength: string;
}) {
  const isUp = direction === "UP";

  return (
    <div className={`p-6 rounded-xl border-2 ${
      isUp
        ? "bg-green-500/10 border-green-500/30"
        : "bg-red-500/10 border-red-500/30"
    }`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-3 rounded-full ${isUp ? "bg-green-500/20" : "bg-red-500/20"}`}>
            {isUp ? (
              <ArrowUp className="h-8 w-8 text-green-500" />
            ) : (
              <ArrowDown className="h-8 w-8 text-red-500" />
            )}
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Prediction pour demain</p>
            <p className={`text-3xl font-bold ${isUp ? "text-green-500" : "text-red-500"}`}>
              {isUp ? "HAUSSE" : "BAISSE"}
            </p>
          </div>
        </div>
        <Badge
          variant="outline"
          className={`text-lg px-4 py-2 ${
            strength === "STRONG"
              ? "border-primary text-primary"
              : strength === "MODERATE"
              ? "border-yellow-500 text-yellow-500"
              : "border-muted-foreground text-muted-foreground"
          }`}
        >
          {strength === "STRONG" ? "Signal Fort" : strength === "MODERATE" ? "Signal Modere" : "Signal Faible"}
        </Badge>
      </div>

      {/* Barre de confiance */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Confiance</span>
          <span className="font-bold">{confidence.toFixed(1)}%</span>
        </div>
        <Progress
          value={confidence}
          className={`h-3 ${isUp ? "[&>div]:bg-green-500" : "[&>div]:bg-red-500"}`}
        />
      </div>
    </div>
  );
}

// Composant pour les probabilités
function ProbabilityBars({ probabilities }: { probabilities: { UP: number; DOWN: number } }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Probabilites
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* UP */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span>Hausse (UP)</span>
            </div>
            <span className="font-mono font-bold text-green-500">{probabilities.UP.toFixed(1)}%</span>
          </div>
          <Progress value={probabilities.UP} className="h-2 [&>div]:bg-green-500" />
        </div>

        {/* DOWN */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <TrendingDown className="h-4 w-4 text-red-500" />
              <span>Baisse (DOWN)</span>
            </div>
            <span className="font-mono font-bold text-red-500">{probabilities.DOWN.toFixed(1)}%</span>
          </div>
          <Progress value={probabilities.DOWN} className="h-2 [&>div]:bg-red-500" />
        </div>
      </CardContent>
    </Card>
  );
}

// Composant pour la recommandation
function RecommendationCard({
  recommendation
}: {
  recommendation: {
    action: string;
    message: string;
    risk_level: string;
  }
}) {
  const getActionIcon = () => {
    switch (recommendation.action) {
      case "CONSIDER_BUY":
        return <TrendingUp className="h-5 w-5 text-green-500" />;
      case "CONSIDER_SELL":
        return <TrendingDown className="h-5 w-5 text-red-500" />;
      case "WATCH":
        return <Eye className="h-5 w-5 text-yellow-500" />;
      default:
        return <Hand className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getActionLabel = () => {
    switch (recommendation.action) {
      case "CONSIDER_BUY":
        return "Considerer l'achat";
      case "CONSIDER_SELL":
        return "Considerer la vente";
      case "WATCH":
        return "Surveiller";
      default:
        return "Attendre";
    }
  };

  const getActionColor = () => {
    switch (recommendation.action) {
      case "CONSIDER_BUY":
        return "bg-green-500/10 border-green-500/30 text-green-500";
      case "CONSIDER_SELL":
        return "bg-red-500/10 border-red-500/30 text-red-500";
      case "WATCH":
        return "bg-yellow-500/10 border-yellow-500/30 text-yellow-500";
      default:
        return "bg-muted border-border text-muted-foreground";
    }
  };

  const getRiskColor = () => {
    switch (recommendation.risk_level) {
      case "LOW":
        return "text-green-500";
      case "MODERATE":
        return "text-yellow-500";
      default:
        return "text-red-500";
    }
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Target className="h-5 w-5" />
          Recommandation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className={`flex items-center gap-3 p-4 rounded-lg border ${getActionColor()}`}>
          {getActionIcon()}
          <span className="font-semibold text-lg">{getActionLabel()}</span>
        </div>

        <p className="text-sm text-muted-foreground">{recommendation.message}</p>

        <div className="flex items-center gap-2 text-sm">
          <ShieldAlert className={`h-4 w-4 ${getRiskColor()}`} />
          <span>Niveau de risque: </span>
          <span className={`font-semibold ${getRiskColor()}`}>
            {recommendation.risk_level === "LOW" ? "Faible" :
             recommendation.risk_level === "MODERATE" ? "Modere" : "Eleve"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// Composant principal
export default function PredictionPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { isConnected, isChecking } = useApiHealth();
  const { status: predictionStatus } = usePredictionStatus();
  const { prediction, isLoading, error, refresh } = usePrediction();
  const { data: marketData } = useMarketData({ refreshInterval: 30000 });

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await refresh();
    setIsRefreshing(false);
  };

  // Si le backend n'est pas connecté
  if (!isChecking && !isConnected) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Prediction IA</h1>
          <p className="text-muted-foreground">Prediction de la direction du BTC pour demain</p>
        </div>
        <Alert variant="destructive">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            <strong>Backend non connecte.</strong> Lancez le serveur avec :{" "}
            <code className="bg-muted px-1 rounded">cd backend && source venv/bin/activate && uvicorn main:app --reload</code>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Si le modèle n'existe pas
  if (!isLoading && predictionStatus && !predictionStatus.model_exists) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold">Prediction IA</h1>
          <p className="text-muted-foreground">Prediction de la direction du BTC pour demain</p>
        </div>

        <Alert>
          <Brain className="h-4 w-4" />
          <AlertTitle>Modele non disponible</AlertTitle>
          <AlertDescription className="mt-2 space-y-4">
            <p>
              Le modele LSTM n'a pas ete trouve. Suivez ces etapes pour l'activer :
            </p>
            <ol className="list-decimal list-inside space-y-2 text-sm">
              <li>Ouvrez le fichier <code className="bg-muted px-1 rounded">colab_option_B_classification.ipynb</code> dans Google Colab</li>
              <li>Executez toutes les cellules pour entrainer le modele</li>
              <li>Telechargez les 3 fichiers generes</li>
              <li>Placez-les dans <code className="bg-muted px-1 rounded">backend/app/ml/models/</code></li>
              <li>Redemarrez le backend</li>
            </ol>
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <p className="text-sm font-medium mb-2">Fichiers requis :</p>
              <ul className="text-sm space-y-1">
                <li className="flex items-center gap-2">
                  {predictionStatus?.model_exists ?
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> :
                    <XCircle className="h-4 w-4 text-red-500" />
                  }
                  btc_lstm_model_B.keras
                </li>
                <li className="flex items-center gap-2">
                  {predictionStatus?.scaler_exists ?
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> :
                    <XCircle className="h-4 w-4 text-red-500" />
                  }
                  btc_scaler_B.pkl
                </li>
                <li className="flex items-center gap-2">
                  {predictionStatus?.config_exists ?
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> :
                    <XCircle className="h-4 w-4 text-red-500" />
                  }
                  training_config_B.json
                </li>
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" />
            Prediction IA
          </h1>
          <p className="text-muted-foreground">Prediction de la direction du BTC par Deep Learning (LSTM)</p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={isLoading || isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Erreur */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Contenu principal */}
      {isLoading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-[250px]" />
          <Skeleton className="h-[250px]" />
          <Skeleton className="h-[200px]" />
          <Skeleton className="h-[200px]" />
        </div>
      ) : prediction ? (
        <>
          {/* Date et prix actuel */}
          <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
            <CardContent className="py-4">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="flex items-center gap-3">
                  <Calendar className="h-5 w-5 text-primary" />
                  <div>
                    <p className="text-sm text-muted-foreground">Prediction pour</p>
                    <p className="font-semibold">{formatDate(prediction.prediction_for)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-sm text-muted-foreground">Prix actuel BTC</p>
                    <p className="font-mono font-bold text-xl">${formatPrice(prediction.current_price.close)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Signal principal */}
          <DirectionSignal
            direction={prediction.prediction.direction}
            confidence={prediction.prediction.confidence}
            strength={prediction.prediction.signal_strength}
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Probabilités */}
            <ProbabilityBars probabilities={prediction.prediction.probabilities} />

            {/* Recommandation */}
            <RecommendationCard recommendation={prediction.recommendation} />
          </div>

          {/* Informations sur le modèle */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5" />
                Informations du Modele
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Type</p>
                  <p className="font-medium text-sm">{prediction.model_info.type}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Version</p>
                  <p className="font-medium">{prediction.model_info.version}</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Sequence</p>
                  <p className="font-medium">{prediction.model_info.sequence_length} jours</p>
                </div>
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-xs text-muted-foreground mb-1">Accuracy</p>
                  <p className="font-medium">
                    {prediction.model_info.metrics?.accuracy
                      ? `${(prediction.model_info.metrics.accuracy * 100).toFixed(1)}%`
                      : 'N/A'
                    }
                  </p>
                </div>
              </div>

              {/* Performance du modèle */}
              {prediction.model_info.metrics && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-sm font-medium mb-3">Performance du modele</p>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    <div className="text-center p-2 bg-muted/30 rounded">
                      <p className="text-xs text-muted-foreground">Accuracy</p>
                      <p className="font-mono text-sm font-bold text-green-500">
                        {(prediction.model_info.metrics.accuracy * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div className="text-center p-2 bg-muted/30 rounded">
                      <p className="text-xs text-muted-foreground">F1-Score</p>
                      <p className="font-mono text-sm">
                        {(prediction.model_info.metrics.f1_score * 100).toFixed(2)}%
                      </p>
                    </div>
                    <div className="text-center p-2 bg-muted/30 rounded">
                      <p className="text-xs text-muted-foreground">vs Random</p>
                      <p className="font-mono text-sm text-primary">
                        +{(prediction.model_info.metrics.improvement_over_random * 100).toFixed(2)}%
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Avertissement */}
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Avertissement</AlertTitle>
            <AlertDescription>
              Les predictions sont generees par un modele de deep learning avec une accuracy de ~54%.
              Ce n'est pas un conseil financier. Le modele a battu le Buy & Hold de +11.87% en backtest,
              mais les performances passees ne garantissent pas les resultats futurs.
              Faites toujours vos propres recherches.
            </AlertDescription>
          </Alert>
        </>
      ) : null}
    </div>
  );
}
