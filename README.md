# TraderPro - AI Trading Assistant

Assistant IA de trading Bitcoin utilisant le Machine Learning et le Reinforcement Learning.

## Architecture

```
TraderPro/
├── backend/                 # API FastAPI (Python)
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── services/       # Binance, Analyse technique
│   │   └── ml/             # Modèles ML/RL
│   └── main.py
├── frontend/               # Interface Next.js (React)
│   └── src/
│       ├── app/           # Pages
│       ├── components/    # Composants UI
│       └── hooks/         # Custom hooks
└── colab_*.ipynb          # Notebooks d'entraînement
```

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Backend** | FastAPI, Python 3.13 |
| **Frontend** | Next.js 16, React 19, TailwindCSS |
| **ML Supervisé** | XGBoost, LSTM (TensorFlow/Keras) |
| **Reinforcement Learning** | Stable-Baselines3, Gymnasium |
| **Data** | Binance API, Pandas, NumPy |

---

## Machine Learning - Les 3 Approches

### 1. XGBoost (Classification)
- **Type** : Supervisé
- **Output** : BUY / SELL / HOLD
- **Entraînement** : Rapide (minutes)
- **Fichier** : `backend/app/ml/model.py`

### 2. LSTM (Deep Learning)
- **Type** : Supervisé
- **Output** : UP / DOWN (direction du prix demain)
- **Entraînement** : Moyen (10-30 min sur Colab)
- **Fichier** : `backend/app/ml/prediction_service.py`
- **Notebook** : `colab_option_B_classification.ipynb`

### 3. Reinforcement Learning (PPO)
- **Type** : Apprentissage par renforcement
- **Output** : Stratégie complète (action + timing + gestion du risque)
- **Entraînement** : Long (heures sur Colab)
- **Notebook** : `colab_rl_training.ipynb`

---

## Reinforcement Learning - Détails

### Algorithmes disponibles (Stable-Baselines3)

```
┌─────────────────────────────────────────────────────────────────┐
│                    FAMILLES D'ALGORITHMES RL                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  VALUE-BASED (apprend Q-values)                                 │
│  ├── Q-Learning (tabulaire, basique)                            │
│  ├── SARSA (tabulaire, on-policy)                               │
│  └── DQN (Deep Q-Learning) ✅                                   │
│                                                                 │
│  POLICY-BASED (apprend directement la policy)                   │
│  └── PPO (Proximal Policy Optimization) ✅ ← Recommandé        │
│                                                                 │
│  ACTOR-CRITIC (combine les deux)                                │
│  ├── A2C (Advantage Actor-Critic) ✅                            │
│  ├── SAC (Soft Actor-Critic) ✅                                 │
│  └── TD3 (Twin Delayed DDPG) ✅                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Comparaison des algorithmes

| Algorithme | Type | Actions | Stabilité | Usage |
|------------|------|---------|-----------|-------|
| **DQN** | Deep Q-Learning | Discrètes | Moyenne | Simple, bon pour débuter |
| **PPO** | Policy Gradient | Toutes | **Haute** | **Standard industrie** |
| **A2C** | Actor-Critic | Toutes | Moyenne | Parallélisable |
| **SAC** | Actor-Critic | Continues | Haute | State-of-the-art continu |

### Pourquoi PPO pour le trading ?

| Critère | DQN | PPO |
|---------|-----|-----|
| Stabilité d'entraînement | Moyenne | **Excellente** |
| Actions discrètes | Oui | Oui |
| Actions continues | Non | **Oui** |
| Sample efficiency | Meilleur | Bon |
| Facilité de tuning | Difficile | **Facile** |
| Production-ready | Oui | **Oui** |

### Configuration RL TraderPro

```python
# Actions
ACTIONS = ["HOLD", "BUY", "SELL"]  # Discrètes

# État (observation)
STATE = [
    "prix (14 derniers jours)",
    "indicateurs (RSI, MACD, BB...)",
    "position actuelle",
    "PnL non réalisé"
]

# Récompense (Sharpe-based)
REWARD = sharpe_ratio - drawdown_penalty - transaction_fees
```

---

## Installation

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

---

## Lancement

### Backend (API)

```bash
cd backend
./venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

API disponible sur : http://localhost:8002/docs

### Frontend

```bash
cd frontend
npm run dev
```

Interface disponible sur : http://localhost:3000

### Mode démo Binance Futures Testnet

Le menu **Démo & Historique** enregistre chaque décision de l'IA dans SQLite et,
pour les signaux `BUY` ou `SELL`, tente un ordre **uniquement sur Binance USD-M
Futures Testnet**. Il utilise la marge isolée et un levier de 1× ; aucun endpoint réel n'est utilisé.

Créez des clés Spot Testnet, sans droits de retrait, puis ajoutez-les dans
`backend/.env` (ne les placez jamais dans `frontend/.env.local`) :

