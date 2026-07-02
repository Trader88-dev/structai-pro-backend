"""
Module de calcul — Dalle pleine bidirectionnelle
Méthodes : Marcus (coefficients) + EC2 / BAEL 91
Vérifications : ELU flexion, ELS flèche, ELS fissuration
"""

from dataclasses import dataclass, field
from typing import List
import math


# ── Choix de barres ──────────────────────────────────────────────────────────
CHOIX_BARRES = [
    (6,  28.3), (8,  50.3), (10, 78.5), (12, 113.1),
    (14, 153.9), (16, 201.1), (20, 314.2), (25, 490.9), (32, 804.2),
]

def _choisir_armatures(As_mm2_ml: float) -> tuple:
    for diam, aire_1 in CHOIX_BARRES:
        for esp in [80, 100, 120, 150, 160, 200, 250]:
            nb = 1000 / esp
            as_fourni = nb * aire_1
            if as_fourni >= As_mm2_ml:
                return round(as_fourni, 1), f"HA{diam} esp. {esp} mm ({as_fourni:.0f} mm²/ml)"
    return round(1000/80*804.2, 1), f"HA32 esp. 80 mm"


# ── Coefficients Marcus (dalle appuyée sur 4 côtés) ─────────────────────────
def _coefficients_marcus(rho: float, appuis: dict) -> tuple:
    """
    rho = Lx/Ly (≤1, Lx = petit côté)
    appuis = dict avec clés 'x1','x2','y1','y2' valeurs 'libre','appuye','encastre'
    Retourne (mu_x, mu_y) coefficients moments travée
    """
    # Table Marcus simplifiée pour dalle appuyée sur 4 côtés
    # Interpolation linéaire entre valeurs tabulées
    table = {
        # rho : (mu_x_trav, mu_y_trav, mu_x_app, mu_y_app)
        0.40: (0.0965, 0.0174, 0.1286, 0.0232),
        0.45: (0.0892, 0.0210, 0.1189, 0.0280),
        0.50: (0.0820, 0.0245, 0.1093, 0.0327),
        0.55: (0.0750, 0.0280, 0.1000, 0.0374),
        0.60: (0.0680, 0.0314, 0.0906, 0.0418),
        0.65: (0.0615, 0.0348, 0.0820, 0.0464),
        0.70: (0.0549, 0.0381, 0.0732, 0.0508),
        0.75: (0.0490, 0.0413, 0.0653, 0.0550),
        0.80: (0.0430, 0.0444, 0.0573, 0.0592),
        0.85: (0.0376, 0.0474, 0.0502, 0.0632),
        0.90: (0.0324, 0.0502, 0.0432, 0.0670),
        0.95: (0.0275, 0.0528, 0.0367, 0.0704),
        1.00: (0.0228, 0.0554, 0.0303, 0.0739),
    }

    rho_c = max(0.40, min(1.00, rho))
    keys = sorted(table.keys())

    # Interpolation
    if rho_c in table:
        vals = table[rho_c]
    else:
        k_low = max(k for k in keys if k <= rho_c)
        k_high = min(k for k in keys if k >= rho_c)
        if k_low == k_high:
            vals = table[k_low]
        else:
            t = (rho_c - k_low) / (k_high - k_low)
            v_low = table[k_low]
            v_high = table[k_high]
            vals = tuple(v_low[i] + t * (v_high[i] - v_low[i]) for i in range(4))

    mu_x_trav, mu_y_trav, mu_x_app, mu_y_app = vals

    # Correction selon conditions d'appui
    # Encastrement → réduction moment travée de 20%
    nb_encastres = sum(1 for v in appuis.values() if v == "encastre")
    facteur = 1.0 - 0.05 * nb_encastres  # -5% par encastrement
    mu_x_trav *= facteur
    mu_y_trav *= facteur

    # Côté libre → augmentation moment travée 30%
    nb_libres = sum(1 for v in appuis.values() if v == "libre")
    if nb_libres > 0:
        mu_x_trav *= (1.0 + 0.15 * nb_libres)
        mu_y_trav *= (1.0 + 0.15 * nb_libres)

    return mu_x_trav, mu_y_trav, mu_x_app, mu_y_app


# ── Dataclasses ───────────────────────────────────────────────────────────────
@dataclass
class EntreeDalle:
    # Géométrie
    Lx: float          # petit côté (m)
    Ly: float          # grand côté (m)
    epaisseur: float   # épaisseur (mm)

    # Conditions d'appui (libre / appuye / encastre)
    appui_x1: str = "appuye"   # rive x=0
    appui_x2: str = "appuye"   # rive x=Lx
    appui_y1: str = "appuye"   # rive y=0
    appui_y2: str = "appuye"   # rive y=Ly

    # Chargement
    g_k: float = 5.0    # charge permanente kN/m²
    q_k: float = 2.5    # charge variable kN/m²

    # Matériaux
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

    # ELS
    classe_fissuration: str = "XC1"  # XC1→wk=0.4, XC2/XC3→wk=0.3, XC4→wk=0.2


