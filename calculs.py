"""
calculs.py — Toutes les fonctions de calcul du Stablecoin Risk Lab.

Ce fichier ne fait AUCUN affichage : il contient uniquement les calculs
(écart au peg, VaR, business plan, Monte Carlo...). L'application app.py
l'importe et se charge de l'affichage. Séparer calculs et affichage est
une bonne pratique : le code est plus lisible et plus facile à tester.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. DONNÉES
# ---------------------------------------------------------------------------

TICKERS = {"USDT": "USDT-USD", "USDC": "USDC-USD", "DAI": "DAI-USD"}
DOSSIER_DATA = Path(__file__).parent / "data"

CRISES = {
    "Covid (mars 2020)": ("2020-03-01", "2020-04-30"),
    "Terra (mai 2022)": ("2022-05-01", "2022-06-15"),
    "SVB (mars 2023)": ("2023-03-01", "2023-03-31"),
}


def charger_donnees():
    """Charge les prix de clôture (Close) et les plus bas du jour (Low).

    1) Si les fichiers CSV exportés depuis Colab sont présents dans data/,
       on les utilise (résultats identiques au notebook).
    2) Sinon, on télécharge les données depuis Yahoo Finance.
    """
    f_close = DOSSIER_DATA / "prix_stablecoins.csv"
    f_low = DOSSIER_DATA / "prix_bas_stablecoins.csv"

    if f_close.exists():
        close = pd.read_csv(f_close, index_col=0, parse_dates=True)
        if f_low.exists():
            low = pd.read_csv(f_low, index_col=0, parse_dates=True)
        else:
            low = close.copy()
        source = "fichiers CSV du projet"
    else:
        import yfinance as yf

        closes, lows = [], []
        for nom, code in TICKERS.items():
            h = yf.Ticker(code).history(start="2020-01-01")
            closes.append(h["Close"].rename(nom))
            lows.append(h["Low"].rename(nom))
        close = pd.concat(closes, axis=1)
        low = pd.concat(lows, axis=1)
        close.index = close.index.tz_localize(None)
        low.index = low.index.tz_localize(None)
        source = "Yahoo Finance (en direct)"

    close.index.name = "Date"
    low.index.name = "Date"
    return close.sort_index(), low.sort_index(), source


# ---------------------------------------------------------------------------
# 2. STABILITÉ DU PEG
# ---------------------------------------------------------------------------

def ecart_pb(prix):
    """Écart au peg en points de base : (prix - 1) x 10 000."""
    return (prix - 1) * 10_000


def statistiques_peg(prix, seuil_pb):
    """Tableau de synthèse de la stabilité de chaque stablecoin."""
    ecart_abs = ecart_pb(prix).abs()
    return pd.DataFrame({
        "Écart moyen (pb)": ecart_abs.mean(),
        f"% jours > {seuil_pb} pb": (ecart_abs > seuil_pb).mean() * 100,
        "Pire clôture ($)": prix.min(),
        "Date de la pire clôture": prix.idxmin().dt.date,
    })


def analyser_crise(close, low, debut, fin):
    """Profondeur, durée et temps de récupération d'une crise."""
    lignes = []
    for coin in close.columns:
        c = close[coin].loc[debut:fin].dropna()
        b = low[coin].loc[debut:fin].dropna()
        if c.empty:
            continue
        date_pire = c.idxmin()
        apres = c.loc[date_pire:]
        retour = apres[(apres - 1).abs() <= 0.001]
        recup = (retour.index[0] - date_pire).days if len(retour) else None
        lignes.append({
            "Stablecoin": coin,
            "Plus bas intrajournalier ($)": round(b.min(), 4),
            "Pire clôture ($)": round(c.min(), 4),
            "Date pire clôture": date_pire.date(),
            "Jours hors ±50 pb": int(((c - 1).abs() > 0.005).sum()),
            "Jours pour revenir à ±10 pb": recup,
        })
    return pd.DataFrame(lignes).set_index("Stablecoin")


# ---------------------------------------------------------------------------
# 3. RISQUE DE MARCHÉ : VaR et Expected Shortfall
# ---------------------------------------------------------------------------

def mesures_risque(rendements, niveau, montant):
    """VaR historique, Expected Shortfall et volatilité pour chaque colonne."""
    q = 1 - niveau
    lignes = {}
    for nom in rendements.columns:
        r = rendements[nom].dropna()
        seuil = r.quantile(q)
        es = r[r <= seuil].mean()
        var = -seuil * montant
        es_val = -es * montant
        lignes[nom] = {
            "VaR": var,
            "Expected Shortfall": es_val,
            "Ratio ES / VaR": es_val / var if var > 0 else np.nan,
            "Volatilité annualisée (%)": r.std() * np.sqrt(365) * 100,
        }
    return pd.DataFrame(lignes).T


