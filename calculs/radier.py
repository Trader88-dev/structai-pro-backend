"""
Module de calcul — Radier général (dalle pleine sur sol élastique)
Méthodes : pression trapézoïdale (ELS) + modèle de Winkler simplifié (ELU)
Normes : EC2 / BAEL 91
"""

from dataclasses import dataclass, field
from typing import List
import math


# ── Données matériaux (importées via app, redéfinies ici pour autonomie) ────
CHOIX_BARRES = [
    (6,  28.3), (8,  50.3), (10, 78.5), (12, 113.1),
    (14, 153.9), (16, 201.1), (20, 314.2), (25, 490.9),
    (32, 804.2),
]


def _choisir_armatures(As_cm2_ml: float, label: str = "") -> tuple[float, str]:
    """Retourne (As_retenu mm²/ml, texte choix) pour un besoin donné."""
    As_mm2 = As_cm2_ml  # déjà en mm²/ml
    for diam, aire_1 in CHOIX_BARRES:
        # espacement entre 80 et 200 mm
        for esp in [80, 100, 120, 150, 160, 200]:
            nb = 1000 / esp
            as_fourni = nb * aire_1
            if as_fourni >= As_mm2:
                return round(as_fourni, 1), f"HA{diam} esp. {esp} mm ({as_fourni:.0f} mm²/ml)"
    # fallback barres HA32 à 80 mm
    nb = 1000 / 80
    as_fourni = nb * 804.2
    return round(as_fourni, 1), f"HA32 esp. 80 mm ({as_fourni:.0f} mm²/ml)"


# ── Dataclasses entrée / sortie ──────────────────────────────────────────────

@dataclass
class EntreeRadier:
    # Géométrie
    Lx: float           # longueur (m)
    Ly: float           # largeur  (m)
    epaisseur: float    # épaisseur (mm)
    debord: float       # débord périphérique (mm)

    # Chargement
    N_k: float          # charge totale caractéristique (kN)
    M_kx: float         # moment selon x (kN.m)
    M_ky: float         # moment selon y (kN.m)
    pct_G: float        # fraction permanente (0-1)

    # Sol
    sigma_sol: float    # contrainte admissible ELS (kPa)
    ks: float           # module de réaction Winkler (kN/m³)

    # Matériaux
    beton: str
    acier: str
    enrobage_classe: str = "XC1"
    norme: str = "EC2"


@dataclass
class ResultatRadier:
    # Géométrie retenue
    Lx_retenu: float = 0.0
    Ly_retenu: float = 0.0
    surface: float = 0.0
    lx_ly_ok: bool = True

    # Efforts
    poids_propre: float = 0.0
    NEd: float = 0.0
    ex: float = 0.0
    ey: float = 0.0

    # Pression sol ELS
    sigma_moy: float = 0.0
    sigma_max: float = 0.0
    sigma_min: float = 0.0
    sigma_ok: bool = True

    # Longueurs élastiques
    l_elastique_x: float = 0.0
    l_elastique_y: float = 0.0

    # Moments ELU (travée + appui)
    MEd_x_trav: float = 0.0
    MEd_y_trav: float = 0.0
    MEd_x_app: float = 0.0
    MEd_y_app: float = 0.0

    # Armatures nappe inférieure x
    As_x_inf_calc: float = 0.0
    As_x_inf_min: float = 0.0
    As_x_inf_retenu: float = 0.0
    choix_x_inf: str = ""

    # Armatures nappe inférieure y
    As_y_inf_calc: float = 0.0
    As_y_inf_min: float = 0.0
    As_y_inf_retenu: float = 0.0
    choix_y_inf: str = ""

    # Armatures nappe supérieure x
    As_x_sup_calc: float = 0.0
    As_x_sup_retenu: float = 0.0
    choix_x_sup: str = ""

    # Armatures nappe supérieure y
    As_y_sup_calc: float = 0.0
    As_y_sup_retenu: float = 0.0
    choix_y_sup: str = ""

    messages: List[str] = field(default_factory=list)


# ── Fonction principale ──────────────────────────────────────────────────────