@dataclass
class ResultatDalle:
    norme: str = "EC2"

    # Géométrie
    rho: float = 0.0          # Lx/Ly
    d_x: float = 0.0          # hauteur utile x (mm)
    d_y: float = 0.0          # hauteur utile y (mm)
    bidirectionnelle: bool = True

    # ELU
    q_ELU: float = 0.0        # charge ELU (kN/m²)
    q_ELS: float = 0.0        # charge ELS (kN/m²)

    # Moments ELU travée
    Mx_trav: float = 0.0      # kN.m/ml
    My_trav: float = 0.0
    # Moments ELU appui
    Mx_app: float = 0.0
    My_app: float = 0.0

    # Armatures inférieures (travée)
    As_x_inf_calc: float = 0.0
    As_x_inf_min: float = 0.0
    As_x_inf_retenu: float = 0.0
    choix_x_inf: str = ""

    As_y_inf_calc: float = 0.0
    As_y_inf_min: float = 0.0
    As_y_inf_retenu: float = 0.0
    choix_y_inf: str = ""

    # Armatures supérieures (appui)
    As_x_sup_calc: float = 0.0
    As_x_sup_retenu: float = 0.0
    choix_x_sup: str = ""

    As_y_sup_calc: float = 0.0
    As_y_sup_retenu: float = 0.0
    choix_y_sup: str = ""

    # ELS — Flèche
    fleche_admissible: float = 0.0   # mm
    fleche_calculee: float = 0.0     # mm
    fleche_ok: bool = True

    # ELS — Fissuration
    wk_x: float = 0.0     # mm
    wk_y: float = 0.0     # mm
    wk_lim: float = 0.3   # mm
    fissuration_ok: bool = True

    # ELS — Contraintes
    sigma_c: float = 0.0   # MPa béton
    sigma_s: float = 0.0   # MPa acier

    messages: List[str] = field(default_factory=list)