# ---------------------------------------------------------------------------
# 4. TRANSFERTS DES MRE
# ---------------------------------------------------------------------------

# Coûts moyens au départ de la France (Banque mondiale, T3 2025)
CANAUX_MRE = {
    "Banque (virement international)": (18.59, "1 à 6 jours"),
    "Banque via opérateur partenaire": (4.58, "Le jour même"),
    "Opérateur de transfert": (4.09, "Moins d'une heure"),
    "Paiement mobile": (2.27, "Quelques minutes"),
}
COUT_MOYEN_MARCHE = 5.23        # % (moyenne de toutes les offres, France)
OBJECTIF_ONU = 3.0              # % (Objectif de développement durable n°10)
TRANSFERTS_MRE_2025 = 122       # milliards de DH (Office des changes)


def tableau_canaux(cout_stablecoin, montant, envois_par_an):
    """Frais par envoi et par an pour chaque canal, stablecoin compris."""
    lignes = [
        {"Canal": canal, "Coût total (%)": cout, "Délai": delai}
        for canal, (cout, delai) in CANAUX_MRE.items()
    ]
    lignes.append({"Canal": "Stablecoin (hypothèse)", "Coût total (%)": cout_stablecoin,
                   "Délai": "Quelques minutes, 24h/24"})
    df = pd.DataFrame(lignes)
    df["Frais par envoi (€)"] = df["Coût total (%)"] / 100 * montant
    df["Frais par an (€)"] = df["Frais par envoi (€)"] * envois_par_an
    return df


def economie_nationale(transferts_mds, adoption, cout_stablecoin, cout_actuel=COUT_MOYEN_MARCHE):
    """Économie annuelle (milliards de DH) si une part des transferts passe au stablecoin."""
    return transferts_mds * adoption * (cout_actuel - cout_stablecoin) / 100


# ---------------------------------------------------------------------------
# 5. BUSINESS PLAN DU MADc
# ---------------------------------------------------------------------------

TAUX_BT13 = 0.02170   # adjudication du 20/10/2026
TAUX_BT52 = 0.02363
TAUX_IS = 0.40        # IS des établissements de crédit (2026)
PROFIL_ENCOURS = np.array([1, 3, 6, 9, 12]) / 12
PROFIL_ADOPTION = np.array([0.10, 0.25, 0.50, 0.75, 1.00])
MARKETING = np.array([15, 15, 10, 10, 10])


def rendement_reserves(part_cash, choc_pb=0.0):
    """Rendement moyen pondéré des réserves (le cash ne rapporte rien).

    La partie placée est répartie 5/8 en BT 13 semaines et 3/8 en BT 52 semaines
    (soit 50 % / 30 % de l'encours quand le cash vaut 20 %).
    """
    choc = choc_pb / 10_000
    taux_place = 5 / 8 * (TAUX_BT13 + choc) + 3 / 8 * (TAUX_BT52 + choc)
    return (1 - part_cash) * taux_place


def business_plan(encours_an5=12, part_cash=0.20, choc_pb=0, commission=0.005,
                  adoption_an5=0.20, couts_fixes=75, cout_variable=0.001,
                  transferts_mre=TRANSFERTS_MRE_2025):
    """Compte de résultat sur 5 ans (en millions de DH)."""
    encours = encours_an5 * PROFIL_ENCOURS
    volume = transferts_mre * adoption_an5 * PROFIL_ADOPTION
    rend = rendement_reserves(part_cash, choc_pb)

    pl = pd.DataFrame(index=[f"Année {a}" for a in range(1, 6)])
    pl["Encours (Mds DH)"] = encours
    pl["Volume MRE (Mds DH)"] = volume
    pl["Revenus des réserves"] = encours * 1000 * rend
    pl["Commissions de transfert"] = volume * 1000 * commission
    pl["Chiffre d'affaires"] = pl["Revenus des réserves"] + pl["Commissions de transfert"]
    pl["Coûts fixes"] = couts_fixes + MARKETING
    pl["Coûts variables"] = volume * 1000 * cout_variable
    pl["Total charges"] = pl["Coûts fixes"] + pl["Coûts variables"]
    pl["Résultat avant impôt"] = pl["Chiffre d'affaires"] - pl["Total charges"]
    pl["Impôt (IS 40 %)"] = pl["Résultat avant impôt"].clip(lower=0) * TAUX_IS
    pl["Résultat net"] = pl["Résultat avant impôt"] - pl["Impôt (IS 40 %)"]
    return pl


def van(taux, flux):
    """Valeur actuelle nette : flux[0] est l'année 0 (non actualisée)."""
    return sum(f / (1 + taux) ** t for t, f in enumerate(flux))


def tri(flux):
    """Taux de rentabilité interne par dichotomie (None si introuvable)."""
    bas, haut = -0.99, 5.0
    if van(bas, flux) * van(haut, flux) > 0:
        return None
    for _ in range(200):
        milieu = (bas + haut) / 2
        if van(bas, flux) * van(milieu, flux) <= 0:
            haut = milieu
        else:
            bas = milieu
    return (bas + haut) / 2


