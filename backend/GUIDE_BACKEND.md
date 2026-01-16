# Guide Complet du Backend TraderPro

## Pour les Débutants - Explications Détaillées

---

## Table des Matières

1. [Introduction](#1-introduction)
2. [Structure du Projet](#2-structure-du-projet)
3. [Les Bonnes Pratiques Utilisées](#3-les-bonnes-pratiques-utilisées)
4. [Explication de Chaque Fichier](#4-explication-de-chaque-fichier)
5. [Le Flux des Données](#5-le-flux-des-données)
6. [Le Machine Learning Expliqué](#6-le-machine-learning-expliqué)
7. [Le Reinforcement Learning (RL)](#7-le-reinforcement-learning-rl)
8. [Glossaire des Termes](#8-glossaire-des-termes)

---

## 1. Introduction

### Qu'est-ce qu'un Backend ?

Imagine une application comme un restaurant :
- Le **Frontend** (NextJS) = La salle du restaurant (ce que voit le client)
- Le **Backend** (FastAPI) = La cuisine (où tout est préparé)
- L'**API** = Le serveur qui fait le lien entre les deux

Le backend est le "cerveau" de l'application. Il :
- Récupère les données (prix Bitcoin depuis Binance)
- Fait les calculs (indicateurs techniques)
- Prend les décisions (signaux de trading via l'IA)
- Envoie les résultats au frontend

### Pourquoi Python + FastAPI ?

```
Python     → Langage idéal pour le Machine Learning et l'analyse de données
FastAPI    → Framework web moderne, rapide, avec documentation automatique
```

FastAPI génère automatiquement une documentation interactive de ton API accessible sur `/docs`.

---

## 2. Structure du Projet

```
backend/
│
├── main.py                 # Point d'entrée - Lance le serveur
├── requirements.txt        # Liste des dépendances Python
├── .env.example           # Modèle pour les variables d'environnement
│
├── app/                    # Code principal de l'application
│   ├── __init__.py        # Marque ce dossier comme un "package" Python
│   │
│   ├── api/               # Tout ce qui concerne l'API (les routes/endpoints)
│   │   ├── __init__.py
│   │   └── routes.py      # Définition des endpoints (URLs)
│   │
│   ├── core/              # Configuration et modèles de base
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration de l'application
│   │   └── models.py      # Définition des structures de données
│   │
│   ├── services/          # La logique métier (le "travail")
│   │   ├── __init__.py
│   │   ├── binance_service.py     # Communication avec Binance
│   │   ├── indicators_service.py  # Calcul des indicateurs
│   │   └── analysis_service.py    # Analyse et signaux
│   │
│   └── ml/                # Machine Learning
│       ├── __init__.py
│       ├── features.py    # Création des features (variables)
│       └── model.py       # Le modèle de prédiction
│
├── scripts/               # Scripts utilitaires
│   └── train_model.py     # Script pour entraîner le modèle
│
├── models/                # Dossier pour sauvegarder les modèles ML
├── data/                  # Dossier pour les données
└── venv/                  # Environnement virtuel Python
```

### Pourquoi cette structure ?

Cette organisation suit le principe de **Séparation des Responsabilités** :
- Chaque dossier a UN rôle précis
- Facile à maintenir et faire évoluer
- Standard dans l'industrie

---

## 3. Les Bonnes Pratiques Utilisées

### 3.1 Environnement Virtuel (venv)

```bash
# Créer un environnement virtuel
python -m venv venv

# L'activer
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
```

**Pourquoi ?**
- Isole les dépendances du projet
- Évite les conflits entre projets
- Garantit que tout le monde utilise les mêmes versions

### 3.2 Variables d'Environnement (.env)

```bash
# .env (NE JAMAIS COMMITER CE FICHIER !)
BINANCE_API_KEY=ta_clé_secrète
BINANCE_API_SECRET=ton_secret
```

**Pourquoi ?**
- Sécurité : Les secrets ne sont pas dans le code
- Flexibilité : Différentes configs pour dev/prod

### 3.3 Type Hints (Typage Python)

```python
# Sans typage (difficile à comprendre)
def calculate_rsi(data, period):
    ...

# Avec typage (clair et documenté)
def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    ...
```

**Pourquoi ?**
- Code plus lisible
- Erreurs détectées plus tôt
- Auto-complétion dans l'IDE

### 3.4 Modèles Pydantic

```python
class TradingSignal(BaseModel):
    action: str           # "BUY", "SELL", "HOLD"
    confidence: float     # 0-100
    entry: float          # Prix d'entrée
```

**Pourquoi ?**
- Validation automatique des données
- Documentation automatique de l'API
- Sérialisation JSON automatique

### 3.5 Pattern Singleton

```python
# À la fin de chaque service
binance_service = BinanceService()  # Une seule instance
```

**Pourquoi ?**
- Une seule connexion à Binance
- Économise les ressources
- État partagé si nécessaire

### 3.6 Async/Await (Asynchrone)

```python
async def get_price():
    data = await binance_api.fetch()  # N'attend pas, fait autre chose
    return data
```

**Pourquoi ?**
- Gère plusieurs requêtes simultanément
- Beaucoup plus rapide
- Essentiel pour les APIs web modernes

---

## 4. Explication de Chaque Fichier

---

### 4.1 `main.py` - Le Point d'Entrée

```python
"""
C'est le fichier principal qui lance tout le serveur.
Comme la clé de contact d'une voiture.
"""

# Création de l'application FastAPI
app = FastAPI(
    title="TraderPro API",
    description="...",
    version="1.0.0"
)

# Configuration CORS (permet au frontend de communiquer avec le backend)
app.add_middleware(CORSMiddleware, ...)

# Inclusion des routes (les URLs disponibles)
app.include_router(router)
```

**Ce que fait ce fichier :**
1. Crée l'application FastAPI
2. Configure les paramètres (CORS, titre, etc.)
3. Charge le modèle ML au démarrage (si disponible)
4. Définit ce qui se passe au démarrage et à l'arrêt

**Pour lancer :**
```bash
uvicorn main:app --reload
# uvicorn = serveur web
# main:app = fichier main.py, variable app
# --reload = redémarre automatiquement si le code change
```

---

### 4.2 `requirements.txt` - Les Dépendances

```
fastapi==0.115.6      # Framework web
uvicorn==0.34.0       # Serveur ASGI
pandas==2.2.3         # Manipulation de données
numpy==2.2.0          # Calculs numériques
xgboost==2.1.3        # Algorithme de Machine Learning
...
```

**Ce que fait ce fichier :**
- Liste toutes les bibliothèques nécessaires
- Fixe les versions pour éviter les incompatibilités

**Pour installer :**
```bash
pip install -r requirements.txt
```

---

### 4.3 `app/core/config.py` - La Configuration

```python
class Settings(BaseSettings):
    """
    Toutes les configurations de l'application.
    Les valeurs peuvent être surchargées par des variables d'environnement.
    """

    # Configuration de l'app
    app_name: str = "TraderPro API"
    debug: bool = True

    # Binance
    binance_api_key: Optional[str] = None

    # Trading
    default_symbol: str = "BTCUSDT"
    default_timeframe: str = "1h"
```

**Ce que fait ce fichier :**
- Centralise TOUTE la configuration
- Charge automatiquement les variables d'environnement
- Fournit des valeurs par défaut

**Pourquoi c'est important :**
- Un seul endroit pour tout modifier
- Pas de valeurs "magiques" dispersées dans le code

---

### 4.4 `app/core/models.py` - Les Modèles de Données

```python
"""
Ce fichier définit la STRUCTURE des données.
C'est comme un dictionnaire qui dit :
"Un signal de trading DOIT avoir ces champs avec ces types"
"""

class TradingSignal(BaseModel):
    action: SignalType        # BUY, SELL, ou HOLD
    confidence: float         # Niveau de confiance (0-100)
    entry: float              # Prix d'entrée suggéré
    stop_loss: float          # Prix de stop loss
    take_profit: float        # Prix de take profit
    risk_reward: float        # Ratio risque/récompense
    reasoning: List[str]      # Raisons du signal
```

**Les principaux modèles :**

| Modèle | Description |
|--------|-------------|
| `OHLCV` | Une bougie (Open, High, Low, Close, Volume) |
| `MarketData` | Données de marché en temps réel |
| `Indicator` | Un indicateur technique (RSI, MACD...) |
| `SupportResistance` | Un niveau de support ou résistance |
| `TradingSignal` | Le signal généré par l'IA |
| `TechnicalAnalysis` | L'analyse complète |

**Pourquoi utiliser des modèles :**
1. **Validation** : Si tu envoies un mauvais type, erreur immédiate
2. **Documentation** : L'API sait quoi attendre et retourner
3. **Auto-complétion** : Ton IDE te suggère les champs

---

### 4.5 `app/services/binance_service.py` - Le Client Binance

```python
"""
Ce service communique avec l'API Binance pour récupérer :
- Le prix actuel du Bitcoin
- Les données historiques (bougies/klines)
- Le carnet d'ordres
- Les trades récents
"""

class BinanceService:
    BASE_URL = "https://api.binance.com/api/v3"

    async def get_current_price(self, symbol: str = "BTCUSDT") -> MarketData:
        """
        Récupère le prix actuel et les stats des dernières 24h

        Appelle: GET /api/v3/ticker/24hr?symbol=BTCUSDT

        Retourne:
        - Prix actuel
        - Variation 24h (en $ et en %)
        - Plus haut/plus bas 24h
        - Volume 24h
        """
        data = await self._request("ticker/24hr", {"symbol": symbol})
        return MarketData(
            price=float(data["lastPrice"]),
            change_24h=float(data["priceChange"]),
            ...
        )

    async def get_klines(self, symbol, interval, limit) -> List[OHLCV]:
        """
        Récupère les données OHLCV (bougies)

        Une "bougie" représente une période de temps :
        - Open: Prix d'ouverture
        - High: Prix le plus haut
        - Low: Prix le plus bas
        - Close: Prix de fermeture
        - Volume: Quantité échangée

        Exemple pour une bougie 1h :
        [timestamp, open, high, low, close, volume]
        [1700000000, 97000, 97500, 96800, 97200, 1234.5]
        """
        ...
```

**Points clés :**

1. **Asynchrone** (`async/await`) : Permet de faire plusieurs requêtes en parallèle

2. **Pas besoin de clé API** : Les données publiques sont accessibles sans authentification

3. **Gestion des erreurs** : Le service gère les erreurs réseau et API

**Comment Binance structure ses données :**
```
Une requête klines retourne :
[
  [
    1499040000000,      // Timestamp d'ouverture
    "0.01634000",       // Open
    "0.80000000",       // High
    "0.01575800",       // Low
    "0.01577100",       // Close
    "148976.11427815",  // Volume
    ...
  ]
]
```

---

### 4.6 `app/services/indicators_service.py` - Les Indicateurs Techniques

```python
"""
Ce service calcule les indicateurs techniques utilisés par les traders.
Chaque indicateur donne une information différente sur le marché.
"""

class IndicatorsService:

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) - Indicateur de MOMENTUM

        Qu'est-ce que c'est ?
        --------------------
        Le RSI mesure la vitesse et l'amplitude des mouvements de prix.
        Il oscille entre 0 et 100.

        Comment l'interpréter ?
        ----------------------
        - RSI < 30  → "Survendu" → Le prix a trop baissé → Signal d'ACHAT potentiel
        - RSI > 70  → "Suracheté" → Le prix a trop monté → Signal de VENTE potentiel
        - RSI 30-70 → Zone neutre

        Formule simplifiée :
        -------------------
        RSI = 100 - (100 / (1 + RS))
        RS = Moyenne des hausses / Moyenne des baisses
        """
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
```

**Les indicateurs calculés :**

| Indicateur | Type | Ce qu'il mesure |
|------------|------|-----------------|
| **RSI** | Momentum | Force du mouvement (suracheté/survendu) |
| **MACD** | Tendance | Direction et force de la tendance |
| **Bollinger Bands** | Volatilité | Écart par rapport à la moyenne |
| **SMA/EMA** | Tendance | Moyenne des prix (tendance) |
| **ATR** | Volatilité | Amplitude moyenne des mouvements |

**Visualisation du RSI :**
```
100 ─────────────────────────────── Suracheté (vendre?)
 70 - - - - - - - - - - - - - - - -
    │    /\      /\
    │   /  \    /  \    /\
 50 │──/────\──/────\──/──\────────
    │ /      \/      \/    \
 30 - - - - - - - - - - - - - - - -
  0 ─────────────────────────────── Survendu (acheter?)
```

---

### 4.7 `app/services/analysis_service.py` - L'Analyse Complète

```python
"""
Ce service combine TOUS les indicateurs pour générer une analyse
et un signal de trading.

C'est ici que la "magie" opère : transformer les données brutes
en décision actionnable (BUY/SELL/HOLD).
"""

class AnalysisService:
    """
    LOGIQUE D'UN TRADER PROFESSIONNEL
    ==================================

    1. CONTEXTE (Vue d'ensemble)
       → Quelle est la tendance générale ?
       → Le marché monte, descend ou stagne ?

    2. ZONES CLÉS
       → Où sont les supports (planchers) ?
       → Où sont les résistances (plafonds) ?

    3. TIMING (Confirmation)
       → Les indicateurs confirment-ils ?
       → Y a-t-il convergence de signaux ?

    4. GESTION DU RISQUE
       → Où mettre le stop-loss ?
       → Quel ratio risk/reward ?

    5. DÉCISION
       → BUY, SELL, ou HOLD ?
    """

    def _generate_trading_signal(self, df, analysis_data) -> TradingSignal:
        """
        Génère le signal final basé sur un système de score.

        Comment ça marche :
        ------------------
        1. On part d'un score de 0
        2. Chaque indicateur BULLISH ajoute +1
        3. Chaque indicateur BEARISH ajoute -1
        4. Si score >= 3 → BUY
        5. Si score <= -3 → SELL
        6. Sinon → HOLD

        Exemple :
        - RSI = bullish (+1)
        - MACD = bullish (+1)
        - Prix > MA50 = bullish (+1)
        - Prix > MA200 = bullish (+1)
        - Volume = neutral (0)

        Score = 4 → Signal BUY
        """
        score = 0
        reasoning = []

        # Compter les signaux
        for indicator in analysis_data["indicators"]:
            if indicator.signal == "bullish":
                score += 1
            elif indicator.signal == "bearish":
                score -= 1

        # Déterminer l'action
        if score >= 3:
            action = "BUY"
        elif score <= -3:
            action = "SELL"
        else:
            action = "HOLD"

        return TradingSignal(action=action, ...)
```

**Le flux de l'analyse :**
```
Données Binance (OHLCV)
        │
        ▼
┌───────────────────┐
│ Calcul Indicateurs│ (RSI, MACD, BB, MA...)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Détection S/R     │ (Support, Résistance)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Calcul du Score   │ (somme des signaux)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ Génération Signal │ (BUY/SELL/HOLD + Entry/SL/TP)
└───────────────────┘
        │
        ▼
    Résultat Final
```

---

### 4.8 `app/ml/features.py` - Feature Engineering

```python
"""
FEATURE ENGINEERING = L'art de transformer les données brutes
en informations que le Machine Learning peut comprendre.

C'est l'étape LA PLUS IMPORTANTE du ML.
Un bon feature engineering > Un algorithme complexe

Analogie :
- Données brutes = Ingrédients crus
- Features = Ingrédients préparés et assaisonnés
- Modèle ML = Le chef qui cuisine
"""

class FeatureEngineering:

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforme les données OHLCV en features utilisables.

        TYPES DE FEATURES CRÉÉES :

        1. FEATURES DE PRIX
           - returns : Variation en % (combien le prix a bougé)
           - log_returns : Log du ratio (plus stable mathématiquement)
           - body_size : Taille du corps de la bougie

        2. FEATURES DE VOLUME
           - volume_change : Le volume augmente ou diminue ?
           - volume_ma_ratio : Volume actuel vs moyenne

        3. FEATURES D'INDICATEURS
           - rsi : RSI normalisé entre 0 et 1
           - macd_histogram : Force du MACD
           - bb_position : Position dans les Bollinger Bands

        4. FEATURES TEMPORELLES
           - hour : Heure de la journée (0-23)
           - day_of_week : Jour de la semaine (0-6)

        5. FEATURES STATISTIQUES
           - rolling_mean : Moyenne sur N périodes
           - momentum : Prix actuel / Prix il y a N périodes
        """
        features = pd.DataFrame()

        # Exemple : Returns (variation de prix)
        features['returns'] = df['close'].pct_change()
        # Si prix passe de 100 à 102, returns = 0.02 (2%)

        # Exemple : RSI normalisé
        rsi = self.calculate_rsi(df)
        features['rsi'] = rsi / 100  # Ramène entre 0 et 1

        # Exemple : Position par rapport à MA50
        ma50 = df['close'].rolling(50).mean()
        features['above_ma50'] = (df['close'] > ma50).astype(int)
        # 1 si le prix est au-dessus, 0 sinon

        return features

    def create_target(self, df, horizon=4, threshold=0.02) -> pd.Series:
        """
        Crée la variable CIBLE (ce qu'on veut prédire).

        LABELLING = Dire au modèle "voici la bonne réponse"

        On utilise le FUTUR pour créer les labels :
        - Si dans 4h le prix monte de +2% → Label = BUY (1)
        - Si dans 4h le prix baisse de -2% → Label = SELL (-1)
        - Sinon → Label = HOLD (0)

        C'est du "hindsight" (regard en arrière) :
        On sait ce qui s'est passé, donc on peut labelliser.

        Exemple :

        Temps    Prix     Future_Return    Label
        T0       100      +3%              BUY (1)
        T1       101      -1%              HOLD (0)
        T2       102      -4%              SELL (-1)
        T3       99       +2.5%            BUY (1)
        """
        future_return = df['close'].shift(-horizon) / df['close'] - 1

        target = pd.Series(0, index=df.index)  # Par défaut HOLD
        target[future_return > threshold] = 1   # BUY
        target[future_return < -threshold] = -1 # SELL

        return target
```

**Visualisation du Feature Engineering :**
```
Données brutes (OHLCV)           Features créées
┌─────────────────────┐         ┌────────────────────────┐
│ open  high low close│         │ returns  rsi  macd ... │
├─────────────────────┤    →    ├────────────────────────┤
│ 100   102  99  101  │         │ 0.01    0.55  0.02 ... │
│ 101   103  100 102  │         │ 0.01    0.58  0.03 ... │
│ 102   105  101 104  │         │ 0.02    0.62  0.05 ... │
└─────────────────────┘         └────────────────────────┘
     5 colonnes                      50+ colonnes
```

---

### 4.9 `app/ml/model.py` - Le Modèle XGBoost

```python
"""
Ce fichier contient le modèle de Machine Learning.

POURQUOI XGBOOST ?
==================
- Très performant sur les données tabulaires (tableaux)
- Rapide à entraîner
- Interprétable (on peut voir quelles features sont importantes)
- Standard de l'industrie pour ce type de problème

COMMENT ÇA MARCHE ?
===================
XGBoost = "Extreme Gradient Boosting"

Imagine 100 "experts" (arbres de décision) qui votent :
- Expert 1 : "Je pense BUY car RSI < 30"
- Expert 2 : "Je pense BUY car prix > MA200"
- Expert 3 : "Je pense SELL car MACD négatif"
- ...

Le vote majoritaire donne la décision finale.

Chaque expert corrige les erreurs des précédents (boosting).
"""

class TradingModel:

    def train(self, df: pd.DataFrame, horizon=4, threshold=0.02):
        """
        Entraîne le modèle sur les données historiques.

        ÉTAPES :

        1. PRÉPARER LES DONNÉES
           - Créer les features (X)
           - Créer les labels (y)

        2. SPLIT TEMPOREL
           - 80% pour l'entraînement
           - 20% pour le test
           - IMPORTANT : On ne mélange pas ! (pas de data leakage)

        3. NORMALISATION
           - Mettre toutes les features sur la même échelle
           - Ex: RSI (0-100) et returns (-0.1 à 0.1) → tout entre 0 et 1

        4. ENTRAÎNEMENT
           - Le modèle apprend les patterns
           - "Quand RSI < 30 ET prix > MA200, souvent ça monte"

        5. ÉVALUATION
           - Tester sur les 20% non vus
           - Calculer l'accuracy, precision, recall
        """

        # 1. Préparer les données
        X, y = feature_engineering.prepare_training_data(df, horizon, threshold)

        # 2. Split temporel (PAS de shuffle pour le trading !)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # 3. Normalisation
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 4. Entraînement
        self.model = xgb.XGBClassifier(
            n_estimators=200,    # 200 "experts"
            max_depth=6,         # Complexité de chaque expert
            learning_rate=0.1,   # Vitesse d'apprentissage
        )
        self.model.fit(X_train_scaled, y_train)

        # 5. Évaluation
        accuracy = self.model.score(X_test_scaled, y_test)
        print(f"Accuracy: {accuracy:.2%}")

    def predict(self, df: pd.DataFrame) -> Tuple[int, float, dict]:
        """
        Fait une prédiction sur les données actuelles.

        Entrée : DataFrame OHLCV récent
        Sortie :
          - signal : 1 (BUY), 0 (HOLD), -1 (SELL)
          - confidence : Niveau de confiance (%)
          - probabilities : Probabilités pour chaque classe

        Exemple de sortie :
        {
            "signal": 1,
            "confidence": 72.5,
            "probabilities": {
                "BUY": 72.5,
                "HOLD": 18.3,
                "SELL": 9.2
            }
        }
        """
        # Créer les features actuelles
        features = feature_engineering.create_features(df)
        X = features.iloc[[-1]]  # Dernière ligne

        # Normaliser
        X_scaled = self.scaler.transform(X)

        # Prédire
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]

        return prediction, max(probabilities) * 100, probabilities
```

**Visualisation de l'entraînement :**
```
Données historiques (90 jours)
│
├─────────────────────────────┬───────────────┐
│      TRAIN (80%)            │   TEST (20%)  │
│      72 jours               │   18 jours    │
└─────────────────────────────┴───────────────┘
        │                            │
        ▼                            ▼
   Le modèle                    Évaluation
   apprend ici                  (accuracy)
```

**ATTENTION au Data Leakage :**
```
❌ MAUVAIS : Mélanger les données (shuffle)
   → Le modèle "voit" le futur
   → Résultats trop optimistes

✅ BON : Split temporel
   → Train = passé
   → Test = futur proche
   → Résultats réalistes
```

---

### 4.10 `app/api/routes.py` - Les Endpoints

```python
"""
Ce fichier définit les URLs (endpoints) de l'API.

Chaque endpoint est une "porte d'entrée" pour le frontend.

ANATOMIE D'UN ENDPOINT :
========================

@router.get("/api/analysis")     ← Décorateur (GET = lecture)
async def get_analysis(          ← Fonction async
    symbol: str = "BTCUSDT"      ← Paramètre avec valeur par défaut
) -> TechnicalAnalysis:          ← Type de retour
    '''Documentation'''          ← Docstring (affichée dans /docs)
    return await analysis_service.get_full_analysis(symbol)
"""

# ENDPOINTS MARKET DATA

@router.get("/market/price")
async def get_current_price(symbol: str = "BTCUSDT"):
    """
    Récupère le prix actuel du Bitcoin.

    Exemple d'appel :
    GET http://localhost:8000/api/market/price?symbol=BTCUSDT

    Réponse :
    {
        "symbol": "BTCUSDT",
        "price": 97245.32,
        "change_24h": 1523.45,
        "change_percent_24h": 1.59,
        "high_24h": 98450.00,
        "low_24h": 95120.00,
        "volume_24h": 32500000000
    }
    """
    return await binance_service.get_current_price(symbol)


# ENDPOINTS ANALYSIS

@router.get("/analysis")
async def get_full_analysis(symbol: str = "BTCUSDT", timeframe: str = "1h"):
    """
    Obtient une analyse technique COMPLÈTE.

    Inclut :
    - Tendance et force
    - Tous les indicateurs
    - Supports/Résistances
    - Signal de trading
    - Résumé textuel

    C'est l'endpoint principal pour l'analyse.
    """
    return await analysis_service.get_full_analysis(symbol, timeframe)


# ENDPOINTS ML

@router.get("/predict")
async def get_ml_prediction(symbol: str = "BTCUSDT"):
    """
    Obtient une prédiction du modèle ML.

    ATTENTION : Le modèle doit être entraîné d'abord !
    Utilisez POST /api/model/train avant.

    Réponse :
    {
        "signal": "BUY",
        "confidence": 72.5,
        "probabilities": {
            "BUY": 72.5,
            "HOLD": 18.3,
            "SELL": 9.2
        }
    }
    """
    if not trading_model.is_trained:
        raise HTTPException(400, "Modèle non entraîné")

    df = await binance_service.get_historical_data(symbol)
    signal, confidence, probs = trading_model.predict(df)

    return {"signal": signal, "confidence": confidence, ...}


@router.post("/model/train")
async def train_model(days: int = 90, horizon: int = 4):
    """
    Entraîne le modèle ML.

    Paramètres :
    - days : Nombre de jours de données (défaut 90)
    - horizon : Périodes de prédiction (défaut 4)

    Cette opération peut prendre plusieurs minutes !
    """
    df = await binance_service.get_historical_data("BTCUSDT", days=days)
    metrics = trading_model.train(df, horizon=horizon)
    trading_model.save()

    return {"status": "success", "metrics": metrics}
```

**Les méthodes HTTP :**
```
GET    → Lire des données (ne modifie rien)
POST   → Créer/Envoyer des données
PUT    → Mettre à jour des données
DELETE → Supprimer des données
```

**Comment tester les endpoints :**
```bash
# Avec curl
curl http://localhost:8000/api/market/price

# Avec le navigateur
http://localhost:8000/docs  ← Interface interactive !
```

---

## 5. Le Flux des Données

Voici comment les données circulent dans l'application :

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (NextJS)                        │
│                                                                  │
│  Dashboard    Analyse    Plans    Assistant                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTP Requests (fetch/axios)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API ROUTES (FastAPI)                        │
│                                                                  │
│  /api/market/price  /api/analysis  /api/predict  /api/chat      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Appels de services
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Binance   │  │ Indicators │  │  Analysis  │
    │  Service   │  │  Service   │  │  Service   │
    └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
          │               │               │
          │               └───────┬───────┘
          │                       │
          ▼                       ▼
    ┌────────────┐         ┌────────────┐
    │  Binance   │         │     ML     │
    │    API     │         │   Model    │
    │ (externe)  │         │ (XGBoost)  │
    └────────────┘         └────────────┘
```

**Exemple concret - Obtenir une analyse :**

```
1. Frontend appelle GET /api/analysis?symbol=BTCUSDT

2. routes.py reçoit la requête
   → Appelle analysis_service.get_full_analysis()

3. analysis_service
   → Appelle binance_service.get_historical_data()
   → Appelle indicators_service.calculate_all_indicators()
   → Génère le signal de trading

4. Réponse JSON envoyée au frontend

5. Frontend affiche les données
```

---

## 6. Le Machine Learning Expliqué

### 6.1 Qu'est-ce que le Machine Learning ?

```
PROGRAMMATION CLASSIQUE :
Données + Règles → Résultat

Exemple :
if rsi < 30:
    return "BUY"
elif rsi > 70:
    return "SELL"

MACHINE LEARNING :
Données + Résultats attendus → Règles (apprises)

Exemple :
Le modèle apprend seul que :
"Quand RSI < 30 ET MACD positif ET volume élevé → souvent BUY est bon"
```

### 6.2 Types de Machine Learning

```
┌─────────────────────────────────────────────────────────────┐
│                    MACHINE LEARNING                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│   SUPERVISÉ     │  NON-SUPERVISÉ  │    REINFORCEMENT        │
│                 │                 │                         │
│ On donne les    │ Pas de labels   │ L'agent apprend         │
│ bonnes réponses │ Le modèle trouve│ par essai-erreur        │
│                 │ des patterns    │                         │
│ Ex: XGBoost     │ Ex: K-Means     │ Ex: Deep Q-Network      │
│ (notre choix)   │ (clustering)    │ (trading automatique)   │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 6.3 Notre Approche : Classification Supervisée

```
OBJECTIF : Prédire si le prix va monter, descendre, ou stagner

ENTRÉES (Features) :
- RSI, MACD, Bollinger Bands
- Moyennes mobiles
- Volume
- Patterns temporels
- ~50 features au total

SORTIE (Classes) :
- BUY (1)   → Le prix va monter de +2%
- HOLD (0)  → Le prix va stagner
- SELL (-1) → Le prix va baisser de -2%

PROCESSUS :
1. Collecter 90 jours de données
2. Créer les features
3. Labelliser (en regardant le futur)
4. Entraîner XGBoost
5. Évaluer sur données non vues
```

### 6.4 Métriques Importantes

```
ACCURACY (Précision globale)
= Prédictions correctes / Total
= 55% est déjà bon pour le trading !

PRECISION (Quand je dis BUY, est-ce vraiment BUY ?)
= Vrais BUY / (Vrais BUY + Faux BUY)
= Important pour ne pas perdre d'argent

RECALL (Est-ce que je capte tous les BUY ?)
= Vrais BUY / (Vrais BUY + BUY manqués)
= Important pour ne pas rater d'opportunités

CONFUSION MATRIX :
                    Prédit
                 BUY  HOLD  SELL
Réel   BUY      [45]   10     5     ← Sur 60 vrais BUY, 45 bien prédits
       HOLD       8   [32]    10
       SELL       7    12   [31]
```

---

## 7. Le Reinforcement Learning (RL)

### 7.1 Introduction au Reinforcement Learning

Le Reinforcement Learning est une approche **fondamentalement différente** du Machine Learning supervisé (LSTM, XGBoost). C'est la prochaine étape pour rendre TraderPro plus intelligent.

```
┌─────────────────────────────────────────────────────────────────┐
│                    POURQUOI LE RL POUR LE TRADING ?             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LSTM/XGBoost (Supervisé)     │  Reinforcement Learning        │
│  ─────────────────────────    │  ───────────────────────       │
│  Prédit UP/DOWN               │  Apprend une STRATÉGIE         │
│  Décision unique              │  Gère position, timing, risk   │
│  Besoin de labels             │  Apprend par RÉCOMPENSES       │
│  Statique après entraînement  │  Peut s'ADAPTER continuellement│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Analogie :**
- **LSTM** = Un analyste qui dit "le prix va monter"
- **RL** = Un trader complet qui décide quand acheter, combien, et quand vendre

---

### 7.2 Différence entre Supervisé et RL

#### Approche Supervisée (LSTM actuel)

```
┌─────────────────────────────────────────────────────────────┐
│  DONNÉES HISTORIQUES         LABELS (qu'on crée nous-même) │
│  ──────────────────         ─────────────────────────────  │
│  Prix jour 1-14       →     "UP" (car jour 15 a monté)     │
│  Prix jour 2-15       →     "DOWN" (car jour 16 a baissé)  │
│  Prix jour 3-16       →     "UP"                           │
│  ...                        ...                            │
│                                                             │
│  Le modèle apprend: "Ces patterns → Cette direction"       │
└─────────────────────────────────────────────────────────────┘
```

**C'est comme un étudiant qui apprend avec un livre de réponses.**

---

#### Approche Reinforcement Learning

```
┌─────────────────────────────────────────────────────────────┐
│  ENVIRONNEMENT SIMULÉ                                       │
│  ────────────────────                                       │
│                                                             │
│  Jour 1: Prix = $95,000                                     │
│          Agent décide: BUY                                  │
│          ...                                                │
│  Jour 5: Prix = $97,000                                     │
│          Agent décide: SELL                                 │
│          Récompense: +$2,000 ✅                             │
│                                                             │
│  Jour 6: Prix = $97,500                                     │
│          Agent décide: BUY                                  │
│          ...                                                │
│  Jour 8: Prix = $94,000                                     │
│          Agent décide: HOLD (garde la position)             │
│          ...                                                │
│  Jour 10: Prix = $91,000                                    │
│          Agent décide: SELL                                 │
│          Récompense: -$6,500 ❌                             │
│                                                             │
│  L'agent apprend: "Cette situation → Mauvaise décision"     │
│                   "Je ne referai plus ça"                   │
└─────────────────────────────────────────────────────────────┘
```

**C'est comme un enfant qui apprend à marcher - il tombe, ça fait mal, il ajuste.**

---

### 7.3 Le Processus d'Entraînement RL

**OUI, le RL nécessite aussi un entraînement**, mais il fonctionne différemment :

```
        ┌──────────────────────────────────────────┐
        │           BOUCLE D'APPRENTISSAGE         │
        │           (des milliers de fois)         │
        └──────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────┐
    │  1. OBSERVER l'état actuel                        │
    │     (prix, indicateurs, position, capital)        │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────┐
    │  2. CHOISIR une action                            │
    │     (BUY? SELL? HOLD?)                            │
    │     Au début: quasi aléatoire                     │
    │     Après entraînement: stratégie optimale        │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────┐
    │  3. EXÉCUTER l'action dans la simulation          │
    │     (pas avec du vrai argent!)                    │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────┐
    │  4. RECEVOIR une récompense                       │
    │     +profit → "Bien joué, continue comme ça"      │
    │     -perte  → "Mauvais choix, évite ça"           │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
    ┌───────────────────────────────────────────────────┐
    │  5. APPRENDRE de cette expérience                 │
    │     Mettre à jour le "cerveau" (réseau neuronal)  │
    └───────────────────────────────────────────────────┘
                            │
                            ▼
                    Recommencer au jour suivant
                    (ou épisode suivant)
```

---

### 7.4 Comparaison Complète

| Aspect | LSTM (Supervisé) | Reinforcement Learning |
|--------|------------------|------------------------|
| **Apprend de** | Données étiquetées | Essais et erreurs |
| **Objectif** | Prédire UP/DOWN | Maximiser le profit total |
| **Feedback** | "Bonne/Mauvaise prédiction" | "Tu as gagné/perdu $X" |
| **Entraînement** | 1 passe sur les données | Des milliers d'épisodes simulés |
| **Durée** | Minutes | Heures/Jours |
| **Output** | Probabilité UP/DOWN | Action (BUY/SELL/HOLD) + Quantité |
| **Gestion du risque** | Non intégrée | Apprise automatiquement |
| **Adaptation** | Ré-entraînement nécessaire | Peut apprendre en continu |

---

### 7.5 Pourquoi le RL est Plus Puissant

Le RL apprend des choses que le LSTM ne peut pas :

```
LSTM pense:     "Le prix va monter" (70% confiance)

RL pense:       "Le prix va probablement monter, MAIS:
                 - J'ai déjà une grosse position
                 - Le marché est très volatile
                 - Mon dernier trade similaire a mal fini
                 → Je vais HOLD et attendre une meilleure entrée"
```

**Le RL apprend une stratégie complète, pas juste une prédiction.**

---

### 7.6 Architecture Proposée pour TraderPro

```
backend/app/ml/
├── models/                    # Existant (LSTM)
├── prediction_service.py      # Existant (LSTM)
├── model.py                   # Existant (XGBoost)
│
└── rl/                        # NOUVEAU - Reinforcement Learning
    ├── __init__.py
    ├── environment.py         # Environnement de trading (Gym)
    ├── agent.py               # Agent RL (DQN, PPO, etc.)
    ├── reward.py              # Fonctions de récompense
    ├── state.py               # Feature engineering pour l'état
    └── rl_service.py          # Service API (comme prediction_service)
```

---

### 7.7 Les Composants Clés du RL

#### A. Environment (Le Simulateur de Marché)

C'est le composant **le plus important**. Il simule le marché pour que l'agent puisse s'entraîner sans risquer de vrai argent.

```python
class TradingEnvironment:
    """
    Simule le marché Bitcoin pour l'entraînement de l'agent.

    COMPOSANTS:
    -----------

    1. STATE (État) - Ce que l'agent "voit"
       - Prix actuel et historique
       - Indicateurs techniques (RSI, MACD, etc.)
       - Position actuelle (long/short/neutral)
       - Capital disponible
       - Profit/Perte non réalisé

    2. ACTIONS - Ce que l'agent peut faire
       - BUY: Acheter du BTC
       - SELL: Vendre du BTC
       - HOLD: Ne rien faire
       (ou en continu: % du portfolio à investir)

    3. REWARD (Récompense) - Le feedback
       - Profit réalisé sur un trade
       - Pénalité pour trop de trades (frais)
       - Bonus pour bon ratio risk/reward

    4. DONE - Fin de l'épisode
       - Capital épuisé
       - Fin de la période de données
    """

    def step(self, action):
        """Exécute une action et retourne le nouvel état"""
        # 1. Exécuter l'action (BUY/SELL/HOLD)
        # 2. Avancer dans le temps (jour suivant)
        # 3. Calculer la récompense
        # 4. Vérifier si l'épisode est terminé
        return new_state, reward, done, info

    def reset(self):
        """Réinitialise l'environnement pour un nouvel épisode"""
        return initial_state
```

**Visualisation de l'environnement :**

```
┌────────────────────────────────────────────────────────────┐
│                    TRADING ENVIRONMENT                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  État actuel:                                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Prix: $97,000  │ RSI: 45  │ Position: LONG 0.5 BTC  │ │
│  │ Capital: $10,000 │ PnL: +$500 │ Drawdown: 2%        │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Actions possibles:                                        │
│  [BUY +0.1 BTC] [HOLD] [SELL 0.5 BTC]                     │
│                                                            │
│  Historique des prix:                                      │
│  ────────────────/\──────                                  │
│                 /  \    /                                  │
│  ─────────────/────\──/                                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

#### B. Agent (Le Cerveau)

L'agent est le "trader IA" qui apprend à prendre des décisions.

```python
class TradingAgent:
    """
    Le cerveau qui apprend à trader.

    ALGORITHMES RECOMMANDÉS:
    ------------------------

    1. DQN (Deep Q-Network)
       - Simple à implémenter
       - Bon pour actions discrètes (BUY/SELL/HOLD)
       - Utilise un réseau neuronal pour estimer la valeur des actions

    2. PPO (Proximal Policy Optimization)
       - Plus stable que DQN
       - Gère bien les actions continues (% du portfolio)
       - Standard de l'industrie

    3. A2C/A3C (Advantage Actor-Critic)
       - Parallélisable (entraînement plus rapide)
       - Bon équilibre performance/stabilité

    4. SAC (Soft Actor-Critic)
       - State-of-the-art pour actions continues
       - Encourage l'exploration
    """

    def select_action(self, state):
        """Choisit une action basée sur l'état actuel"""
        # Au début: exploration (actions aléatoires)
        # Après entraînement: exploitation (meilleures actions)
        return action

    def learn(self, experience):
        """Apprend d'une expérience (state, action, reward, next_state)"""
        # Met à jour le réseau neuronal
        pass
```

---

#### C. Reward Function (La Fonction de Récompense)

C'est **critique** - elle définit ce que l'agent optimise.

```python
class RewardFunction:
    """
    Définit comment récompenser/pénaliser l'agent.

    EXEMPLES DE RÉCOMPENSES:
    ------------------------

    1. SIMPLE (profit brut)
       reward = profit_realized
       ⚠️ Problème: L'agent peut prendre trop de risques

    2. SHARPE RATIO (ajusté au risque)
       reward = returns / volatility
       ✅ Encourage la consistance

    3. PROFIT - DRAWDOWN
       reward = profit - max_drawdown_penalty
       ✅ Pénalise les grosses pertes

    4. RÉALISTE (avec frais)
       reward = profit * (1 - transaction_fee)
       ✅ Évite le sur-trading
    """

    def calculate(self, action, profit, position, portfolio):
        reward = 0

        # Récompense pour le profit
        reward += profit

        # Pénalité pour le drawdown
        if portfolio.drawdown > 0.1:  # Plus de 10% de perte
            reward -= portfolio.drawdown * 10

        # Pénalité pour trop de trades (frais)
        if action != "HOLD":
            reward -= 0.001  # 0.1% de frais

        return reward
```

---

### 7.8 Flux d'Utilisation

```
┌─────────────────────────────────────────────────────────────┐
│                    PHASE D'ENTRAÎNEMENT                     │
│                    (sur Colab ou local)                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Données historiques (1-2 ans)                              │
│          │                                                  │
│          ▼                                                  │
│  ┌─────────────────┐                                        │
│  │   Environment   │ ← Simule le marché                     │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │     Agent       │ ← Apprend par essai-erreur             │
│  │  (DQN/PPO/SAC)  │   (milliers d'épisodes)                │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Modèle entraîné│ → Sauvegardé (.pt ou .keras)           │
│  └─────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PHASE DE PRODUCTION                      │
│                    (Backend TraderPro)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Prix temps réel (Binance API)                              │
│          │                                                  │
│          ▼                                                  │
│  ┌─────────────────┐                                        │
│  │  State Builder  │ ← Construit l'état actuel              │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Agent (chargé) │ ← Utilise le modèle entraîné           │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │ Action recomm.  │ → BUY/SELL/HOLD + quantité             │
│  └─────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 7.9 Endpoints API Envisagés

```python
# ============ RL ENDPOINTS ============

@router.get("/rl/action")
async def get_rl_action(symbol: str = "BTCUSDT"):
    """
    Obtenir l'action recommandée par l'agent RL.

    Retourne:
    - action: BUY, SELL, ou HOLD
    - quantity: Quantité suggérée (% du portfolio)
    - confidence: Niveau de confiance
    - reasoning: Explication de la décision
    """
    pass

@router.get("/rl/status")
async def get_rl_status():
    """
    Obtenir le statut de l'agent RL.

    Retourne:
    - is_loaded: Si le modèle est chargé
    - algorithm: Algorithme utilisé (DQN, PPO, etc.)
    - training_episodes: Nombre d'épisodes d'entraînement
    - performance_metrics: Métriques de performance
    """
    pass

@router.post("/rl/train")
async def train_rl_agent(
    episodes: int = 1000,
    algorithm: str = "PPO"
):
    """
    Entraîner l'agent RL (ATTENTION: Long!)

    Cette opération peut prendre plusieurs heures.
    Recommandé de le faire sur Colab avec GPU.
    """
    pass

@router.get("/rl/performance")
async def get_rl_performance():
    """
    Obtenir les métriques de performance de l'agent.

    Retourne:
    - total_return: Rendement total
    - sharpe_ratio: Ratio de Sharpe
    - max_drawdown: Perte maximale
    - win_rate: Taux de trades gagnants
    - avg_trade_duration: Durée moyenne des trades
    """
    pass
```

---

### 7.10 Librairies à Utiliser

```python
# requirements.txt - Ajouts pour RL

# Environnement
gymnasium>=0.29.0        # Création d'environnements (ex-OpenAI Gym)

# Algorithmes RL
stable-baselines3>=2.0   # Implémentations RL prêtes à l'emploi
                         # Inclut: DQN, PPO, A2C, SAC, TD3

# Deep Learning Backend
torch>=2.0               # PyTorch (backend pour les réseaux)

# Optionnel
tensorboard>=2.0         # Visualisation de l'entraînement
optuna>=3.0              # Optimisation des hyperparamètres
```

---

### 7.11 Exemple Simplifié d'Entraînement

```python
"""
Exemple simplifié d'entraînement RL pour le trading.
(Version conceptuelle pour comprendre le flux)
"""

from stable_baselines3 import PPO
from gymnasium import Env

class SimpleTradingEnv(Env):
    def __init__(self, df):
        self.df = df
        self.current_step = 0
        self.position = 0  # 0=neutral, 1=long, -1=short
        self.capital = 10000

    def reset(self):
        self.current_step = 0
        self.position = 0
        self.capital = 10000
        return self._get_state()

    def step(self, action):
        # Exécuter l'action
        if action == 0:  # BUY
            self.position = 1
        elif action == 1:  # SELL
            self.position = -1
        else:  # HOLD
            pass

        # Avancer dans le temps
        self.current_step += 1

        # Calculer le profit/perte
        price_change = self.df['close'].iloc[self.current_step] - \
                       self.df['close'].iloc[self.current_step - 1]

        reward = self.position * price_change
        self.capital += reward

        # Vérifier si terminé
        done = self.current_step >= len(self.df) - 1 or self.capital <= 0

        return self._get_state(), reward, done, {}

    def _get_state(self):
        # Retourne l'état actuel (prix, indicateurs, position)
        return [
            self.df['close'].iloc[self.current_step],
            self.df['rsi'].iloc[self.current_step],
            self.position,
            self.capital
        ]


# ENTRAÎNEMENT
env = SimpleTradingEnv(historical_data)
model = PPO("MlpPolicy", env, verbose=1)

# Entraîner pendant 100,000 steps
model.learn(total_timesteps=100000)

# Sauvegarder
model.save("trading_agent_ppo")


# UTILISATION
model = PPO.load("trading_agent_ppo")
state = env.reset()
action, _ = model.predict(state)
print(f"Action recommandée: {['BUY', 'SELL', 'HOLD'][action]}")
```

---

### 7.12 Résumé RL vs LSTM

```
┌─────────────────────────────────────────────────────────────────┐
│                        RÉSUMÉ COMPARATIF                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LSTM (Actuel)                 Reinforcement Learning (Futur)  │
│  ─────────────                 ─────────────────────────────   │
│                                                                 │
│  ✅ Simple à implémenter       ⚠️ Plus complexe                 │
│  ✅ Entraînement rapide        ⚠️ Entraînement long (heures)    │
│  ✅ Fonctionne bien            ✅ Potentiellement meilleur      │
│                                                                 │
│  ❌ Prédit seulement UP/DOWN   ✅ Stratégie complète            │
│  ❌ Pas de gestion du risque   ✅ Risk management intégré       │
│  ❌ Pas de position sizing     ✅ Apprend combien investir      │
│                                                                 │
│  RECOMMANDATION:                                                │
│  Garder LSTM + Ajouter RL comme "mode avancé"                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Glossaire des Termes

### Termes Généraux

| Terme | Définition |
|-------|------------|
| **API** | Interface permettant à deux programmes de communiquer |
| **Endpoint** | URL spécifique de l'API (ex: /api/analysis) |
| **JSON** | Format de données texte structuré |
| **Async** | Exécution non-bloquante (n'attend pas) |
| **CORS** | Sécurité permettant au frontend d'appeler le backend |

### Termes Trading

| Terme | Définition |
|-------|------------|
| **OHLCV** | Open, High, Low, Close, Volume (une bougie) |
| **Timeframe** | Période d'une bougie (1m, 1h, 1d...) |
| **Support** | Niveau de prix où le prix rebondit (plancher) |
| **Résistance** | Niveau de prix où le prix est rejeté (plafond) |
| **Stop Loss** | Ordre de vente automatique pour limiter les pertes |
| **Take Profit** | Ordre de vente automatique pour prendre les gains |
| **Risk/Reward** | Ratio gain potentiel / perte potentielle |

### Termes Indicateurs

| Terme | Définition |
|-------|------------|
| **RSI** | Indicateur de momentum (suracheté/survendu) |
| **MACD** | Indicateur de tendance (croisements) |
| **Bollinger Bands** | Bandes de volatilité autour d'une moyenne |
| **SMA** | Simple Moving Average (moyenne simple) |
| **EMA** | Exponential Moving Average (plus réactive) |
| **ATR** | Average True Range (volatilité moyenne) |

### Termes Machine Learning

| Terme | Définition |
|-------|------------|
| **Feature** | Variable d'entrée du modèle |
| **Label/Target** | Variable de sortie à prédire |
| **Training** | Phase d'apprentissage du modèle |
| **Inference** | Phase de prédiction |
| **Overfitting** | Le modèle apprend par coeur (mauvais) |
| **Data Leakage** | Le modèle "voit" le futur (erreur grave) |

### Termes Reinforcement Learning

| Terme | Définition |
|-------|------------|
| **Agent** | L'entité qui apprend et prend des décisions |
| **Environment** | Le monde simulé dans lequel l'agent évolue |
| **State** | L'observation actuelle de l'environnement |
| **Action** | Ce que l'agent peut faire (BUY/SELL/HOLD) |
| **Reward** | Feedback numérique (+profit ou -perte) |
| **Episode** | Une séquence complète (du début à la fin) |
| **Policy** | La stratégie de l'agent (état → action) |
| **Q-Value** | Valeur estimée d'une action dans un état |
| **Exploration** | Essayer des actions aléatoires pour découvrir |
| **Exploitation** | Utiliser la meilleure action connue |
| **DQN** | Deep Q-Network (algorithme RL avec neural network) |
| **PPO** | Proximal Policy Optimization (algorithme stable) |
| **Sharpe Ratio** | Rendement ajusté au risque (plus = mieux) |
| **Drawdown** | Perte maximale depuis le pic (à minimiser) |

---

## Conclusion

Tu as maintenant une compréhension complète du backend TraderPro !

**Pour résumer :**
1. **FastAPI** gère les requêtes HTTP
2. **Services** font le travail (Binance, Indicateurs, Analyse)
3. **ML Supervisé** prédit les mouvements avec XGBoost et LSTM
4. **Modèles Pydantic** structurent les données
5. **Reinforcement Learning** (à venir) apprendra des stratégies complètes

**Architecture IA actuelle :**
```
┌─────────────────────────────────────────────────────────────┐
│                    TRADERPRO - STACK IA                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   XGBoost   │  │    LSTM     │  │  Reinforcement RL   │ │
│  │  (ML rapide)│  │ (Deep Learn)│  │    (À implémenter)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│         ▼                ▼                     ▼            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              SIGNAL DE TRADING FINAL                    ││
│  │           BUY / SELL / HOLD + Confiance                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Prochaines étapes :**
1. Lance le backend : `./venv/bin/uvicorn main:app --reload`
2. Explore la documentation : `http://localhost:8000/docs`
3. Teste la prédiction LSTM : `GET /api/prediction/tomorrow`
4. (Futur) Implémenter le Reinforcement Learning

**Évolution prévue :**
- **Phase 1** ✅ : XGBoost + Analyse technique
- **Phase 2** ✅ : LSTM pour prédiction UP/DOWN
- **Phase 3** 🔄 : Reinforcement Learning pour stratégie complète

---

*Document créé pour TraderPro - Ton assistant IA de trading Bitcoin*
