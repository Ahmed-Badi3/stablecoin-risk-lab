"""
app.py — Dashboard interactif du Stablecoin Risk Lab.

Lancer en local :   streamlit run app.py
Tous les calculs se trouvent dans calculs.py ; ce fichier gère l'affichage.
"""

from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import calculs as c

# ---------------------------------------------------------------------------
# CONFIGURATION GÉNÉRALE
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Stablecoin Risk Lab",
    page_icon="🪙",
    layout="wide",
    initial_sidebar_state="expanded",
)

COULEURS = {"USDT": "#26A17B", "USDC": "#2775CA", "DAI": "#F5AC37"}
VERT, ROUGE, ORANGE, GRIS = "#16A34A", "#DC2626", "#F59E0B", "#6B7280"

# Un peu de mise en forme : cartes blanches, titres plus aérés
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    div[data-testid="stMetric"] {
        background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 14px 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    div[data-testid="stMetricLabel"] p {font-size: 0.9rem; color: #4B5563;}
    .hero {
        background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
        border: 1px solid #DBEAFE; border-radius: 16px; padding: 24px 28px; margin-bottom: 1rem;
    }
    .hero h1 {margin: 0 0 6px 0; font-size: 2.1rem; color: #1E3A8A;}
    .hero p {margin: 0; font-size: 1.05rem; color: #374151;}
    .etape {
        background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
        padding: 14px 16px; height: 100%;
    }
    .etape b {color: #1E3A8A;}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# PETITS OUTILS D'AFFICHAGE
# ---------------------------------------------------------------------------

def mise_en_forme(fig, hauteur=420, survol_unifie=False):
    """Style commun à tous les graphiques : fond blanc, légende en haut."""
    fig.update_layout(
        template="plotly_white",
        height=hauteur,
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        font=dict(size=13),
        title_font=dict(size=16),
    )
    if survol_unifie:
        fig.update_layout(hovermode="x unified")
    return fig


def a_retenir(texte, ton="info"):
    """Encadré d'interprétation sous un graphique."""
    message = f"💡 **Ce qu'il faut retenir.** {texte}"
    {"info": st.info, "succes": st.success, "alerte": st.warning, "danger": st.error}[ton](message)


def comment_lire(texte):
    """Aide de lecture repliable."""
    with st.expander("👀 Comment lire ce graphique ?"):
        st.markdown(texte)


def mdh(x, decimales=1):
    """Formate un montant en millions de DH, à la française."""
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",") + " M DH"


def fr(x, decimales=1):
    """Nombre avec une virgule décimale (format français)."""
    return f"{x:.{decimales}f}".replace(".", ",")


def pct(x, decimales=1):
    return f"{x:.{decimales}f}".replace(".", ",") + " %"


def nombre(x, decimales=0):
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


# ---------------------------------------------------------------------------
# DONNÉES (mises en cache : chargées une seule fois)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=24 * 3600, show_spinner="Chargement des données de marché…")
def donnees():
    return c.charger_donnees()


@st.cache_data(show_spinner="Simulation des crises en cours…")
def simulation(part_cash, b, cap13, cap52, n):
    return c.simuler_crises(part_cash, b, cap13, cap52, n)


@st.cache_data(show_spinner="Calcul de la courbe d'arbitrage…")
def arbitrage(b, cap13, cap52, n):
    return c.courbe_arbitrage(b, cap13, cap52, n)


try:
    close, low, source = donnees()
except Exception as erreur:  # pas de fichier CSV et pas d'accès à Internet
    st.error(
        "Impossible de charger les données. Placez les fichiers `prix_stablecoins.csv` "
        "et `prix_bas_stablecoins.csv` dans le dossier `data/`, ou vérifiez la connexion Internet.\n\n"
        f"Détail : {erreur}"
    )
    st.stop()

DATE_MIN, DATE_MAX = close.index.min().date(), close.index.max().date()


# ---------------------------------------------------------------------------
# BARRE LATÉRALE
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🪙 Stablecoin Risk Lab")
    st.markdown(
        "**Un stablecoin adossé au dirham est-il viable et résilient ?**\n\n"
        "Analyse empirique des stablecoins, cas d'usage marocain, business plan "
        "et stress test de liquidité."
    )
    st.divider()
    st.markdown("**Auteur** : Ahmed Badi  \nIngénieur financier — EMSI Rabat")
    st.markdown(f"**Données** : {source}  \n{DATE_MIN:%d/%m/%Y} → {DATE_MAX:%d/%m/%Y}")
    st.divider()
    st.caption(
        "Chaque onglet contient des curseurs : modifiez les hypothèses, "
        "les graphiques et les interprétations se mettent à jour automatiquement."
    )


# ---------------------------------------------------------------------------
# ONGLETS
# ---------------------------------------------------------------------------

onglets = st.tabs([
    "🏠 Accueil",
    "📉 Stabilité du peg",
    "⚠️ Risque (VaR)",
    "🇲🇦 Transferts MRE",
    "💼 Business plan MADc",
    "🎲 Stress test",
    "📚 Méthodologie",
])


# ===========================================================================
# 1. ACCUEIL
# ===========================================================================
with onglets[0]:
    st.markdown(
        """
        <div class="hero">
          <h1>Stablecoin Risk Lab</h1>
          <p>Un stablecoin adossé au dirham, émis par une banque marocaine, peut-il être
          à la fois <b>rentable</b> et <b>résilient</b> face aux crises ?</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Indicateurs clés calculés en direct avec les hypothèses de base
    recent = close.loc["2021-01-01":]
    ecart_usdc = c.ecart_pb(recent["USDC"]).abs().mean()
    risque_base = c.mesures_risque(recent.pct_change().dropna(), 0.99, 1_000_000)
    pl_base = c.business_plan()
    eval_base = c.evaluer_projet(pl_base, 80, 0.10)
    sim_base = simulation(0.20, 12.0, 0.03, 0.01, 10_000)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Écart moyen de l'USDC au peg (depuis 2021)", f"{ecart_usdc:.1f} pb".replace(".", ","))
    k2.metric("VaR 99 % sur 1 M$ en USDC (1 jour)", f"{nombre(risque_base.loc['USDC', 'VaR'])} $")
    k3.metric("VAN du MADc (scénario central)", mdh(eval_base["van"]))
    k4.metric("Risque de rupture avec 20 % de cash", pct(sim_base["Rupture"].mean() * 100, 2))

    st.markdown("### Le parcours de l'analyse")
    e1, e2, e3, e4, e5 = st.columns(5)
    etapes = [
        ("📉", "Stabilité du peg", "Les stablecoins restent-ils vraiment à 1 $ ?"),
        ("⚠️", "Risque", "Combien peut-on perdre lors d'un mauvais jour ?"),
        ("🇲🇦", "Transferts MRE", "Combien les familles pourraient-elles économiser ?"),
        ("💼", "Business plan", "Un stablecoin dirham serait-il rentable ?"),
        ("🎲", "Stress test", "Résisterait-il à une panique bancaire ?"),
    ]
    for col, (icone, titre, question) in zip([e1, e2, e3, e4, e5], etapes):
        col.markdown(f'<div class="etape">{icone} <b>{titre}</b><br>{question}</div>',
                     unsafe_allow_html=True)

    st.markdown("### Les principales conclusions")
    st.markdown(
        """
        - **Les stablecoins adossés à des réserves sont devenus très stables** depuis 2021 :
          quelques points de base d'écart en moyenne. Leur danger n'est plus la fluctuation
          quotidienne, mais la **crise de confiance soudaine** (Terra 2022, SVB 2023).
        - **Les transferts des MRE** (122 milliards de DH en 2025) coûtent environ 6,4 milliards
          de DH de frais par an : un stablecoin régulé pourrait en économiser plusieurs milliards.
        - **Le MADc serait rentable dès l'année 3**, mais très **dépendant des taux d'intérêt** :
          une baisse d'environ 30 pb suffirait à rendre la VAN négative.
        - **Avec 20 % de réserves en liquidités**, le MADc résiste à plus de 99 % des crises simulées.
        """
    )
    st.caption(
        "👉 Utilisez les onglets en haut de la page pour explorer chaque partie et tester vos propres hypothèses."
    )


# ===========================================================================
# 2. STABILITÉ DU PEG
# ===========================================================================
with onglets[1]:
    st.header("📉 Les stablecoins restent-ils à 1 $ ?")
    st.markdown(
        "Un stablecoin promet de valoir **toujours 1 dollar** : c'est le **peg**. "
        "On mesure ici de combien chaque stablecoin s'en écarte, en **points de base** "
        "(1 pb = 0,01 %, donc 100 pb = 1 %)."
    )

    f1, f2, f3, f4 = st.columns([1.2, 2, 1.2, 1])
    choix = f1.multiselect("Stablecoins", list(close.columns), default=list(close.columns))
    periode = f2.slider("Période", min_value=DATE_MIN, max_value=DATE_MAX,
                        value=(DATE_MIN, DATE_MAX), format="DD/MM/YYYY")
    seuil = f3.slider("Seuil d'alerte (pb)", 10, 200, 50, step=10,
                      help="On considère qu'il y a un écart significatif au-delà de ce seuil.")
    vue = f4.radio("Afficher", ["Écart (pb)", "Prix ($)"], horizontal=False)

    if not choix:
        st.warning("Sélectionnez au moins un stablecoin.")
    else:
        prix_p = close.loc[str(periode[0]):str(periode[1]), choix]

        if vue == "Prix ($)":
            fig = px.line(prix_p, color_discrete_map=COULEURS,
                          labels={"value": "Prix ($)", "Date": "", "variable": ""})
            fig.add_hline(y=1, line_dash="dash", line_color="black")
            fig.add_hrect(y0=1 - seuil / 10_000, y1=1 + seuil / 10_000, fillcolor=VERT,
                          opacity=0.08, line_width=0)
        else:
            fig = px.line(c.ecart_pb(prix_p), color_discrete_map=COULEURS,
                          labels={"value": "Écart au peg (pb)", "Date": "", "variable": ""})
            fig.add_hline(y=0, line_dash="dash", line_color="black")
            fig.add_hrect(y0=-seuil, y1=seuil, fillcolor=VERT, opacity=0.08, line_width=0)
        fig.update_layout(title="Évolution par rapport au peg")
        st.plotly_chart(mise_en_forme(fig, 430, survol_unifie=True))

        comment_lire(
            f"- La **ligne noire** représente le peg (1 \\$, soit un écart de 0).\n"
            f"- La **bande verte** est la zone « normale » : écart inférieur à {seuil} pb.\n"
            "- Une courbe qui sort de la bande signale un **décrochage**.\n"
            "- Sélectionnez une zone du graphique avec la souris pour **zoomer** "
            "(double-clic pour revenir)."
        )

        stats = c.statistiques_peg(prix_p, seuil)
        stats_aff = stats.copy()
        stats_aff["Écart moyen (pb)"] = stats_aff["Écart moyen (pb)"].round(1)
        stats_aff[f"% jours > {seuil} pb"] = stats_aff[f"% jours > {seuil} pb"].round(2)
        stats_aff["Pire clôture ($)"] = stats_aff["Pire clôture ($)"].round(4)
        st.dataframe(stats_aff)

        plus_stable = stats["Écart moyen (pb)"].idxmin()
        moins_stable = stats["Écart moyen (pb)"].idxmax()
        texte = (
            f"Sur la période choisie, **{plus_stable}** est le plus proche du peg "
            f"({fr(stats.loc[plus_stable, 'Écart moyen (pb)'])} pb d'écart en moyenne)"
        )
        if len(choix) > 1:
            texte += (
                f", et **{moins_stable}** le plus instable "
                f"({fr(stats.loc[moins_stable, 'Écart moyen (pb)'])} pb), "
                f"avec {fr(stats.loc[moins_stable, f'% jours > {seuil} pb'])} % des jours "
                f"au-delà de {seuil} pb"
            )
        texte += "."
        if periode[0] < date(2021, 1, 1):
            texte += (" La période inclut **2020**, année d'un marché encore jeune et peu liquide : "
                      "essayez de la démarrer en 2021 pour voir à quel point les écarts se réduisent.")
        a_retenir(texte)

    st.divider()
    st.subheader("🔎 Zoom sur une crise")
    crise = st.selectbox("Choisissez une crise", list(c.CRISES.keys()), index=2)
    debut, fin = c.CRISES[crise]
    afficher_low = st.toggle("Afficher aussi le prix le plus bas de chaque journée (en pointillés)", value=True)

    fig = go.Figure()
    for coin in close.columns:
        fig.add_scatter(x=close.loc[debut:fin].index, y=close.loc[debut:fin, coin], name=f"{coin} (clôture)",
                        line=dict(color=COULEURS[coin], width=2.5))
        if afficher_low:
            fig.add_scatter(x=low.loc[debut:fin].index, y=low.loc[debut:fin, coin], name=f"{coin} (plus bas)",
                            line=dict(color=COULEURS[coin], width=1.2, dash="dot"))
    fig.add_hline(y=1, line_dash="dash", line_color="black")
    fig.add_hrect(y0=0.995, y1=1.005, fillcolor=VERT, opacity=0.08, line_width=0)
    fig.update_layout(title=f"Crise : {crise}", yaxis_title="Prix ($)")
    st.plotly_chart(mise_en_forme(fig, 430, survol_unifie=True))

    tab_crise = c.analyser_crise(close, low, debut, fin)
    st.dataframe(tab_crise)

    plus_touche = tab_crise["Plus bas intrajournalier ($)"].idxmin()
    creux = tab_crise.loc[plus_touche, "Plus bas intrajournalier ($)"]
    cloture = tab_crise.loc[plus_touche, "Pire clôture ($)"]
    recits = {
        "Covid (mars 2020)": "un **choc systémique** : tous les marchés paniquent, les stablecoins "
                             "décrochent dans les deux sens.",
        "Terra (mai 2022)": "une **crise de confiance sur les réserves** : après l'effondrement de l'UST, "
                            "l'USDT, jugé peu transparent, est le plus attaqué.",
        "SVB (mars 2023)": "un **choc de contrepartie** : une partie des réserves de l'USDC est bloquée "
                           "dans une banque en faillite, et le DAI chute avec lui par contagion.",
    }
    a_retenir(
        f"Cette crise est {recits[crise]} Le stablecoin le plus touché est **{plus_touche}**, "
        f"tombé à **{fr(creux, 4)} \\$** pendant la journée, alors que sa pire clôture n'est que de "
        f"{fr(cloture, 4)} \\$ : les prix de clôture **sous-estiment** la violence réelle des crises.",
        ton="alerte",
    )


# ===========================================================================
# 3. RISQUE (VaR / ES)
# ===========================================================================
with onglets[2]:
    st.header("⚠️ Combien peut-on perdre lors d'un mauvais jour ?")
    st.markdown(
        "Une entreprise détient sa trésorerie en stablecoins. La **VaR** (Value at Risk) répond à : "
        "« *quelle perte ne dépassera-t-on pas dans X % des jours ?* ». "
        "L'**Expected Shortfall** répond à : « *quand ça va vraiment mal, combien perd-on en moyenne ?* »."
    )

    r1, r2, r3 = st.columns(3)
    montant = r1.select_slider("Montant détenu ($)", options=[100_000, 500_000, 1_000_000, 5_000_000, 10_000_000],
                               value=1_000_000, format_func=lambda x: f"{nombre(x)} $")
    niveau = r2.select_slider("Niveau de confiance", options=[0.90, 0.95, 0.99, 0.995], value=0.99,
                              format_func=lambda x: f"{x * 100:g} %".replace(".", ","))
    per = r3.radio("Période d'analyse", ["Depuis 2021 (marché mature)", "Depuis 2020 (avec le krach du Covid)"])

    debut_r = "2021-01-01" if per.startswith("Depuis 2021") else "2020-01-01"
    rend = close.loc[debut_r:].pct_change().dropna()
    risque = c.mesures_risque(rend, niveau, montant)

    m = st.columns(3)
    for col, coin in zip(m, risque.index):
        col.metric(f"{coin} — VaR {niveau * 100:g} %".replace(".", ","), f"{nombre(risque.loc[coin, 'VaR'])} $",
                   delta=f"ES : {nombre(risque.loc[coin, 'Expected Shortfall'])} $", delta_color="off")

    long = risque[["VaR", "Expected Shortfall"]].reset_index(names="Stablecoin").melt(
        id_vars="Stablecoin", var_name="Mesure", value_name="Perte ($)")
    fig = px.bar(long, x="Stablecoin", y="Perte ($)", color="Mesure", barmode="group", text_auto=",.0f",
                 color_discrete_map={"VaR": "#93C5FD", "Expected Shortfall": "#1D4ED8"},
                 title=f"Perte potentielle sur une journée pour {nombre(montant)} $")
    st.plotly_chart(mise_en_forme(fig, 400))

    comment_lire(
        "- **Barre claire (VaR)** : la perte qu'on ne dépasse pas lors des jours « normalement mauvais ».\n"
        "- **Barre foncée (Expected Shortfall)** : la perte moyenne lors des **pires** jours.\n"
        "- Plus l'écart entre les deux barres est grand, plus les crises sont **violentes** par rapport "
        "aux mauvais jours ordinaires : c'est le **risque de queue**."
    )

    tab_r = risque.copy()
    tab_r["VaR"] = tab_r["VaR"].round(0)
    tab_r["Expected Shortfall"] = tab_r["Expected Shortfall"].round(0)
    tab_r["Ratio ES / VaR"] = tab_r["Ratio ES / VaR"].round(2)
    tab_r["Volatilité annualisée (%)"] = tab_r["Volatilité annualisée (%)"].round(2)
    st.dataframe(tab_r)

    moins_risque = risque["VaR"].idxmin()
    queue = risque["Ratio ES / VaR"].idxmax()
    texte = (
        f"Selon la VaR, **{moins_risque}** est le stablecoin le moins risqué "
        f"({nombre(risque.loc[moins_risque, 'VaR'])} \\$ pour {nombre(montant)} \\$, soit "
        f"{fr(risque.loc[moins_risque, 'VaR'] / montant * 100, 2)} % du capital). "
    )
    if queue == moins_risque:
        texte += (f"Pourtant, c'est aussi lui qui présente le ratio ES / VaR le plus élevé "
                  f"({fr(risque.loc[queue, 'Ratio ES / VaR'])}) : ")
    else:
        texte += (f"Mais **{queue}** présente le ratio ES / VaR le plus élevé "
                  f"({fr(risque.loc[queue, 'Ratio ES / VaR'])}) : ")
    texte += ("ses pires jours sont bien plus violents que ses mauvais jours habituels. "
              "La VaR seule peut donc **masquer** un risque de crise.")
    a_retenir(texte)

    st.divider()
    st.subheader("📊 La distribution des rendements journaliers")
    coin_h = st.radio("Stablecoin à examiner", list(close.columns), index=1, horizontal=True)
    r_pb = rend[coin_h] * 10_000
    var_pb = -r_pb.quantile(1 - niveau)
    es_pb = -r_pb[r_pb <= r_pb.quantile(1 - niveau)].mean()

    fig = px.histogram(r_pb, nbins=200, log_y=True, color_discrete_sequence=[COULEURS[coin_h]],
                       labels={"value": "Rendement journalier (pb)"})
    fig.add_vline(x=-var_pb, line_dash="dash", line_color=ORANGE,
                  annotation_text=f"VaR {niveau * 100:g} %", annotation_position="top left")
    fig.add_vline(x=-es_pb, line_dash="dash", line_color=ROUGE,
                  annotation_text="Expected Shortfall", annotation_position="bottom left")
    fig.update_layout(showlegend=False, yaxis_title="Nombre de jours (échelle log)",
                      title=f"{coin_h} : combien de jours pour chaque niveau de rendement ?")
    st.plotly_chart(mise_en_forme(fig, 400))

    comment_lire(
        "- Chaque barre compte **le nombre de jours** ayant eu ce rendement.\n"
        "- L'axe vertical est en **échelle logarithmique** : elle « écrase » les grands nombres pour "
        "qu'on puisse voir les rares jours extrêmes (1 ou 2 jours) à côté des milliers de jours calmes.\n"
        "- Les **petites barres isolées loin du centre** sont les jours de crise."
    )
    pire = r_pb.min()
    a_retenir(
        f"La grande majorité des jours se concentre autour de 0. Pourtant, le pire jour de {coin_h} "
        f"atteint **{pire:.0f} pb**, soit environ **{abs(pire) / var_pb:.0f} fois la VaR**. "
        "C'est la signature d'une distribution à **queues épaisses** : les crises sont rares, mais d'une "
        "ampleur qu'un modèle classique (loi normale) sous-estimerait fortement.",
        ton="alerte",
    )


# ===========================================================================
# 4. TRANSFERTS DES MRE
# ===========================================================================
with onglets[3]:
    st.header("🇲🇦 Combien les familles marocaines pourraient-elles économiser ?")
    st.markdown(
        f"Les Marocains résidant à l'étranger ont envoyé **plus de {c.TRANSFERTS_MRE_2025} milliards de DH** "
        "en 2025. Chaque transfert coûte des frais affichés **et** une perte cachée sur le taux de change. "
        "Comparons les canaux actuels à un futur stablecoin dirham régulé."
    )

    t1, t2, t3, t4 = st.columns(4)
    montant_envoi = t1.slider("Montant d'un envoi (€)", 50, 1000, 140, step=10)
    envois = t2.slider("Envois par an", 1, 24, 12)
    cout_sc = t3.slider("Coût du stablecoin (%)", 0.2, 3.0, 1.0, step=0.1,
                        help="Hypothèse : achat ≈ 0,5 % + transfert quasi gratuit + conversion en dirhams ≈ 0,5 %.")
    adoption = t4.slider("Part des transferts en stablecoin (%)", 0, 100, 50, step=5)

    canaux = c.tableau_canaux(cout_sc, montant_envoi, envois)
    couleurs_canaux = [GRIS, GRIS, GRIS, GRIS, VERT]
    fig = go.Figure(go.Bar(
        x=canaux["Canal"], y=canaux["Coût total (%)"], marker_color=couleurs_canaux,
        text=[pct(v, 2) for v in canaux["Coût total (%)"]], textposition="outside",
    ))
    fig.add_hline(y=c.COUT_MOYEN_MARCHE, line_dash="dot", line_color=GRIS,
                  annotation_text="Moyenne du marché : 5,23 %", annotation_position="top right")
    fig.add_hline(y=c.OBJECTIF_ONU, line_dash="dash", line_color=VERT,
                  annotation_text="Objectif ONU 2030 : 3 %", annotation_position="bottom right")
    fig.update_layout(title="Coût total d'un envoi France → Maroc, selon le canal",
                      yaxis_title="Coût (% du montant envoyé)",
                      yaxis_range=[0, max(canaux["Coût total (%)"]) * 1.15])
    st.plotly_chart(mise_en_forme(fig, 420))

    comment_lire(
        "- Chaque barre montre le **coût total** (frais + perte de change) en % du montant envoyé.\n"
        "- La **barre verte** est le stablecoin (selon votre hypothèse de coût).\n"
        "- Sous la **ligne verte** (3 %), un canal respecte l'objectif fixé par les Nations unies."
    )

    operateur = canaux.loc[canaux["Canal"] == "Opérateur de transfert", "Frais par an (€)"].iloc[0]
    stablecoin = canaux.loc[canaux["Canal"] == "Stablecoin (hypothèse)", "Frais par an (€)"].iloc[0]

    st.subheader("👨‍👩‍👧 Pour une famille")
    m1, m2, m3 = st.columns(3)
    m1.metric("Frais annuels — opérateur de transfert", f"{nombre(operateur, 2)} €")
    m2.metric("Frais annuels — stablecoin", f"{nombre(stablecoin, 2)} €")
    m3.metric("Économie par famille et par an", f"{nombre(operateur - stablecoin, 2)} €",
              delta=pct(-(1 - stablecoin / operateur) * 100, 0) if operateur else None,
              delta_color="inverse")

    aff = canaux.copy()
    aff["Frais par envoi (€)"] = aff["Frais par envoi (€)"].round(2)
    aff["Frais par an (€)"] = aff["Frais par an (€)"].round(2)
    st.dataframe(aff, hide_index=True)

    st.subheader("🇲🇦 À l'échelle du Maroc")
    frais_actuels = c.TRANSFERTS_MRE_2025 * c.COUT_MOYEN_MARCHE / 100
    eco = c.economie_nationale(c.TRANSFERTS_MRE_2025, adoption / 100, cout_sc)
    n1, n2 = st.columns(2)
    n1.metric("Frais payés aujourd'hui par les familles", f"{frais_actuels:.2f} Mds DH / an".replace(".", ","))
    n2.metric("Économie annuelle avec le stablecoin", f"{eco:.2f} Mds DH / an".replace(".", ","),
              delta=f"{eco / frais_actuels * 100:.0f} % des frais actuels" if frais_actuels else None)

    adoptions = np.arange(0, 101, 5)
    courbes = pd.DataFrame({
        "Adoption (%)": np.tile(adoptions, 3),
        "Coût du stablecoin": np.repeat(["0,5 %", f"{cout_sc:.1f} % (votre choix)".replace(".", ","), "2 %"],
                                        len(adoptions)),
        "Économie (Mds DH)": np.concatenate([
            c.economie_nationale(c.TRANSFERTS_MRE_2025, adoptions / 100, x) for x in (0.5, cout_sc, 2.0)
        ]),
    })
    fig = px.line(courbes, x="Adoption (%)", y="Économie (Mds DH)", color="Coût du stablecoin",
                  color_discrete_sequence=["#93C5FD", VERT, "#FCA5A5"],
                  title="Économie annuelle selon la part des transferts en stablecoin")
    fig.add_vline(x=adoption, line_dash="dot", line_color="black",
                  annotation_text="Votre scénario", annotation_position="top left")
    st.plotly_chart(mise_en_forme(fig, 400, survol_unifie=True))

    texte = (
        f"Avec un stablecoin à {fr(cout_sc)} % et {adoption} % d'adoption, les familles marocaines "
        f"économiseraient environ **{fr(eco, 2)} milliards de DH par an**. "
    )
    texte += (
        "Remarquez que les courbes s'écartent peu les unes des autres : **le niveau d'adoption compte bien "
        "plus que le coût exact du stablecoin**. Le vrai facteur de succès est donc la **confiance** des "
        "utilisateurs et la simplicité d'usage."
    )
    a_retenir(texte, ton="succes" if eco > 0 else "alerte")
    st.caption("Sources : Office des changes (transferts 2025) ; Banque mondiale, Remittance Prices Worldwide "
               "(T3 2025, envoi de 140 € au départ de la France).")


# ===========================================================================
# 5. BUSINESS PLAN DU MADc
# ===========================================================================
with onglets[4]:
    st.header("💼 Un stablecoin dirham serait-il rentable ?")
    st.markdown(
        "Une banque marocaine émet le **MADc** (1 MADc = 1 DH). Elle place les dirhams déposés "
        "en **bons du Trésor** et garde les intérêts, et prend une **commission** sur les transferts des MRE. "
        "Modifiez les hypothèses pour voir l'impact sur la rentabilité."
    )

    with st.container(border=True):
        st.markdown("**⚙️ Hypothèses**")
        h1, h2, h3, h4 = st.columns(4)
        encours5 = h1.slider("Encours en année 5 (Mds DH)", 2, 30, 12)
        part_cash_bp = h2.slider("Réserves gardées en cash (%)", 5, 50, 20, step=5)
        choc = h3.slider("Variation des taux des bons du Trésor (pb)", -150, 150, 0, step=10,
                         help="0 = taux actuels (BT 13 semaines : 2,170 % ; BT 52 semaines : 2,363 %).")
        commission = h4.slider("Commission sur les transferts (%)", 0.0, 1.0, 0.5, step=0.1)
        h5, h6, h7, h8 = st.columns(4)
        adoption5 = h5.slider("Part des transferts MRE en MADc, an 5 (%)", 0, 50, 20)
        couts_fixes = h6.slider("Coûts fixes hors marketing (M DH / an)", 30, 150, 75, step=5)
        capex = h7.slider("Investissement initial — CAPEX (M DH)", 20, 200, 80, step=10)
        taux_act = h8.slider("Rendement exigé (%)", 6, 15, 10)

    params = dict(encours_an5=encours5, part_cash=part_cash_bp / 100, choc_pb=choc,
                  commission=commission / 100, adoption_an5=adoption5 / 100, couts_fixes=couts_fixes)
    pl = c.business_plan(**params)
    ev = c.evaluer_projet(pl, capex, taux_act / 100)

    k = st.columns(5)
    k[0].metric("VAN", mdh(ev["van"]), delta="crée de la valeur" if ev["van"] > 0 else "détruit de la valeur",
                delta_color="normal" if ev["van"] > 0 else "inverse")
    k[1].metric("TRI", pct(ev["tri"] * 100) if ev["tri"] is not None else "—",
                delta=f"exigé : {taux_act} %", delta_color="off")
    k[2].metric("Première année rentable", f"Année {ev['annee_rentable']}" if ev["annee_rentable"] else "Jamais")
    k[3].metric("Délai de récupération",
                f"{ev['delai']:.1f} ans".replace(".", ",") if ev["delai"] is not None else "> 5 ans")
    k[4].metric("Besoin de financement max.", mdh(ev["besoin_max"]))

    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        fig.add_bar(x=pl.index, y=pl["Chiffre d'affaires"], name="Chiffre d'affaires", marker_color="#60A5FA")
        fig.add_bar(x=pl.index, y=pl["Total charges"], name="Charges", marker_color="#FCA5A5")
        fig.add_scatter(x=pl.index, y=pl["Résultat net"], name="Résultat net", mode="lines+markers+text",
                        text=[f"{v:.0f}" for v in pl["Résultat net"]], textposition="top center",
                        line=dict(color=VERT, width=3))
        fig.add_hline(y=0, line_color="black")
        fig.update_layout(barmode="group", title="Compte de résultat (M DH)")
        st.plotly_chart(mise_en_forme(fig, 400))
    with g2:
        annees = ["Année 0"] + list(pl.index)
        fig = go.Figure()
        fig.add_bar(x=annees, y=ev["flux"], name="Flux de l'année",
                    marker_color=[ROUGE if f < 0 else VERT for f in ev["flux"]])
        fig.add_scatter(x=annees, y=ev["cumul"], name="Solde cumulé", mode="lines+markers",
                        line=dict(color="#1D4ED8", width=3))
        fig.add_hline(y=0, line_color="black")
        fig.update_layout(title="Récupère-t-on la mise ? (flux de trésorerie, M DH)")
        st.plotly_chart(mise_en_forme(fig, 400))

    comment_lire(
        "**À gauche** : quand la barre bleue (ce qui rentre) dépasse la barre rouge (ce qui sort), "
        "le projet gagne de l'argent. La courbe verte est le résultat net après impôt (IS de 40 %).\n\n"
        "**À droite** : imaginez le compte en banque du projet. On part de −CAPEX, puis on ajoute "
        "chaque année le résultat net. Quand la courbe bleue repasse **au-dessus de zéro**, "
        "l'investissement est **remboursé**."
    )

    with st.expander("📋 Voir le compte de résultat détaillé"):
        st.dataframe(pl.T.round(1))

    if ev["van"] > 0:
        texte = (f"Avec ces hypothèses, le MADc **crée de la valeur** : VAN de {mdh(ev['van'])}"
                 + (f" et TRI de {pct(ev['tri'] * 100)}" if ev["tri"] is not None else "")
                 + f", supérieur aux {taux_act} % exigés. ")
        ton = "succes"
    else:
        texte = (f"Avec ces hypothèses, le MADc **détruit de la valeur** (VAN de {mdh(ev['van'])}) : "
                 "il ne rapporte pas assez pour justifier l'investissement. ")
        ton = "danger"
    part_reserves = pl["Revenus des réserves"].iloc[-1] / pl["Chiffre d'affaires"].iloc[-1] * 100
    texte += (f"En année 5, **{part_reserves:.0f} % des revenus** proviennent des intérêts sur les réserves : "
              "la rentabilité dépend donc fortement des taux d'intérêt.")
    a_retenir(texte, ton)

    st.divider()
    st.subheader("📉 Que se passe-t-il si les taux d'intérêt changent ?")
    chocs = list(range(-150, 151, 25))
    vans = [c.van(taux_act / 100, [-capex] + list(c.business_plan(**{**params, "choc_pb": x})["Résultat net"]))
            for x in chocs]
    fig = go.Figure(go.Bar(x=[f"{x:+d}" for x in chocs], y=vans,
                           marker_color=[VERT if v > 0 else ROUGE for v in vans],
                           text=[f"{v:.0f}" for v in vans], textposition="outside"))
    fig.add_hline(y=0, line_color="black")
    fig.update_layout(title="VAN du MADc selon la variation des taux des bons du Trésor",
                      xaxis_title="Variation des taux par rapport à aujourd'hui (pb)", yaxis_title="VAN (M DH)")
    st.plotly_chart(mise_en_forme(fig, 400))

    comment_lire(
        "- Chaque barre est un **scénario de taux** : à gauche les taux baissent, à droite ils montent.\n"
        "- **Vert** : le projet reste rentable. **Rouge** : il ne l'est plus.\n"
        "- Rappel : 100 pb = 1 point de pourcentage (par exemple 2,17 % → 1,17 %)."
    )
    seuil_c = c.seuil_choc_taux({k_: v for k_, v in params.items() if k_ != "choc_pb"}, capex, taux_act / 100)
    if seuil_c is None:
        if ev["van"] < 0:
            a_retenir("Même avec des taux beaucoup plus élevés, le projet resterait non rentable : le problème "
                      "ne vient pas des taux mais d'un **encours trop faible** ou de **coûts trop élevés**.",
                      ton="danger")
        else:
            a_retenir("Le projet reste rentable même en cas de forte baisse des taux : il est **peu dépendant** "
                      "de la politique monétaire avec ces hypothèses.", ton="succes")
    elif seuil_c < 0:
        a_retenir(
            f"Il suffirait d'une **baisse des taux d'environ {abs(seuil_c):.0f} pb** pour que la VAN devienne "
            "négative. Le MADc est en réalité un **pari sur le niveau des taux** fixés par la politique "
            "monétaire de Bank Al-Maghrib. Pour réduire cette dépendance : diversifier les revenus "
            "(paiements marchands, volumes de transferts) ou réduire les coûts fixes.",
            ton="alerte",
        )
    else:
        a_retenir(
            f"Avec ces hypothèses, il faudrait une **hausse des taux d'environ {seuil_c:.0f} pb** pour que le "
            "projet devienne rentable : il n'est pas viable aux taux actuels.",
            ton="danger",
        )


# ===========================================================================
# 6. STRESS TEST
# ===========================================================================
with onglets[5]:
    st.header("🎲 Le MADc résisterait-il à une panique bancaire ?")
    st.markdown(
        "Une rumeur circule : beaucoup de clients veulent récupérer leurs dirhams **en même temps**. "
        "La banque paie d'abord avec son **cash**, puis revend ses **bons du Trésor**, mais seulement une "
        "quantité limitée par jour. Si elle ne peut plus payer à temps, c'est la **rupture de liquidité**. "
        "On simule des milliers de crises de 10 jours (encours de 12 milliards de DH)."
    )

    with st.container(border=True):
        st.markdown("**⚙️ Hypothèses**")
        s1, s2, s3 = st.columns(3)
        cash_st = s1.slider("Réserves gardées en cash (%)", 5, 50, 20, step=5, key="cash_stress")
        gravite = s2.select_slider("Gravité des crises", options=list(c.GRAVITES.keys()), value="Centrale",
                                   help="Modérée ≈ 7,7 % de retraits en moyenne ; Centrale ≈ 11,1 % ; Sévère ≈ 17,6 %.")
        n_sim = s3.select_slider("Nombre de crises simulées", options=[1_000, 5_000, 10_000, 20_000], value=10_000,
                                 format_func=nombre)
        s4, s5, s6 = st.columns(3)
        cap13 = s4.slider("BT 13 semaines revendables par jour (% de l'encours)", 1.0, 10.0, 3.0, step=0.5)
        cap52 = s5.slider("BT 52 semaines revendables par jour (% de l'encours)", 0.5, 5.0, 1.0, step=0.5)
        tolerance = s6.slider("Risque de rupture acceptable (%)", 0.1, 5.0, 1.0, step=0.1)

    b = c.GRAVITES[gravite]
    sim = simulation(cash_st / 100, b, cap13 / 100, cap52 / 100, n_sim)
    proba = sim["Rupture"].mean() * 100
    ruptures = sim.loc[sim["Rupture"], "Intensité (%)"]
    seuil_res = ruptures.min() if len(ruptures) else None

    k = st.columns(4)
    k[0].metric("Probabilité de rupture", pct(proba, 2),
                delta="sous le seuil acceptable" if proba <= tolerance else "au-dessus du seuil",
                delta_color="normal" if proba <= tolerance else "inverse")
    k[1].metric("Retraits moyens d'une crise", pct(sim["Intensité (%)"].mean()))
    k[2].metric("Seuil de résistance", f"≈ {pct(seuil_res, 0)} de retraits" if seuil_res else "Aucune rupture")
    k[3].metric("Pertes max. de vente forcée", mdh(sim["Pertes de vente forcée (M DH)"].max(), 2))

    sim_aff = sim.assign(**{"Rupture de liquidité": sim["Rupture"].map({True: "Oui", False: "Non"})})
    fig = px.histogram(sim_aff, x="Intensité (%)", color="Rupture de liquidité", nbins=60,
                       color_discrete_map={"Non": "#86EFAC", "Oui": ROUGE},
                       category_orders={"Rupture de liquidité": ["Non", "Oui"]})
    fig.add_vline(x=sim["Intensité (%)"].mean(), line_dash="dash", line_color="black",
                  annotation_text="Crise moyenne", annotation_position="top right")
    fig.update_layout(title=f"{nombre(n_sim)} crises simulées avec {cash_st} % de cash",
                      xaxis_title="Part de l'encours retirée pendant la crise (%)", yaxis_title="Nombre de crises")
    st.plotly_chart(mise_en_forme(fig, 420))

    comment_lire(
        "- Chaque barre compte **combien de crises** ont eu cette gravité (axe horizontal).\n"
        "- **Vert** : la banque a payé tout le monde. **Rouge** : rupture de liquidité.\n"
        "- La plupart des crises sont petites (à gauche) ; les crises extrêmes sont rares (à droite)."
    )
    if seuil_res:
        a_retenir(
            f"Avec {cash_st} % de cash, le MADc surmonte **{fr(100 - proba)} % des crises**. Les ruptures "
            f"n'apparaissent qu'au-delà d'environ **{seuil_res:.0f} % de l'encours retiré** en 10 jours. "
            f"Même dans le pire cas, les pertes restent limitées ({mdh(sim['Pertes de vente forcée (M DH)'].max(), 1)}) : "
            "le danger n'est pas de **manquer d'argent**, mais de **ne pas pouvoir le mobiliser assez vite**.",
            ton="succes" if proba <= tolerance else "alerte",
        )
    else:
        a_retenir(f"Avec {cash_st} % de cash, **aucune** des crises simulées ne provoque de rupture.", ton="succes")

    st.divider()
    st.subheader("⚖️ Quel est le bon niveau de cash ?")
    arb = arbitrage(b, cap13 / 100, cap52 / 100, n_sim)
    acceptables = arb[arb["Probabilité de rupture (%)"] <= tolerance]
    optimal = acceptables.loc[acceptables["Revenus des réserves an 5 (M DH)"].idxmax()] if len(acceptables) else None

    fig = go.Figure()
    fig.add_scatter(x=arb["Revenus des réserves an 5 (M DH)"], y=arb["Probabilité de rupture (%)"],
                    mode="lines+markers+text", text=[f"{p} % cash" for p in arb["Part de cash (%)"]],
                    textposition="top right", line=dict(color="#1D4ED8", width=2.5), name="Niveaux de cash")
    if optimal is not None:
        fig.add_scatter(x=[optimal["Revenus des réserves an 5 (M DH)"]], y=[optimal["Probabilité de rupture (%)"]],
                        mode="markers", marker=dict(size=18, color=VERT, symbol="star"), name="Choix optimal")
    fig.add_hline(y=tolerance, line_dash="dash", line_color=ROUGE,
                  annotation_text=f"Risque acceptable : {fr(tolerance)} %",
                  annotation_position="top left")
    fig.update_layout(title="Arbitrage sécurité / rentabilité",
                      xaxis_title="Revenus des réserves en année 5 (M DH)  →  plus rentable",
                      yaxis_title="Probabilité de rupture (%)  →  plus risqué")
    st.plotly_chart(mise_en_forme(fig, 440))

    comment_lire(
        "- **Vers la droite**, la banque gagne plus (elle place davantage). **Vers le haut**, c'est plus dangereux.\n"
        "- Chaque point est un niveau de cash. La **ligne rouge** est le risque maximal accepté.\n"
        "- Le **bon choix** est le point **le plus à droite qui reste sous la ligne rouge** (l'étoile verte)."
    )
    if optimal is not None:
        a_retenir(
            f"Avec un risque acceptable de {fr(tolerance)} %, le niveau de cash optimal est de "
            f"**{int(optimal['Part de cash (%)'])} %** : c'est l'allocation la plus rentable "
            f"({mdh(optimal['Revenus des réserves an 5 (M DH)'])} de revenus en année 5) qui respecte la contrainte. "
            "Au-delà, chaque tranche de cash supplémentaire coûte environ 13,5 M DH par an pour un gain de "
            "sécurité de plus en plus faible : ce sont les **rendements décroissants**.",
            ton="succes",
        )
    else:
        a_retenir("Aucun niveau de cash testé ne respecte le risque acceptable choisi : il faudrait plus de "
                  "50 % de cash, ou un accès à la liquidité de Bank Al-Maghrib.", ton="danger")

    with st.expander("📋 Voir le tableau complet"):
        st.dataframe(arb.round(2), hide_index=True)


# ===========================================================================
# 7. MÉTHODOLOGIE
# ===========================================================================
with onglets[6]:
    st.header("📚 Méthodologie, hypothèses et limites")

    st.markdown(
        """
        #### Données
        - **Prix des stablecoins** (USDT, USDC, DAI) : Yahoo Finance, données journalières depuis janvier 2020
          (prix de clôture et plus bas de la journée).
        - **Transferts des MRE** : Office des changes (plus de 122 milliards de DH en 2025).
        - **Coût des transferts** : Banque mondiale, *Remittance Prices Worldwide*, T3 2025 (envoi de 140 € au départ de la France).
        - **Taux** : bons du Trésor à 13 semaines (2,170 %) et 52 semaines (2,363 %), adjudication du 20 octobre 2026 ;
          taux directeur de Bank Al-Maghrib à 2,25 %.
        - **Fiscalité** : impôt sur les sociétés de 40 % pour les établissements de crédit (2026).

        #### Méthodes
        | Partie | Méthode |
        |---|---|
        | Stabilité du peg | Écart au peg en points de base, fréquence des dépassements de seuil |
        | Risque de marché | VaR historique et Expected Shortfall sur rendements journaliers |
        | Crises | Profondeur (clôture et intrajournalier), durée, temps de récupération |
        | Transferts MRE | Comparaison des coûts par canal, scénarios d'adoption |
        | Business plan | Compte de résultat sur 5 ans, VAN, TRI, sensibilité aux taux |
        | Stress test | Simulation de Monte Carlo (loi Bêta), mobilisation séquentielle des réserves |

        #### Principales limites
        - Le **coût du stablecoin** pour les transferts est une hypothèse : le circuit n'est pas encore encadré au Maroc.
        - Le coût moyen retenu (5,23 %) concerne le **corridor France–Maroc** ; une partie des transferts transite
          par des canaux informels.
        - Le business plan ne tient pas compte du **report des déficits** et ne retient **aucune valeur terminale**
          (approche prudente).
        - La probabilité de rupture est **conditionnelle** à la survenance d'une crise ; elle dépend des hypothèses
          sur la gravité des crises et la profondeur du marché des bons du Trésor.
        """
    )
    st.caption("Projet réalisé par Ahmed Badi — Ingénieur financier, EMSI Rabat. Code : Python, pandas, Plotly, Streamlit.")