def evaluer_projet(pl, capex, taux_actualisation):
    """VAN, TRI, délai de récupération et besoin de financement maximal."""
    flux = [-capex] + list(pl["Résultat net"])
    cumul = np.cumsum(flux)

    delai = None
    for t in range(1, len(cumul)):
        if cumul[t] >= 0 > cumul[t - 1]:
            delai = (t - 1) + (-cumul[t - 1]) / flux[t]
            break

    annee_rentable = next((i + 1 for i, r in enumerate(pl["Résultat net"]) if r > 0), None)

    return {
        "flux": flux,
        "cumul": cumul,
        "van": van(taux_actualisation, flux),
        "tri": tri(flux),
        "delai": delai,
        "besoin_max": -min(cumul.min(), 0),
        "annee_rentable": annee_rentable,
    }


def seuil_choc_taux(params, capex, taux_actualisation):
    """Choc de taux (pb) qui annule la VAN, cherché entre -400 et +400 pb."""
    def f(c):
        pl = business_plan(**{**params, "choc_pb": c})
        return van(taux_actualisation, [-capex] + list(pl["Résultat net"]))

    bas, haut = -400.0, 400.0
    if f(bas) * f(haut) > 0:
        return None
    for _ in range(80):
        milieu = (bas + haut) / 2
        if f(bas) * f(milieu) <= 0:
            haut = milieu
        else:
            bas = milieu
    return (bas + haut) / 2


# ---------------------------------------------------------------------------
# 6. STRESS TEST DE LIQUIDITÉ (MONTE CARLO)
# ---------------------------------------------------------------------------

POIDS_PANIQUE = np.array([0.25, 0.20, 0.15, 0.10, 0.08, 0.07, 0.05, 0.04, 0.03, 0.03])

# Gravité des crises : paramètre b de la loi Bêta(1,5 ; b)
GRAVITES = {
    "Modérée": 18.0,    # intensité moyenne ≈ 7,7 %
    "Centrale": 12.0,   # intensité moyenne ≈ 11,1 % (hypothèse du notebook)
    "Sévère": 7.0,      # intensité moyenne ≈ 17,6 %
}


def simuler_crises(part_cash, b=12.0, cap13=0.03, cap52=0.01,
                   n_simulations=10_000, seed=42, encours=12_000):
    """Simule n crises de 10 jours (version vectorisée : toutes les crises en même temps).

    Renvoie un DataFrame avec, pour chaque crise : intensité (%), rupture (bool),
    pertes de vente forcée (M DH).
    """
    rng = np.random.default_rng(seed)
    intensite = rng.beta(1.5, b, n_simulations)
    retraits = intensite[:, None] * encours * POIDS_PANIQUE[None, :]

    cash = np.full(n_simulations, part_cash * encours)
    bt13 = np.full(n_simulations, (1 - part_cash) * 5 / 8 * encours)
    bt52 = np.full(n_simulations, (1 - part_cash) * 3 / 8 * encours)
    pertes = np.zeros(n_simulations)
    rupture = np.zeros(n_simulations, dtype=bool)

    for jour in range(len(POIDS_PANIQUE)):
        besoin = retraits[:, jour].copy()

        paye = np.minimum(cash, besoin)                       # ① cash
        cash -= paye
        besoin -= paye

        vente = np.minimum(np.minimum(bt13, cap13 * encours), besoin)   # ② BT 13 sem.
        bt13 -= vente
        besoin -= vente
        pertes += vente * 0.0025

        vente = np.minimum(np.minimum(bt52, cap52 * encours), besoin)   # ③ BT 52 sem.
        bt52 -= vente
        besoin -= vente
        pertes += vente * 0.02

        rupture |= besoin > 1e-9

    return pd.DataFrame({
        "Intensité (%)": intensite * 100,
        "Rupture": rupture,
        "Pertes de vente forcée (M DH)": pertes,
    })


def courbe_arbitrage(b=12.0, cap13=0.03, cap52=0.01, n_simulations=10_000,
                     niveaux=(0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50),
                     encours=12_000):
    """Probabilité de rupture et revenus des réserves pour chaque niveau de cash."""
    lignes = []
    for c in niveaux:
        s = simuler_crises(c, b, cap13, cap52, n_simulations, encours=encours)
        lignes.append({
            "Part de cash (%)": int(round(c * 100)),
            "Probabilité de rupture (%)": s["Rupture"].mean() * 100,
            "Pertes moyennes (M DH)": s["Pertes de vente forcée (M DH)"].mean(),
            "Revenus des réserves an 5 (M DH)": encours * rendement_reserves(c),
        })
    return pd.DataFrame(lignes)
