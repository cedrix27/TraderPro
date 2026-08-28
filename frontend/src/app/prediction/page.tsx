"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePrediction, usePredictionStatus, useApiHealth } from "@/hooks";
import { predictionApi, TTMPrediction, TTMStatus, PredictionComparison } from "@/lib/api/client";
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Calendar,
  AlertCircle,
  WifiOff,
  Brain,
  Target,
  ArrowUp,
  ArrowDown,
  Activity,
  Info,
  XCircle,
  ShieldAlert,
  Eye,
  Hand,
  Cpu,
  GitCompare
} from "lucide-react";

// Fonction pour formater le prix
function formatPrice(price: number): string {
  return price.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatPercentMetric(metrics: Record<string, unknown>, key: string): string {
  const value = metrics[key];
  return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "N/A";
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
  strength,
  modelName
}: {
  direction: "UP" | "DOWN";
  confidence: number;
  strength: string;
  modelName?: string;
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
            <p className="text-sm text-muted-foreground">
              Prediction {modelName ? `(${modelName})` : ""} pour demain
            </p>
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
  recommendation,
}: {
  recommendation: {
    action: string;
    message?: string;
    text?: string;
    risk_level?: string;
    confidence_level?: string;
    disclaimer?: string;
  };
}) {
  const getActionIcon = () => {
    switch (recommendation.action) {
      case "CONSIDER_BUY":
        return <TrendingUp className="h-5 w-5 text-green-500" />;
      case "CONSIDER_SELL":
        return <TrendingDown className="h-5 w-5 text-red-500" />;
      case "WATCH":
      case "HOLD_BULLISH":
      case "HOLD_BEARISH":
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
      case "HOLD_BULLISH":
        return "Surveiller (haussier)";
      case "HOLD_BEARISH":
        return "Surveiller (baissier)";
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
      case "HOLD_BULLISH":
      case "HOLD_BEARISH":
        return "bg-yellow-500/10 border-yellow-500/30 text-yellow-500";
      default:
        return "bg-muted border-border text-muted-foreground";
    }
  };

  const riskLevel = recommendation.risk_level || recommendation.confidence_level || "MODERATE";
  const getRiskColor = () => {
    switch (riskLevel) {
      case "LOW":
      case "STRONG":
        return "text-green-500";
      case "MODERATE":
        return "text-yellow-500";
      default:
        return "text-red-500";
    }
  };

  const message = recommendation.message || recommendation.text || "";

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

        <p className="text-sm text-muted-foreground">{message}</p>

        <div className="flex items-center gap-2 text-sm">
          <ShieldAlert className={`h-4 w-4 ${getRiskColor()}`} />
          <span>Niveau: </span>
          <span className={`font-semibold ${getRiskColor()}`}>
            {riskLevel === "LOW" || riskLevel === "WEAK" ? "Faible" :
             riskLevel === "MODERATE" ? "Modere" :
             riskLevel === "STRONG" ? "Fort" : "Eleve"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

// Composant pour le statut du modèle non disponible
function ModelNotAvailable({ modelName, files, notebook }: { modelName: string; files: string[]; notebook: string }) {
  return (
    <Alert>
      <Brain className="h-4 w-4" />
      <AlertTitle>Modele {modelName} non disponible</AlertTitle>
      <AlertDescription className="mt-2 space-y-4">
        <p>
          Le modele {modelName} n&apos;a pas ete trouve. Suivez ces etapes pour l&apos;activer :
        </p>
        <ol className="list-decimal list-inside space-y-2 text-sm">
          <li>Ouvrez le fichier <code className="bg-muted px-1 rounded">{notebook}</code> dans Google Colab</li>
          <li>Executez toutes les cellules pour entrainer le modele</li>
          <li>Telechargez les fichiers generes</li>
          <li>Placez-les dans le dossier indique</li>
          <li>Redemarrez le backend</li>
        </ol>
        <div className="mt-4 p-3 bg-muted rounded-lg">
          <p className="text-sm font-medium mb-2">Fichiers requis :</p>
          <ul className="text-sm space-y-1">
            {files.map((file) => (
              <li key={file} className="flex items-center gap-2">
                <XCircle className="h-4 w-4 text-red-500" />
                {file}
              </li>
            ))}
          </ul>
        </div>
      </AlertDescription>
    </Alert>
  );
}

// Composant pour la comparaison des modèles
function ModelComparison({ comparison }: { comparison: PredictionComparison }) {
  const { predictions, consensus } = comparison;

  return (
    <div className="space-y-6">
      {/* Consensus */}
      {consensus && (
        <Card className={`border-2 ${
          consensus.agreement === "FULL"
            ? "border-green-500/50 bg-green-500/5"
            : consensus.agreement === "NONE"
            ? "border-yellow-500/50 bg-yellow-500/5"
            : "border-blue-500/50 bg-blue-500/5"
        }`}>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GitCompare className="h-5 w-5" />
              Consensus des Modeles
            </CardTitle>
          </CardHeader>
          <CardContent>
            {consensus.agreement === "FULL" ? (
              <div className="flex items-center gap-4">
                <div className={`p-4 rounded-full ${consensus.direction === "UP" ? "bg-green-500/20" : "bg-red-500/20"}`}>
                  {consensus.direction === "UP" ? (
                    <ArrowUp className="h-10 w-10 text-green-500" />
                  ) : (
                    <ArrowDown className="h-10 w-10 text-red-500" />
                  )}
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {consensus.direction === "UP" ? "HAUSSE" : "BAISSE"}
                  </p>
                  <p className="text-muted-foreground">
                    Tous les modeles ({consensus.models_agreeing}) sont d&apos;accord
                  </p>
                  <p className="text-sm mt-1">
                    Confiance moyenne: <span className="font-bold">{consensus.avg_confidence?.toFixed(1)}%</span>
                  </p>
                </div>
              </div>
            ) : consensus.agreement === "NONE" ? (
              <div className="text-center py-4">
                <AlertCircle className="h-10 w-10 text-yellow-500 mx-auto mb-2" />
                <p className="text-lg font-semibold text-yellow-500">Signaux Contradictoires</p>
                <p className="text-muted-foreground mt-1">{consensus.recommendation}</p>
              </div>
            ) : (
              <div className="text-center py-4">
                <Info className="h-10 w-10 text-blue-500 mx-auto mb-2" />
                <p className="text-lg font-semibold">Un seul modele disponible</p>
                <p className="text-muted-foreground">
                  Modele: {consensus.model?.toUpperCase()} - Direction: {consensus.direction}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Détails par modèle */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* LSTM */}
        <Card className={predictions.lstm?.available ? "" : "opacity-50"}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Brain className="h-5 w-5" />
              LSTM
            </CardTitle>
            <CardDescription>Deep Learning (sequences)</CardDescription>
          </CardHeader>
          <CardContent>
            {predictions.lstm?.available ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {predictions.lstm.direction === "UP" ? (
                    <ArrowUp className="h-6 w-6 text-green-500" />
                  ) : (
                    <ArrowDown className="h-6 w-6 text-red-500" />
                  )}
                  <span className={`font-bold text-xl ${
                    predictions.lstm.direction === "UP" ? "text-green-500" : "text-red-500"
                  }`}>
                    {predictions.lstm.direction}
                  </span>
                </div>
                <Badge variant="outline">{predictions.lstm.confidence?.toFixed(1)}%</Badge>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{predictions.lstm?.error || "Non disponible"}</p>
            )}
          </CardContent>
        </Card>

        {/* TTM */}
        <Card className={predictions.ttm?.available ? "" : "opacity-50"}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Cpu className="h-5 w-5" />
              TTM
            </CardTitle>
            <CardDescription>Transformer (IBM)</CardDescription>
          </CardHeader>
          <CardContent>
            {predictions.ttm?.available ? (
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {predictions.ttm.direction === "UP" ? (
                    <ArrowUp className="h-6 w-6 text-green-500" />
                  ) : (
                    <ArrowDown className="h-6 w-6 text-red-500" />
                  )}
                  <span className={`font-bold text-xl ${
                    predictions.ttm.direction === "UP" ? "text-green-500" : "text-red-500"
                  }`}>
                    {predictions.ttm.direction}
                  </span>
                </div>
                <Badge variant="outline">{predictions.ttm.confidence?.toFixed(1)}%</Badge>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">{predictions.ttm?.error || "Non disponible"}</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// Composant principal
export default function PredictionPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("lstm");
  const { isConnected, isChecking } = useApiHealth();
  const { status: lstmStatus } = usePredictionStatus();
  const { prediction: lstmPrediction, isLoading: lstmLoading, error: lstmError, refresh: refreshLstm } = usePrediction();

  // États TTM
  const [ttmPrediction, setTtmPrediction] = useState<TTMPrediction | null>(null);
  const [ttmStatus, setTtmStatus] = useState<TTMStatus | null>(null);
  const [ttmLoading, setTtmLoading] = useState(false);
  const [ttmError, setTtmError] = useState<string | null>(null);

  // État comparaison
  const [comparison, setComparison] = useState<PredictionComparison | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);

  const loadTTMPrediction = useCallback(async () => {
    setTtmLoading(true);
    setTtmError(null);
    try {
      const pred = await predictionApi.getTTMPrediction();
      setTtmPrediction(pred);
    } catch (err: unknown) {
      setTtmError(err instanceof Error ? err.message : "Erreur lors du chargement de la prediction TTM");
    } finally {
      setTtmLoading(false);
    }
  }, []);

  const loadComparison = useCallback(async () => {
    setComparisonLoading(true);
    try {
      const comp = await predictionApi.comparePredictions();
      setComparison(comp);
    } catch (err) {
      console.error("Erreur comparaison:", err);
    } finally {
      setComparisonLoading(false);
    }
  }, []);

  // Charger le statut TTM au démarrage
  useEffect(() => {
    if (isConnected) {
      predictionApi.getTTMStatus().then(setTtmStatus).catch(() => {});
    }
  }, [isConnected]);

  // Charger les données en fonction de l'onglet actif
  useEffect(() => {
    if (!isConnected) return;

    if (activeTab === "ttm" && !ttmPrediction && !ttmLoading) {
      loadTTMPrediction();
    } else if (activeTab === "compare" && !comparison && !comparisonLoading) {
      loadComparison();
    }
  }, [activeTab, comparison, comparisonLoading, isConnected, loadComparison, loadTTMPrediction, ttmLoading, ttmPrediction]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    if (activeTab === "lstm") {
      await refreshLstm();
    } else if (activeTab === "ttm") {
      await predictionApi.refreshTTM();
      await loadTTMPrediction();
    } else if (activeTab === "compare") {
      await loadComparison();
    }
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" />
            Prediction IA
          </h1>
          <p className="text-muted-foreground">Predictions multi-modeles pour le BTC</p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={lstmLoading || ttmLoading || isRefreshing}
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </div>

      {/* Tabs pour les différents modèles */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="lstm" className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            LSTM
          </TabsTrigger>
          <TabsTrigger value="ttm" className="flex items-center gap-2">
            <Cpu className="h-4 w-4" />
            TTM (Transformer)
          </TabsTrigger>
          <TabsTrigger value="compare" className="flex items-center gap-2">
            <GitCompare className="h-4 w-4" />
            Comparaison
          </TabsTrigger>
        </TabsList>

        {/* Contenu LSTM */}
        <TabsContent value="lstm" className="space-y-6">
          {lstmError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{lstmError}</AlertDescription>
            </Alert>
          )}

          {!lstmLoading && lstmStatus && !lstmStatus.model_exists ? (
            <ModelNotAvailable
              modelName="LSTM"
              files={["btc_lstm_model_B.keras", "btc_scaler_B.pkl", "training_config_B.json"]}
              notebook="colab_option_B_classification.ipynb"
            />
          ) : lstmLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[200px]" />
              <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-[150px]" />
                <Skeleton className="h-[150px]" />
              </div>
            </div>
          ) : lstmPrediction ? (
            <>
              {/* Date et prix */}
              <Card className="bg-gradient-to-r from-primary/10 to-primary/5 border-primary/20">
                <CardContent className="py-4">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-primary" />
                      <div>
                        <p className="text-sm text-muted-foreground">Prediction pour</p>
                        <p className="font-semibold">{formatDate(lstmPrediction.prediction_for)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Prix actuel BTC</p>
                      <p className="font-mono font-bold text-xl">${formatPrice(lstmPrediction.current_price.close)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <DirectionSignal
                direction={lstmPrediction.prediction.direction}
                confidence={lstmPrediction.prediction.confidence}
                strength={lstmPrediction.prediction.signal_strength}
                modelName="LSTM"
              />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ProbabilityBars probabilities={lstmPrediction.prediction.probabilities} />
                <RecommendationCard recommendation={lstmPrediction.recommendation} />
              </div>

              {/* Info modèle */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Info className="h-5 w-5" />
                    Modele LSTM
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Type</p>
                      <p className="font-medium text-sm">{lstmPrediction.model_info.type}</p>
                    </div>
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Version</p>
                      <p className="font-medium">{lstmPrediction.model_info.version}</p>
                    </div>
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Sequence</p>
                      <p className="font-medium">{lstmPrediction.model_info.sequence_length} jours</p>
                    </div>
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Accuracy</p>
                      <p className="font-medium">
                        {formatPercentMetric(lstmPrediction.model_info.metrics, "accuracy")}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : null}
        </TabsContent>

        {/* Contenu TTM */}
        <TabsContent value="ttm" className="space-y-6">
          {ttmError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{ttmError}</AlertDescription>
            </Alert>
          )}

          {!ttmLoading && ttmStatus && !ttmStatus.model_exists ? (
            <ModelNotAvailable
              modelName="TTM (Tiny Time Mixer)"
              files={ttmStatus.required_files || ["config.json", "model.safetensors", "preprocessor.pkl", "ttm_config.json"]}
              notebook="colab_ttm_finetuning.ipynb"
            />
          ) : ttmLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[200px]" />
              <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-[150px]" />
                <Skeleton className="h-[150px]" />
              </div>
            </div>
          ) : ttmPrediction ? (
            <>
              {/* Date et prix */}
              <Card className="bg-gradient-to-r from-purple-500/10 to-purple-500/5 border-purple-500/20">
                <CardContent className="py-4">
                  <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div className="flex items-center gap-3">
                      <Calendar className="h-5 w-5 text-purple-500" />
                      <div>
                        <p className="text-sm text-muted-foreground">Prediction TTM pour</p>
                        <p className="font-semibold">{formatDate(ttmPrediction.prediction_for)}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-muted-foreground">Prix actuel BTC</p>
                      <p className="font-mono font-bold text-xl">${formatPrice(ttmPrediction.current_price.close)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <DirectionSignal
                direction={ttmPrediction.prediction.direction}
                confidence={ttmPrediction.prediction.confidence}
                strength={ttmPrediction.prediction.signal_strength}
                modelName="TTM"
              />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ProbabilityBars probabilities={ttmPrediction.prediction.probabilities} />
                <RecommendationCard recommendation={ttmPrediction.recommendation} />
              </div>

              {/* Info modèle TTM */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Cpu className="h-5 w-5" />
                    Modele TTM (Tiny Time Mixer)
                  </CardTitle>
                  <CardDescription>Transformer d&apos;IBM pour les series temporelles</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Type</p>
                      <p className="font-medium text-sm">{ttmPrediction.model_info.type}</p>
                    </div>
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Base</p>
                      <p className="font-medium text-xs truncate">{ttmPrediction.model_info.base_model}</p>
                    </div>
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Context</p>
                      <p className="font-medium">{ttmPrediction.model_info.context_length} jours</p>
                    </div>
                    <div className="p-3 bg-muted/50 rounded-lg">
                      <p className="text-xs text-muted-foreground mb-1">Direction Acc.</p>
                      <p className="font-medium">
                        {formatPercentMetric(ttmPrediction.model_info.metrics, "direction_accuracy")}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Disclaimer TTM */}
              {ttmPrediction.recommendation.disclaimer && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{ttmPrediction.recommendation.disclaimer}</AlertDescription>
                </Alert>
              )}
            </>
          ) : (
            <div className="text-center py-8">
              <Cpu className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Cliquez sur Actualiser pour charger la prediction TTM</p>
            </div>
          )}
        </TabsContent>

        {/* Contenu Comparaison */}
        <TabsContent value="compare" className="space-y-6">
          {comparisonLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-[150px]" />
              <div className="grid grid-cols-2 gap-4">
                <Skeleton className="h-[120px]" />
                <Skeleton className="h-[120px]" />
              </div>
            </div>
          ) : comparison ? (
            <ModelComparison comparison={comparison} />
          ) : (
            <div className="text-center py-8">
              <GitCompare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Cliquez sur Actualiser pour comparer les modeles</p>
              <Button variant="outline" className="mt-4" onClick={loadComparison}>
                Charger la comparaison
              </Button>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Avertissement global */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Avertissement</AlertTitle>
        <AlertDescription>
          Les predictions sont generees par des modeles d&apos;intelligence artificielle.
          Ce n&apos;est pas un conseil financier. Les performances passees ne garantissent pas les resultats futurs.
          Faites toujours vos propres recherches avant de prendre des decisions d&apos;investissement.
        </AlertDescription>
      </Alert>
    </div>
  );
}