# ── Fonction principale ───────────────────────────────────────────────────────
def calculer_dalle(e: EntreeDalle) -> ResultatDalle:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatDalle(norme=e.norme)
    msgs = r.messages

    # ── Matériaux ─────────────────────────────────────────────────────────────
    bet  = BETONS[e.beton]
    acr  = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)

    fck  = bet.fck
    fcd  = fck / 1.5
    fyk  = acr.fyk
    fyd  = fyk / 1.15
    E_s  = 200000  # MPa
    E_cm = 22000 * ((fck + 8) / 10) ** 0.3  # MPa

    # ── Géométrie ─────────────────────────────────────────────────────────────
    # Assurer Lx ≤ Ly
    Lx = min(e.Lx, e.Ly)
    Ly = max(e.Lx, e.Ly)
    ep  = e.epaisseur  # mm
    rho = Lx / Ly
    r.rho = round(rho, 3)
    r.bidirectionnelle = rho >= 0.4

    # Hauteurs utiles
    phi_sup = 10  # diamètre supposé
    d_x = ep - c_nom - phi_sup / 2
    d_y = ep - c_nom - phi_sup - phi_sup / 2
    d_x = max(d_x, 80)
    d_y = max(d_y, 60)
    r.d_x = round(d_x, 0)
    r.d_y = round(d_y, 0)

    # ── Vérification épaisseur minimale (EC2 §7.4) ───────────────────────────
    ep_min_x = Lx * 1000 / 35   # mm  (L/35 pour dalles courantes)
    ep_min_y = Ly * 1000 / 35
    if ep < ep_min_x:
        msgs.append(f"⚠️ Épaisseur insuffisante pour vérif. flèche forfaitaire : e={ep}mm < L/35={ep_min_x:.0f}mm")

    # ── ELU / ELS ─────────────────────────────────────────────────────────────
    gamma_G, gamma_Q = 1.35, 1.50
    q_ELU = gamma_G * e.g_k + gamma_Q * e.q_k
    q_ELS = e.g_k + e.q_k
    r.q_ELU = round(q_ELU, 2)
    r.q_ELS = round(q_ELS, 2)

    # ── Moments ELU — Marcus ──────────────────────────────────────────────────
    appuis = {
        "x1": e.appui_x1, "x2": e.appui_x2,
        "y1": e.appui_y1, "y2": e.appui_y2,
    }

    if r.bidirectionnelle:
        mu_x_t, mu_y_t, mu_x_a, mu_y_a = _coefficients_marcus(rho, appuis)
        Mx_trav = mu_x_t * q_ELU * Lx**2
        My_trav = mu_y_t * q_ELU * Lx**2
        Mx_app  = mu_x_a * q_ELU * Lx**2
        My_app  = mu_y_a * q_ELU * Lx**2
        msgs.append(f"Dalle bidirectionnelle (ρ={rho:.2f} ≥ 0.4) — Méthode Marcus")
    else:
        # Dalle unidirectionnelle selon Lx
        Mx_trav = q_ELU * Lx**2 / 8
        My_trav = 0.2 * Mx_trav   # armatures de répartition
        Mx_app  = q_ELU * Lx**2 / 16
        My_app  = 0.2 * Mx_app
        msgs.append(f"Dalle unidirectionnelle (ρ={rho:.2f} < 0.4) — travée selon Lx={Lx}m")

    r.Mx_trav = round(Mx_trav, 2)
    r.My_trav = round(My_trav, 2)
    r.Mx_app  = round(Mx_app,  2)
    r.My_app  = round(My_app,  2)

    # ── Calcul armatures ──────────────────────────────────────────────────────
    def _as_flexion(Med_kNm: float, d_mm: float) -> float:
        d_m = d_mm / 1000
        mu  = Med_kNm / (1.0 * d_m**2 * fcd * 1000)
        mu  = min(mu, 0.372)
        alpha = (1 - math.sqrt(max(0, 1 - 2*mu)))
        z   = d_m * (1 - 0.4*alpha)
        As  = Med_kNm / (z * fyd / 1000) if z > 0 else 0
        return max(As, 0.0)

    # Armature minimale EC2 §9.3.1
    rho_min = max(0.26 * 0.30 * fck**(2/3) / fyk, 0.0013)
    As_min  = rho_min * 1000 * d_x   # mm²/ml

    # Nappe inférieure x
    as_xi = _as_flexion(Mx_trav, d_x)
    r.As_x_inf_calc = round(as_xi, 0)
    r.As_x_inf_min  = round(As_min, 0)
    ret, ch = _choisir_armatures(max(as_xi, As_min))
    r.As_x_inf_retenu, r.choix_x_inf = ret, ch

    # Nappe inférieure y
    as_yi = _as_flexion(My_trav, d_y)
    r.As_y_inf_calc = round(as_yi, 0)
    r.As_y_inf_min  = round(As_min * 0.2 if not r.bidirectionnelle else As_min, 0)
    ret, ch = _choisir_armatures(max(as_yi, r.As_y_inf_min))
    r.As_y_inf_retenu, r.choix_y_inf = ret, ch

    # Nappe supérieure x (appuis encastrés)
    as_xs = _as_flexion(Mx_app, d_x)
    ret, ch = _choisir_armatures(max(as_xs, As_min * 0.5))
    r.As_x_sup_calc, r.As_x_sup_retenu, r.choix_x_sup = round(as_xs, 0), ret, ch

    # Nappe supérieure y
    as_ys = _as_flexion(My_app, d_y)
    ret, ch = _choisir_armatures(max(as_ys, As_min * 0.5))
    r.As_y_sup_calc, r.As_y_sup_retenu, r.choix_y_sup = round(as_ys, 0), ret, ch

    # ── ELS — Flèche (méthode forfaitaire EC2 §7.4.2) ────────────────────────
    # Rapport L/d minimum selon EC2 Tableau 7.4N
    rho_s = r.As_x_inf_retenu / (1000 * d_x)   # taux d'armature
    rho_0 = math.sqrt(fck) / 1000               # taux de référence

    if rho_s <= rho_0:
        kappa = 11 + 1.5 * math.sqrt(fck) * rho_0 / rho_s + 3.2 * math.sqrt(fck) * (rho_0/rho_s - 1)**1.5
    else:
        kappa = 11 + 1.5 * math.sqrt(fck) * rho_0 / (rho_s - rho_0) + math.sqrt(fck/rho_s) / 12

    # Facteur dalle (vs poutre) = 1.0 ; facteur portée > 7m
    if Lx > 7.0:
        kappa *= 7.0 / Lx

    l_d_min = kappa
    l_d_reel = Lx * 1000 / d_x

    fleche_adm = Lx * 1000 / 250   # mm

    # Flèche approchée (charge répartie, assimilation à une bande de dalle en flexion)
    # NOTE : coefficient 5/48 (appuis simples 4 côtés) ou 1/16 (autres cas) — approximation
    # empruntée à la théorie des poutres. Une dalle bidirectionnelle relève en toute rigueur
    # de la théorie des plaques (coefficients dépendant de Ly/Lx, cf. tables de Timoshenko),
    # à affiner si une précision réglementaire stricte est requise.
    coeff_k = 5/48 if all(v == "appuye" for v in appuis.values()) else 1/16
    fleche_calc = coeff_k * q_ELS * (Lx*1000)**4 / (E_cm * (1000*ep**3/12))

    r.fleche_admissible = round(fleche_adm, 1)
    r.fleche_calculee   = round(fleche_calc, 1)
    r.fleche_ok         = (l_d_reel <= l_d_min * 1.3)  # tolérance 30%

    if not r.fleche_ok:
        msgs.append(f"⚠️ Vérif. flèche forfaitaire : L/d={l_d_reel:.0f} > {l_d_min:.0f} — augmenter épaisseur ou armatures")
    else:
        msgs.append(f"✅ Flèche vérifiée (L/d={l_d_reel:.0f} ≤ {l_d_min:.0f})")

    # ── ELS — Fissuration (EC2 §7.3) ─────────────────────────────────────────
    wk_lim = {"XC1": 0.4, "XC2": 0.3, "XC3": 0.3, "XC4": 0.2}.get(e.classe_fissuration, 0.3)
    r.wk_lim = wk_lim

    # Moment ELS travée
    Mx_ELS = (e.g_k + e.q_k) / q_ELU * Mx_trav if q_ELU > 0 else 0
    My_ELS = (e.g_k + e.q_k) / q_ELU * My_trav if q_ELU > 0 else 0

    def _wk(Med_ELS_kNm: float, As_mm2: float, d_mm: float, phi_mm: float = 10) -> float:
        if As_mm2 <= 0:
            return 0.0
        d_m  = d_mm / 1000
        As_m = As_mm2 / 1e6
        # Contrainte acier ELS
        z_els = 0.9 * d_m
        sigma_s = Med_ELS_kNm / (As_m * z_els * 1000) if As_m > 0 else 0
        # Espacement fissures sr_max (EC2 §7.3.4)
        c = c_nom / 1000
        rho_eff = As_mm2 / (1000 * min(2.5*(ep/1000 - d_m), (ep/1000)/2) * 1000)
        rho_eff = max(rho_eff, 0.0001)
        sr_max = 3.4 * c + 0.425 * 0.8 * 1.0 * (phi_mm/1000) / rho_eff
        # Ouverture fissure
        eps_sm = max(sigma_s / E_s - 0.4 * bet.fctm / (E_s * rho_eff), 0.6 * sigma_s / E_s)
        wk = sr_max * eps_sm * 1000  # mm
        return round(wk, 3)

    r.wk_x = _wk(Mx_ELS, r.As_x_inf_retenu, d_x)
    r.wk_y = _wk(My_ELS, r.As_y_inf_retenu, d_y)
    r.fissuration_ok = (r.wk_x <= wk_lim) and (r.wk_y <= wk_lim)

    if not r.fissuration_ok:
        msgs.append(f"⚠️ Fissuration : wk_x={r.wk_x}mm ou wk_y={r.wk_y}mm > wk,lim={wk_lim}mm — augmenter armatures")
    else:
        msgs.append(f"✅ Fissuration vérifiée : wk_x={r.wk_x}mm, wk_y={r.wk_y}mm ≤ {wk_lim}mm")

    # ── Contraintes ELS ───────────────────────────────────────────────────────
    Mx_ELS_sc = Mx_ELS
    n = E_s / E_cm
    d_m = d_x / 1000
    As_m = r.As_x_inf_retenu / 1e6
    # Position axe neutre
    x_n = (-As_m * n + math.sqrt((As_m * n)**2 + 2 * 1.0 * d_m * As_m * n)) / 1.0
    I_fiss = 1.0 * x_n**3 / 3 + n * As_m * (d_m - x_n)**2
    sigma_c = Mx_ELS_sc * x_n / I_fiss / 1000 if I_fiss > 0 else 0
    sigma_s_els = n * Mx_ELS_sc * (d_m - x_n) / I_fiss / 1000 if I_fiss > 0 else 0
    r.sigma_c = round(sigma_c, 1)
    r.sigma_s = round(sigma_s_els, 1)

    sig_c_lim = 0.6 * fck
    sig_s_lim = 0.8 * fyk
    if sigma_c > sig_c_lim:
        msgs.append(f"⚠️ Contrainte béton ELS : σc={sigma_c:.1f} MPa > 0.6fck={sig_c_lim:.1f} MPa")
    if sigma_s_els > sig_s_lim:
        msgs.append(f"⚠️ Contrainte acier ELS : σs={sigma_s_els:.1f} MPa > 0.8fyk={sig_s_lim:.1f} MPa")

    msgs.append(f"Armature minimale : {round(As_min, 0)} mm²/ml")

    return r