```env
BINANCE_TESTNET=true
BINANCE_FUTURES_TESTNET_API_KEY=votre_cle_futures_testnet
BINANCE_FUTURES_TESTNET_API_SECRET=votre_secret_futures_testnet
FUTURES_LEVERAGE=1
```

Les décisions, positions ouvertes, positions clôturées et P&L réalisé sont
conservés dans la base SQLite `backend/data/traderpro.db`.

---

## Endpoints API

### Market Data
- `GET /api/market/price` - Prix actuel BTC
- `GET /api/market/klines` - Données OHLCV

### Analyse Technique
- `GET /api/analysis` - Analyse complète
- `GET /api/analysis/signal` - Signal rapide

### ML Predictions
- `GET /api/predict` - Prédiction XGBoost
- `POST /api/model/train` - Entraîner XGBoost

### LSTM Predictions
- `GET /api/prediction/tomorrow` - Prédiction UP/DOWN demain
- `GET /api/prediction/status` - Statut du modèle LSTM

### Reinforcement Learning (à venir)
- `GET /api/rl/action` - Action recommandée par l'agent
- `GET /api/rl/status` - Statut de l'agent RL

### Démo et historique
- `POST /api/demo/execute` - Analyse une paire, enregistre la décision et tente l'ordre Testnet
- `GET /api/demo/history` - Décisions, positions, historique et gains/pertes

---

## Notebooks Colab

| Notebook | Description |
|----------|-------------|
| `colab_option_A_simple.ipynb` | LSTM basique (régression prix) |
| `colab_option_B_classification.ipynb` | LSTM classification UP/DOWN |
| `colab_option_C_external_data.ipynb` | LSTM avec données externes |
| `colab_rl_training.ipynb` | **Reinforcement Learning (PPO)** |

---

## Roadmap

- [x] **Phase 1** : XGBoost + Analyse technique
- [x] **Phase 2** : LSTM pour prédiction UP/DOWN
- [ ] **Phase 3** : Reinforcement Learning (PPO)
- [ ] **Phase 4** : Interface de backtesting
- [x] **Phase 5** : Paper trading avec Binance Spot Testnet et historique local

---

## Documentation

- [Guide Backend](backend/GUIDE_BACKEND.md) - Documentation complète du backend avec explications ML/RL

---

## Avertissement

Ce projet est à but éducatif. Le trading de cryptomonnaies comporte des risques. Les prédictions et signaux générés ne constituent pas des conseils financiers.

---

*TraderPro - AI Trading Assistant*







