# 🪙 Stablecoin Risk Lab

**Un stablecoin adossé au dirham, émis par une banque marocaine, peut-il être à la fois rentable et résilient face aux crises ?**

Projet d'analyse fintech complet : analyse empirique des stablecoins existants (USDT, USDC, DAI), mesure du risque, étude des crises historiques, cas d'usage marocain (transferts des MRE), business plan d'un stablecoin dirham fictif (« MADc ») et stress test de liquidité par simulation de Monte Carlo.

   🔗 **Dashboard interactif :** [stablecoin-risk-lab.streamlit.app](https://stablecoin-risk-lab.streamlit.app)

---

## 🎯 Contexte

Les stablecoins sont devenus une infrastructure clé de la finance numérique (paiements instantanés, transferts internationaux). Au Maroc, un projet de loi sur les cryptoactifs prévoit de placer les stablecoins sous la supervision de **Bank Al-Maghrib** et de réserver leur émission aux **banques et établissements de paiement**.

Ce projet évalue la viabilité d'un stablecoin dirham sous l'angle de la **stabilité**, du **risque**, de l'**utilité**, de la **rentabilité** et de la **résilience**.

## 📊 Principaux résultats

| Analyse | Résultat clé |
|---|---|
| Stabilité du peg | Depuis 2021, l'USDC ne s'écarte que de **1,9 pb** en moyenne de 1 \$ (contre 34 pb en 2020) |
| Risque de marché | VaR 99 % de **961 \$** par jour pour 1 M\$ en USDC, mais un **Expected Shortfall 3,3 fois supérieur** : un risque de queue marqué |
| Crises | Chaque crise frappe un stablecoin différent (Terra → USDT, SVB → USDC et DAI) ; le peg est rétabli en **moins de 5 jours** |
| Transferts des MRE | 122 Mds DH de transferts en 2025 et environ **6,4 Mds DH de frais** par an ; jusqu'à **2,6 Mds DH d'économies** avec un stablecoin régulé |
| Business plan MADc | Rentable dès l'**année 3**, **VAN de +32 M DH** et **TRI de 15,9 %**, mais une baisse des taux d'environ **30 pb** suffit à annuler la création de valeur |
| Stress test | Avec **20 % de liquidités**, le MADc résiste à **99,3 %** des 10 000 crises simulées |

## 🧠 Méthodes

- **Analyse du peg** : écart au peg en points de base, fréquence des dépassements de seuil, comparaison avant / après 2021
- **Risque de marché** : rendements journaliers, volatilité annualisée, **VaR historique** et **Expected Shortfall**
- **Étude d'événements** : profondeur (clôture et intrajournalier), durée et temps de récupération des crises Covid, Terra et SVB
- **Transferts des MRE** : comparaison des coûts par canal (données Banque mondiale) et analyse de sensibilité
- **Business plan** : compte de résultat sur 5 ans, **VAN**, **TRI**, délai de récupération, sensibilité aux taux
- **Stress test** : **simulation de Monte Carlo** (10 000 crises, loi Bêta), mobilisation séquentielle des réserves, arbitrage sécurité / rentabilité

## 🛠️ Technologies

Python · pandas · NumPy · Plotly · Streamlit · yfinance · Google Colab

## 📁 Structure du projet

```
stablecoin-risk-lab/
├── app.py                     # Dashboard Streamlit (affichage)
├── calculs.py                 # Toutes les fonctions de calcul
├── requirements.txt           # Bibliothèques nécessaires
├── .streamlit/config.toml     # Thème clair du dashboard
├── data/
│   ├── prix_stablecoins.csv       # Prix de clôture (2020-2026)
│   └── prix_bas_stablecoins.csv   # Prix les plus bas du jour
└── notebook/
    └── stablecoin_risk_lab.ipynb  # Analyse complète commentée
```

## ▶️ Lancer le dashboard en local

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📚 Sources

- Prix des stablecoins : Yahoo Finance
- Transferts des MRE : Office des changes
- Coût des transferts : Banque mondiale, *Remittance Prices Worldwide* (T3 2025)
- Taux des bons du Trésor : adjudications d'octobre 2026 ; taux directeur de Bank Al-Maghrib
- Fiscalité : IS de 40 % applicable aux établissements de crédit (2026)

## ⚠️ Limites

Le coût d'un transfert par stablecoin et la gravité des crises simulées reposent sur des **hypothèses**, testées par des analyses de sensibilité. Le MADc est un émetteur **fictif**, modélisé à des fins d'analyse.

---

**Auteur :** Ahmed Badi — Ingénieur financier (EMSI Rabat) · Data Analyst / Finance