def calculer_radier(e: EntreeRadier) -> ResultatRadier:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatRadier()
    msgs = r.messages

    # ── Matériaux ────────────────────────────────────────────────────────────
    bet  = BETONS[e.beton]
    acr  = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 30)

    fck  = bet.fck
    fcd  = fck / 1.5 if e.norme == "EC2" else fck / 1.5
    fyk  = acr.fyk
    fyd  = fyk / 1.15

    # ── Géométrie ────────────────────────────────────────────────────────────
    ep_m = e.epaisseur / 1000          # m
    deb_m = e.debord / 1000            # m
    Lx = round(e.Lx + 2 * deb_m, 2)
    Ly = round(e.Ly + 2 * deb_m, 2)
    r.Lx_retenu = Lx
    r.Ly_retenu = Ly
    r.surface   = round(Lx * Ly, 2)
    r.lx_ly_ok  = (Lx / Ly) <= 2.0

    if not r.lx_ly_ok:
        msgs.append("⚠️ Rapport Lx/Ly > 2 : comportement unidirectionnel — vérifier hypothèse dalle.")

    # Hauteur utile (enrobage + ∅ supposé 16)
    d_x = e.epaisseur - c_nom - 8        # mm  (nappe x, barre du bas)
    d_y = e.epaisseur - c_nom - 8 - 16   # mm  (nappe y, au-dessus de x)
    d_x = max(d_x, 100)
    d_y = max(d_y, 100)

    # ── ELU / ELS coefficients ────────────────────────────────────────────────
    gamma_G = 1.35 if e.norme == "EC2" else 1.35
    gamma_Q = 1.50 if e.norme == "EC2" else 1.50
    pct_Q   = 1 - e.pct_G

    N_G = e.N_k * e.pct_G
    N_Q = e.N_k * pct_Q
    N_ELU = gamma_G * N_G + gamma_Q * N_Q
    N_ELS = e.N_k                         # ELS caractéristique

    # ── Poids propre radier ───────────────────────────────────────────────────
    gamma_b = 25.0  # kN/m³
    poids = round(r.surface * ep_m * gamma_b, 1)
    r.poids_propre = poids
    N_ELS_tot = N_ELS + poids
    N_ELU_tot = N_ELU + gamma_G * poids
    r.NEd = round(N_ELU_tot, 1)

    # ── Excentricités ─────────────────────────────────────────────────────────
    r.ex = round(e.M_kx / N_ELS_tot, 3) if N_ELS_tot > 0 else 0.0
    r.ey = round(e.M_ky / N_ELS_tot, 3) if N_ELS_tot > 0 else 0.0

    Wx = Lx * Ly**2 / 6
    Wy = Ly * Lx**2 / 6

    sigma_moy = N_ELS_tot / r.surface
    sigma_max = sigma_moy + e.M_kx / Wx + e.M_ky / Wy
    sigma_min = sigma_moy - e.M_kx / Wx - e.M_ky / Wy

    r.sigma_moy = round(sigma_moy, 1)
    r.sigma_max = round(sigma_max, 1)
    r.sigma_min = round(sigma_min, 1)
    r.sigma_ok  = sigma_max <= e.sigma_sol

    if not r.sigma_ok:
        msgs.append(f"ERREUR : σmax={r.sigma_max} kPa > σadm={e.sigma_sol} kPa — augmenter les dimensions du radier.")
    else:
        msgs.append(f"✅ Pression sol vérifiée : σmax={r.sigma_max} kPa ≤ σadm={e.sigma_sol} kPa")

    if sigma_min < 0:
        msgs.append(f"⚠️ σmin={r.sigma_min} kPa < 0 : décollement partiel — vérifier stabilité au renversement.")

    # ── Longueurs élastiques (méthode Winkler) ────────────────────────────────
    E_cm = 22000 * ((fck + 8) / 10) ** 0.3   # MPa
    E_cm_kN = E_cm * 1000                      # kN/m²
    I_x = 1.0 * ep_m**3 / 12                   # m⁴/ml
    I_y = I_x

    # l_e = (4EI/ks)^0.25  en m
    le_x = (4 * E_cm_kN * I_x / e.ks) ** 0.25
    le_y = (4 * E_cm_kN * I_y / e.ks) ** 0.25
    r.l_elastique_x = round(le_x, 2)
    r.l_elastique_y = round(le_y, 2)

    msgs.append(f"Longueur élastique x : {r.l_elastique_x} m | y : {r.l_elastique_y} m")

    # ── Moments ELU (méthode forfaitaire dalle appuyée sur sol) ──────────────
    # Pression ELU moyenne sous radier
    q_ELU = N_ELU_tot / r.surface   # kN/m²

    # Moments travée et appui selon les coefficients des dalles continues
    # Approche simplifiée : méthode des coefficients forfaitaires
    # Travée : M = q * l² / 12  (encastrement partiel sur sol)
    # Appui  : M = q * l² / 24  (moment négatif en zone de poteau)
    MEd_x_trav = q_ELU * Lx**2 / 12
    MEd_y_trav = q_ELU * Ly**2 / 12
    MEd_x_app  = q_ELU * Lx**2 / 24
    MEd_y_app  = q_ELU * Ly**2 / 24

    r.MEd_x_trav = round(MEd_x_trav, 2)
    r.MEd_y_trav = round(MEd_y_trav, 2)
    r.MEd_x_app  = round(MEd_x_app,  2)
    r.MEd_y_app  = round(MEd_y_app,  2)

    # ── Calcul armatures ─────────────────────────────────────────────────────
    def _calc_as(Med_kNm: float, d_mm: float) -> float:
        """Armature (mm²/ml) pour moment Med en kN.m/ml, hauteur utile d en mm."""
        d_m = d_mm / 1000
        b   = 1.0   # 1 ml
        mu  = Med_kNm / (b * d_m**2 * fcd * 1000)
        mu  = min(mu, 0.372)   # pivot A limite
        alpha = (1 - math.sqrt(1 - 2 * mu))
        z   = d_m * (1 - 0.4 * alpha)
        As  = Med_kNm / (z * fyd / 1000)  # mm²/ml
        return max(As, 0.0)

    # Armature minimale EC2 / BAEL
    rho_min = max(0.26 * (0.30 * fck**(2/3)) / fyk, 0.0013)
    As_min  = rho_min * 1000 * d_x   # mm²/ml  (section brute 1m × d)

    # Nappe inférieure x (travée)
    as_xi = _calc_as(r.MEd_x_trav, d_x)
    r.As_x_inf_calc = round(as_xi, 0)
    r.As_x_inf_min  = round(As_min, 0)
    as_xi_ret, ch_xi = _choisir_armatures(max(as_xi, As_min))
    r.As_x_inf_retenu = as_xi_ret
    r.choix_x_inf     = ch_xi

    # Nappe inférieure y (travée)
    as_yi = _calc_as(r.MEd_y_trav, d_y)
    r.As_y_inf_calc = round(as_yi, 0)
    r.As_y_inf_min  = round(As_min, 0)
    as_yi_ret, ch_yi = _choisir_armatures(max(as_yi, As_min))
    r.As_y_inf_retenu = as_yi_ret
    r.choix_y_inf     = ch_yi

    # Nappe supérieure x (appui / hogging)
    as_xs = _calc_as(r.MEd_x_app, d_x)
    r.As_x_sup_calc = round(as_xs, 0)
    as_xs_ret, ch_xs = _choisir_armatures(max(as_xs, As_min))
    r.As_x_sup_retenu = as_xs_ret
    r.choix_x_sup     = ch_xs

    # Nappe supérieure y
    as_ys = _calc_as(r.MEd_y_app, d_y)
    r.As_y_sup_calc = round(as_ys, 0)
    as_ys_ret, ch_ys = _choisir_armatures(max(as_ys, As_min))
    r.As_y_sup_retenu = as_ys_ret
    r.choix_y_sup     = ch_ys

    msgs.append(f"Armature minimale retenue : {round(As_min, 0)} mm²/ml")
    msgs.append("Calcul basé sur méthode forfaitaire simplifiée (Winkler) — à affiner par EF si nécessaire.")

    return r