Oui, et le résultat actuel est réellement insuffisant pour
  trader : il est même légèrement sous le baseline naïf «
  toujours HOLD » sur notre test. Ce n’est pas un problème
  de GridSearch ; c’est surtout notre objectif
  d’apprentissage qui est trop simpliste.

  Pourquoi :

  - On demande au modèle de deviner BUY / HOLD / SELL à 4
    heures avec un seuil fixe de 0,4 %. À cet horizon, BTC
    contient beaucoup de bruit.

  - Notre modèle n’a qu’un an de données, soit 8 760
    bougies. Il n’a pas vu assez de régimes BTC différents.

  - Il n’utilise que OHLCV + indicateurs techniques. Il lui
    manque les données réellement informatives pour les
    Futures : funding rate, open interest, basis,
    liquidations, carnet d’ordres, volatilité réalisée et
    éventuellement sentiment.

  - L’accuracy est une mauvaise cible pour un bot.
    L’important est : « quand le modèle est très confiant,
    le mouvement dépasse-t-il frais + slippage + risque ? »

  - Les statistiques le montrent : BUY a seulement 27 % de
    précision et 29 % de rappel. Le modèle n’a pas
    d’avantage exploitable dans son état actuel.

     éviter d’entraîner sur le futur ; son paramètre gap
     exclut les observations trop proches. Documentation
     scikit-learn


  4. Déclencher un trade seulement lorsque la prédiction est
     supérieure à un seuil qui couvre les coûts. Une étude
     récente sur ~70 000 bougies horaires BTC-USDT conclut
     justement que le filtre tenant compte des frais est
     plus décisif que le choix XGBoost/LSTM/iTransformer.
     Étude walk-forward BTC
     (https://arxiv.org/abs/2606.00060)

  5. Ajouter une couche de méta-labellisation : le modèle
     principal propose LONG/SHORT, un second décide si le
     signal mérite d’être exécuté.

  Je te recommande de ne pas continuer à « tuner » ce
  XGBoost V1. La bonne V2 serait :

  - 5 à 8 ans de bougies 1 h ;
  - labels dynamiques selon l’ATR/volatilité ;
  - XGBoost en régression du rendement attendu ;
  - calibration des probabilités ;
  - filtre d’exécution coût-aware ;
  - walk-forward mensuel ;
  - métriques de trading : P&L net, Sharpe, drawdown, profit
    factor — pas seulement accuracy ;

  - puis seulement envoyer les signaux validés au Futures
    Testnet.

  C’est cette voie qui peut améliorer les résultats de
  manière honnête, sans promettre un bot miraculeux.

────────────────────────────────────────────────────────────


› Je te recommande de ne pas continuer à « tuner » ce
    XGBoost V1. La bonne V2 serait :

    - XGBoost en régression du rendement attendu ;
    - calibration des probabilités ;
    - filtre d’exécution coût-aware ;
    - walk-forward mensuel ;
    - métriques de trading : P&L net, Sharpe, drawdown,
  profit
      factor — pas seulement accuracy ;

  ca c'est ce que tu me propose en fonction de tout ce que
  tu as trouver sur internet? ou non? par ce que tu as dit
  que sur internet on me propse une autre route


• Oui. C’est ma proposition, construite à partir des
  méthodes sérieuses retrouvées en ligne et adaptée à
  TraderPro.

  Internet ne propose pas une recette magique unique. Le
  consensus utile est plutôt :

  - validation walk-forward et séparation temporelle
    stricte ;

  - labels dynamiques / filtrés selon la volatilité ;
  - ne trader que les prédictions assez fortes pour couvrir
    frais et slippage ;

  - juger le modèle sur le P&L net et le risque, pas sur
    l’accuracy seule.

  L’étude BTC horaire récente utilise justement
  walk-forward, beaucoup plus de données, XGBoost et un
  filtre coût-aware ; elle conclut que la manière de
  transformer une prédiction en trade compte davantage que
  le modèle seul. Étude BTC
  (https://arxiv.org/abs/2606.00060)

  Les labels dynamiques et la méta-labellisation viennent de
  la méthodologie de ML financier de López de Prado.
  Référence (https://philpapers.org/rec/LPEAIF)

  Donc non, je ne te dis pas simplement « change XGBoost par
  un autre modèle ». Je propose de transformer notre
  entraînement en pipeline de trading réaliste. XGBoost peut
  rester très utile, mais il doit prédire un rendement/
  probabilité calibrée et être entouré de règles d’exécution
  et de risque.


  La V2 est construite, entraînée et validée — et elle
  confirme honnêtement qu’elle ne doit pas encore trader.

  Elle inclut :

  - 5 ans de BTCUSDT 1 h : 43 793 bougies ;
  - rendement futur en régression ;
  - labels dynamiques ATR avec barrières haut/bas ;
  - calibration de confiance ;
  - filtre coûts + edge sélectionné sur validation ;
  - walk-forward mensuel : 3 ans d’entraînement, 30 jours de
    validation, 30 jours de test ;

  - métriques P&L net, drawdown, profit factor et win rate.

  Résultat walk-forward réel sur 22 fenêtres :

  - 128 trades
  - rendement net agrégé : -9,49 %
  - drawdown maximal : 21,98 %

  Donc le modèle V2 est volontairement déclaré
  eligible_for_testnet: false. Je ne l’ai pas connecté au
  bot Futures, car cela reviendrait à automatiser une
  stratégie qui échoue hors échantillon.

  Tu peux consulter :

  - backend/models/trading_model_v2.joblib
  - backend/models/trading_model_v2.manifest.json
  - backend/data/BTCUSDT_1h_5y.csv
  - endpoint GET /api/model/v2/status

  La prochaine amélioration pertinente est d’ajouter des
  variables Futures réelles — funding rate, open interest,
  basis, liquidations et carnet d’ordres. Les seules bougies
  OHLCV ne donnent pas assez d’information pour un edge
  robuste sur BTC.

─ Worked for 25m 06s ───────────────────────────────────────


› la comment on fait alors?


• Je vérifie les endpoints Futures officiels disponibles
  aujourd’hui afin de te proposer un pipeline réalisable
  avec Binance, pas une liste théorique.

• Searching the web

• Searched the web for site:developers.binance.com Binance
  Futures API open interest history funding rate historical
  klines liquidation order book endpoint ...

────────────────────────────────────────────────────────────

• On sépare les données d’entraînement et l’exécution :

  - Entraînement : données publiques du marché Futures réel
    Binance — aucune clé API nécessaire, aucun ordre envoyé.

  - Exécution : uniquement ton compte Futures Testnet avec
    ta clé actuelle.

  Binance propose des API REST et WebSocket pour les Futures
  USDⓈ-M, donc on peut collecter ces données
  automatiquement. Documentation officielle Futures
  (https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/Introduction)

  Concrètement, je vais créer dans TraderPro un collecteur
  qui enregistre dans une base de données :

  ━━━━━━━━━━━━━━━━━━━━━━━━  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Prix / bougies Futures    tendance, volatilité, ATR
  ────────────────────────  ────────────────────────────────
   Funding rate              coût et biais LONG/SHORT
                             le marché
  ────────────────────────  ────────────────────────────────
   Ratio long/short          positionnement des traders
  ────────────────────────  ────────────────────────────────
   Taker buy/sell volume     pression acheteuse ou vendeuse
  ────────────────────────  ────────────────────────────────
   Liquidations en direct    mouvements forcés et régimes
  ────────────────────────  ────────────────────────────────
   Carnet d’ordres           déséquilibre bid/ask à court
                             terme

  donc le marché réel public, mais le bot reste en Testnet
  pour exécuter ses trades de démo.

  funding_rates
  open_interest
  long_short_ratios
  orderbook_snapshots
  liquidations
  model_predictions
  demo_decisions
  demo_trades

  Deux limites honnêtes :

  - les bougies et funding historiques peuvent être
    récupérés ;

  - un historique complet de carnet d’ordres/liquidations
    sur cinq ans n’est généralement pas fourni gratuitement
    par l’API : il faut commencer à le collecter maintenant,
    ou acheter un dataset spécialisé plus tard.

  La prochaine étape concrète est donc : j’implémente le
  collecteur Futures public + les tables de base de données,
  puis nous laissons TraderPro accumuler ses propres données
  pendant que le bot reste en Testnet.

────────────────────────────────────────────────────────────


› Screenshot 2026-07-21 at 4.40.08 PM, dans le bureau ,
  voici les resulats du rienforcement learning


• Je ne vois pas encore l’image dans la conversation.
  Attache le screenshot ici, ou copie les métriques
  affichées — surtout total reward, mean reward, episode
  reward, loss, explained variance, et le résultat du
  backtest.

  Je pourrai alors te dire si le RL apprend réellement, s’il
  surapprend, ou s’il est bloqué.


  4.40.08 PM


• Je cherche le fichier exact sur le Bureau, puis je l’ouvre
• Explored
  └ List Desktop
    Search Screenshot 2026-07-21 at 4\.40\.08

• Viewed Image
  └ ~/Desktop/Screenshot 2026-07-21 at 4.40.08 PM.png

────────────────────────────────────────────────────────────

• Le RL n’est pas bon non plus : il ne faut pas l’utiliser
  dans le bot.

  Résultats hors échantillon visibles :

  - rendement : -6,33 %
  - Sharpe : -0,358
  - drawdown maximal : 31,49 %
  - nombre de trades : 51

  La courbe monte de 10 000 à environ 12 200, puis subit une
  forte chute et termine vers 9 350. Cela montre que le
  modèle a probablement appris un régime favorable au début
  du test, puis échoue quand le marché change.

  Deux points importants :

  1. Ce notebook est encore une simulation simple et ne
     reflète pas entièrement notre Futures Testnet : frais
     Futures réalistes, funding, short/long, liquidation et
     exécution.

  2. Le résultat doit être comparé au buy-and-hold sur
     exactement la même période. Mais même sans cette
     comparaison, un rendement négatif avec 31 % de drawdown
     est un refus clair.
  Les fichiers best_model.zip, ppo_btc_final.zip et
  vecnormalize.pkl sont bien produits, mais ils ne doivent
  pas être intégrés à TraderPro.

  réelles, avec évaluation walk-forward, et non seulement
  sur ces bougies OHLCV.

────────────────────────────────────────────────────────────


› mais c'est pas grace , il s'ameliorera au fure et a
  mesure, n'est ce pas?


• Pas automatiquement.

  Pendant son entraînement sur l’historique, le RL peut
  améliorer sa récompense sur les données qu’il voit. Mais
  cela ne garantit pas qu’il s’améliore sur le marché
  futur : il peut aussi surapprendre à une période passée et
  devenir pire quand le régime BTC change.

  Et actuellement, le bot Testnet :
    chaque trade.

  Pour qu’il apprenne progressivement de façon saine, il
  faut un cycle contrôlé :
     conditions de marché dans la base.

  2. Chaque semaine ou mois, créer un nouveau jeu de
     données.

  3. Réentraîner hors ligne sur l’historique enrichi.
  4. Comparer l’ancien et le nouveau modèle en walk-forward.
  5. Ne remplacer le modèle actif que si le nouveau est
     meilleur après frais et avec un drawdown acceptable.

  6. Garder le précédent modèle sinon.

  Il ne faut pas laisser le modèle apprendre directement en
  production trade par trade : quelques mauvais épisodes ou
  un changement brutal de marché peuvent le dégrader très
  vite. Le Testnet est justement l’endroit où l’on accumule
  les données et vérifie cette amélioration avant toute
  autre étape.


› Et actuellement, le bot Testnet , c'est quoi le bot
  tesnet?


• Le bot Testnet, c’est ton bot TraderPro qui passe des
  ordres sur un compte Binance de démonstration.

  Il utilise :

  réel.

  Ce n’est pas encore un bot autonome qui surveille le
  marché 24h/24 et décide seul : pour l’instant, TraderPro


› okay c'est un bot simple sans AI ,n'est ce pas, il ce
  faucalise que sur l'analyse technique? et tu me dis qu'il
  ne marche que si j'execute le tout frontend et backend ,
  ou j'ai pas compris?


• Oui, exactement : actuellement c’est un bot de démo
  simple.

  - Il se base surtout sur l’analyse technique : RSI, MACD,
    Bollinger, tendance, etc.

  - Il peut aussi afficher les prédictions XGBoost/LSTM,
    mais les modèles actuels ne sont pas assez validés pour
    piloter les trades.

  - Le RL V2 n’est pas connecté au bot car ses résultats
    sont négatifs.

  - Il n’est pas autonome : il passe un ordre seulement
    quand tu déclenches l’action depuis le frontend.

  Et oui, pour l’utiliser aujourd’hui :

  1. Le backend doit être démarré : il récupère les données,
     calcule le signal et parle à Binance Futures Testnet.

  2. Le frontend doit être démarré : c’est l’interface qui
     te permet de voir l’analyse et d’envoyer l’action.

  Le navigateur ne garde pas le bot actif. Si tu fermes
  frontend/backend, il ne surveille rien et ne trade rien.
  Pour un vrai bot autonome, il faudra ajouter un scheduler
  côté backend : par exemple analyser BTC toutes les heures,
  journaliser la décision, puis éventuellement exécuter un
  trade Testnet selon des règles de risque.


› Il n’est pas autonome : il passe un ordre seulement quand
  tu déclenches l’action depuis le frontend, j'ai pas
  compris cette partie,il faut que je le lance depuis
  depuis le frontend, ou il comment automatiquement des que
  j'execute le frontend et le backend? et puis alors on
  peut d'abord tester juste ce bot , et voir comment il ce
  comporte , s'il arrive a faire des gains et tout, mais
  pour la strategie qu'il utilise c'est une strategie deja
  hardcoder , ou non il s'adapte et adapte sa strategie en
  fonction des indicateurs?


• Tu dois cliquer sur le bouton d’exécution dans le
  frontend.

  Dès que frontend et backend sont lancés, le bot affiche
  les analyses et signaux, mais il ne place pas d’ordre
  automatiquement. Il attend ton action : tu ouvres la page
  Historique, tu regardes le signal, puis tu lances
  l’exécution. À ce moment-là, le backend envoie l’ordre au
  Futures Testnet.

  Donc oui, on peut tester ce bot maintenant :

  - lancer frontend + backend ;
  - laisser le marché évoluer ;
  - consulter le signal ;
  - exécuter quelques trades Testnet ;
  - observer l’historique, P&L et drawdown ;
  - comparer les décisions sur plusieurs jours/semaines.

  Sa stratégie est actuellement hardcodée : elle combine des
  règles d’analyse technique. Elle réagit aux indicateurs
  actuels — RSI, MACD, tendance, volatilité, bandes de
  Bollinger — mais elle ne modifie pas elle-même ses règles
  et paramètres après ses gains ou pertes.

  En bref :

  Indicateurs actuels → règles techniques fixes → BUY /
  SELL / HOLD → tu confirmes → ordre Testnet

  Elle s’adapte au marché au sens où les indicateurs
  changent, mais elle n’apprend pas encore de ses propres
  résultats.

  okay mais on peut pas faire un bot plus intelligent qui
  prend des position, seul et pour la strategie qui
  s'adapte au marche ?

  Données Futures → analyse du régime de marché → stratégie
  adaptée → contrôle risque → ordre Testnet → journal +
  apprentissage contrôlé


  - marché haussier : privilégier LONG et suivre la
    tendance ;

  - marché baissier : privilégier SHORT ;
  - marché latéral : réduire les trades ou appliquer une
    stratégie de retour à la moyenne ;

  - volatilité excessive : ne rien faire ou réduire
    fortement la taille des positions.

  La partie « intelligente » ne doit pas être un RL qui
  change ses règles après chaque trade. Une approche plus
  sûre est :

  1. Détecteur de régime : tendance / range / haute
     volatilité.

  2. Plusieurs stratégies simples, chacune adaptée à un
     régime.

  3. Score de confiance basé sur les indicateurs, puis
     filtre frais/risque.

  4. Gestion stricte : levier 1×, taille limitée, stop-loss,
     take-profit, perte journalière maximale, nombre maximal
     de positions.

  5. Scheduler backend : analyse automatique à chaque
     clôture de bougie 1 h.

  6. Journal complet et réentraînement hors ligne
     périodique.

  On peut commencer en Testnet avec un mode « autonome
  surveillé » : le bot décide seul, mais seulement avec de
  petites positions fictives et des règles de sécurité
  strictes. Après plusieurs semaines de résultats cohérents,
  on réévalue.

  C’est la bonne prochaine évolution de TraderPro.


› okay , mais ce ot peut il apprendre et s'ameliorer en
  fonction de ses gains et des echecs? ou non. Car ce que
  je veux , je veux un bot qui puisse prendre des decision
  trader, sans etre trop dans l'optique de ne pas vouloir
  perdre, car en trading les perte sont invetitable et le
  plus important c'est que les gains couvrent les pertes et
  qu'il s'ameliore continuellement


• Oui, c’est possible — et c’est bien l’objectif pertinent :
  pas éviter toute perte, mais viser une espérance de gain
  positive où les gains dépassent les pertes après frais.

  Un bot intelligent peut apprendre de ses gains et échecs,
  mais il doit le faire avec un vrai cycle d’apprentissage,
  pas en modifiant sa stratégie après chaque trade isolé.

  Trade autonome → résultat/P&L enregistré → contexte de
  marché enregistré
  → analyse de centaines de trades → nouveau modèle candidat
  → backtest + Testnet → remplacement seulement s’il est
  meilleur

  Ce qu’il apprendrait pour chaque décision :

  - régime du marché : tendance, range, volatilité ;
  - indicateurs et données Futures au moment de l’entrée ;
  - direction choisie, taille, stop-loss et take-profit ;
  - P&L net après frais/funding ;
  - drawdown et durée de position ;
  - si le trade était bon ou mauvais dans ce contexte.

  La récompense ne serait donc pas « +1 si gain, −1 si perte
  », trop simpliste. Elle pourrait être :

  récompense = P&L net
              − pénalité si drawdown trop grand
              − pénalité si trop de trades/frais
              + bonus si profit factor et régularité
              s’améliorent

  Ainsi, le bot accepte des pertes normales. Une stratégie
  avec 45 % de trades gagnants peut être excellente si ses
  gains moyens sont bien plus grands que ses pertes
  moyennes.

  La bonne architecture serait :

  - un bot autonome Testnet qui prend de petites positions ;
  - une base de données de toutes ses expériences ;
  - un modèle de décision adaptatif ;
  - un RL entraîné périodiquement sur ces expériences et
    l’historique ;

  - un modèle « champion » actif et un modèle « challenger »
    testé en parallèle ;

  - remplacement du champion seulement si le challenger
    améliore le P&L net, profit factor, Sharpe et drawdown
    sur une période fraîche.

  Donc : oui, il peut s’améliorer continuellement, accepter
  des pertes contrôlées, et chercher une rentabilité
  globale. Mais l’amélioration doit être mesurée et validée,
  sinon il risque simplement d’apprendre les mauvaises
  leçons d’une courte série de gains ou de pertes.

  La première couche de l’architecture autonome est en place
  et vérifiée.

  Elle inclut :

  - scheduler backend qui vérifie le marché toutes les 5
    minutes, mais ne traite qu’une fois chaque bougie 1 h ;

  - stratégie adaptative par régime :
      - tendance → suivi de tendance ;
      - range → retour à la moyenne avec RSI ;
      - volatilité élevée → aucune nouvelle position ;

  - une seule position BTC à la fois ;
  - plafond de 4 trades/jour ;
  - perte journalière maximale de 20 USDT Testnet ;
  - journal des cycles et expériences dans SQLite ;
  - endpoint GET /api/autonomous/status.

  Le bot est actuellement désactivé et n’envoie aucun
  ordre :

  AUTONOMOUS_TRADING_ENABLED=false

  Quand tu voudras lancer le test autonome sur Binance
  Futures Testnet, mets dans backend/.env :

  AUTONOMOUS_TRADING_ENABLED=true

  puis redémarre le backend. Le frontend ne sera plus
  nécessaire pour déclencher chaque trade ; il servira
  surtout à consulter l’historique.

  Important : cette première version adapte ses règles au
  régime détecté, mais elle n’apprend pas encore
  automatiquement de chaque trade. Les expériences sont
  maintenant enregistrées pour construire ensuite le cycle
  champion/challenger de réentraînement contrôlé.

  Le cycle d’apprentissage contrôlé est maintenant prêt.

  À chaque cycle autonome, TraderPro enregistre :

  - régime de marché ;
  - indicateurs au moment de la décision ;
  - action, confiance et raison ;
  - décision/position Testnet associée ;
  - P&L et résultat win / loss / flat dès que le trade est
    clôturé.

  J’ai aussi ajouté le registre champion/challenger :

  - champion actuel : rules-v1, la stratégie adaptative par
    régimes ;

  - challenger : futur modèle entraîné sur les expériences
    collectées ;

  - aucune promotion automatique avant au moins 100 trades
    clôturés ;

  - le challenger devra avoir P&L net positif, profit factor
    ≥ 1,15, drawdown ≤ 15 % et passer plusieurs fenêtres
    walk-forward fraîches.

  Tu peux consulter :

  - GET /api/autonomous/status
  - GET /api/learning/status

  Pour l’instant, le bot autonome reste désactivé. Une fois
  que tu voudras démarrer sa collecte Testnet :

  AUTONOMOUS_TRADING_ENABLED=true

  puis redémarre le backend. Il pourra alors prendre les
  décisions lui-même et remplir progressivement la base
  d’expériences.



  La direction décidée est celle-ci : construire un bot
  autonome de Testnet, prudent mais réellement décisionnel,
  qui s’améliore par cycles contrôlés — pas un modèle qui
  réécrit sa stratégie après chaque trade.

  La logique actuelle :

  Données BTC Futures
  → détection du régime de marché
  → stratégie adaptée au régime
  → règles de risque
  → trade Binance Futures Testnet
  → journal complet des décisions et P&L
  → entraînement périodique d’un challenger
  → remplacement seulement s’il bat le modèle actif

  Concrètement, le bot actif prévu est rules-v1 :

  - Marché en tendance : suivi de tendance, plutôt LONG en
    hausse / SHORT en baisse.

  - Marché en range : retour à la moyenne, notamment via
    RSI.

  - Forte volatilité : pas de nouvelle position.
  - Limites : 1 position BTC à la fois, maximum 4 trades/
    jour, perte journalière max de 20 USDT Testnet, levier
    1×.

  Il est autonome côté backend : il vérifie toutes les 5
  minutes mais ne décide qu’à la clôture d’une bougie 1 h.
  Il est actuellement désactivé avec :

  AUTONOMOUS_TRADING_ENABLED=false

  Le jour où tu veux le tester réellement en démo, tu le
  ordre ; il sert surtout à suivre l’historique.

  Ce qu’on a décidé de ne pas utiliser pour trader
  automatiquement, pour l’instant :
    trop faible.

  - XGBoost V2 : pipeline plus sérieux, mais résultat walk-
    forward négatif (-9,49 %, drawdown 21,98 %) ; donc non
    éligible au Testnet comme moteur de décision.
    échantillon est aussi négatif (-6,33 %, drawdown 31,49
    %).

  - Apprentissage en direct après chaque trade : abandonné,
    car trop instable et propice au surapprentissage.

  Ce qu’on conserve :

  - XGBoost, LSTM et TTM comme outils d’analyse/affichage et
    futurs challengers.

  - Le RL comme piste future, mais seulement après davantage
    de données Futures réelles et une validation sérieuse.

  - Le Testnet comme environnement d’observation et de
    collecte, jamais le réel à ce stade.

  Le mécanisme d’amélioration décidé est « champion/
  challenger » :

  1. rules-v1 est le champion et trade en Testnet.
  2. Chaque cycle enregistre contexte, régime, indicateurs,
     décision, P&L et résultat.

  3. Après au moins 100 trades clôturés, on entraîne un
     challenger.

  4. Il ne remplace le champion que s’il est meilleur sur
     données fraîches : P&L net positif, profit factor ≥
     1,15, drawdown ≤ 15 % et validation walk-forward.

  Donc, notre prochaine étape n’est pas de tuner encore
  XGBoost ou de brancher le RL actuel. C’est de faire
  tourner et observer le bot autonome adaptatif sur Testnet,
  accumuler des expériences propres, puis entraîner un
  premier challenger à partir de ces données.


› okay crois-tu que je dois laisser tourner le backend et
  le bot combien de temps, pour etre sur qu'il apprenne
  assez
• Je vais te donner une durée fondée sur le fonctionnement
  réellement retenu : le critère utile n’est pas seulement
  le temps écoulé, mais le nombre de trades clôturés et la
  variété des régimes de marché observés.

• Laisse-le tourner jusqu’à avoir au minimum 100 trades
  clôturés, pas juste 100 décisions. C’est le seuil déjà
  retenu dans le projet avant même d’envisager un premier
  modèle challenger.

  Avec la limite de 4 trades/jour, le minimum théorique est
  25 jours actifs, mais en pratique je viserais :

  - 4 à 6 semaines : premier contrôle technique — vérifier
    qu’il enregistre bien décisions, positions, P&L, frais
    et fermetures.

  - 2 à 3 mois : objectif réaliste pour atteindre environ
    100 trades clôturés dans plusieurs contextes de marché.

  - 3 à 6 mois : base bien plus crédible pour évaluer une
    amélioration, car il aura vu tendance, range et
    volatilité forte.

  Important : actuellement, le bot n’apprend pas
  automatiquement pendant qu’il tourne. Il collecte ses
  expériences. L’apprentissage arrive ensuite : on entraîne
  un challenger à partir des trades enregistrés, on le teste
  hors échantillon, puis on ne le remplace que s’il dépasse
  rules-v1.

  Tu n’as pas besoin de laisser le frontend ouvert. Le
  backend doit rester lancé continuellement avec
  AUTONOMOUS_TRADING_ENABLED=true; idéalement, plus tard, on
  le mettra sur un serveur/VPS pour éviter les arrêts du
  Mac.


c'est quoi exactement? fincept terminal?


• Fincept Terminal est un logiciel de type terminal
  financier : une interface qui regroupe données de marché,
  graphiques, actualités, indicateurs, recherche et parfois
  outils de portefeuille ou de trading.

  Pense à Bloomberg Terminal, mais dans une version plus
  accessible et orientée développeurs/finance moderne.

  Pour TraderPro, il ne remplacerait pas notre application.
  Il pourrait fournir du contexte supplémentaire pour mieux
  - sa stratégie et son apprentissage ;
  - sa base d’expériences ;
  - ses ordres sur Binance Futures Demo ;
  - son suivi P&L et risque.
  financière ; TraderPro = notre bot de décision et
  d’exécution Testnet.


› mais comment il se presente c'est frontend et aussi un
  backend qui donne acces a tout un ecosysteme de trading,
  un peu comme trading view en local? ou j'ai rien compris?


• Oui, tu as globalement compris.

  Fincept Terminal se présente comme une application de
  bureau, avec une interface riche : graphiques, tableaux de
  marché, actualités, screener, portefeuille, analyse, etc.
  Donc visuellement, c’est proche d’un mélange entre
  TradingView et un terminal financier.

  Mais ce n’est pas forcément un unique « backend magique »
  qui possède toutes les données. Son principe est plutôt :

  Interface locale Fincept
  → connecteurs vers des fournisseurs de données / brokers /
  APIs
  → affichage, analyse et outils dans le terminal

  Il peut donc centraliser un écosystème de trading, mais
  les données viennent généralement de sources externes.
  Selon les connecteurs utilisés, certaines données peuvent
  être gratuites, différées, limitées ou payantes.

  Par rapport à TradingView :

  - TradingView : très orienté graphiques, indicateurs,
    communauté et alertes, principalement cloud.

  - Fincept : davantage un poste de travail financier
    extensible, potentiellement local, connecté à plusieurs
    sources de données et outils.

  - TraderPro : notre application spécialisée BTC Futures
    Demo, avec stratégie autonome, journal de trades et
    apprentissage contrôlé.

  Donc Fincept pourrait être un outil complémentaire pour
  nous, pas le moteur de TraderPro.


› okay nice donc on peut l'implementer alors dans notre
  systeme, mais qu'est ce qui fera vraiment? et comment il
  sera afficher cote frontend?


• Oui, mais on l’intégrerait comme une source de contexte de
  marché, pas comme une seconde application affichée dans
  TraderPro.

  Ce qu’il apporterait réellement au bot :

  Prix + indicateurs actuels
  + funding rate
  + open interest
  + ratio long/short
  + liquidations
  + volume acheteur/vendeur
  + news / sentiment / macro
  → meilleure lecture du régime de marché
  → stratégie plus sélective

  Exemples concrets :
    très chargé en LONG, donc éviter de suivre aveuglément
    une hausse.

  - Liquidations SHORT fortes + tendance haussière :
    confirmation possible d’un mouvement haussier.

  - Volatilité anormale ou news importante : réduire la
    réduire la confiance du signal.

  Le bot ne « devient pas Fincept ». Il conserverait sa
  logique actuelle, mais ses décisions auraient davantage de
  contexte :

  Fincept / sources de données
  → backend TraderPro : collecte et stockage
  → détecteur de régime + score de confiance
  │ Régime : Tendance haussière     Confiance : 78 % │
  ├──────────────┬──────────────┬───────────────────┤
  │ Funding      │ Open interest│ Liquidations      │
  │ +0,01 %      │ +4,2 %       │ Shorts élevés     │
  ├──────────────┴──────────────┴───────────────────┤
  │ Contexte : tendance confirmée, mais LONGs élevés │
  │ Décision : LONG autorisé avec prudence           │
  └─────────────────────────────────────────────────┘

  Et sur la page Historique, chaque trade afficherait aussi
  le contexte au moment de sa décision : régime, funding,
  OI, sentiment, raison d’entrée et résultat P&L. C’est
  précisément ce qui permettra au futur challenger
  d’apprendre quelles conditions donnent de bons trades.

  Le point à vérifier avant de coder est : Fincept donne-t-
  il une API officielle que nous pouvons consommer, ou faut-
  il connecter directement les mêmes fournisseurs de
  données. Dans les deux cas, l’interface TraderPro
  resterait la même.