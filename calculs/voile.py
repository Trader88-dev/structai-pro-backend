"""
Module de calcul — Voile BA
Compression + flexion composée — EC2 / BAEL 91
Vérifications : ELU flambement, armatures verticales + horizontales + about
"""

from dataclasses import dataclass, field
from typing import List
import math


CHOIX_BARRES = [
    (6, 28.3), (8, 50.3), (10, 78.5), (12, 113.1),
    (14, 153.9), (16, 201.1), (20, 314.2), (25, 490.9), (32, 804.2),
]

def _choisir_armatures_ml(As_mm2_ml: float) -> tuple:
    for diam, aire_1 in CHOIX_BARRES:
        for esp in [100, 120, 150, 160, 200, 250, 300]:
            nb = 1000 / esp
            as_fourni = nb * aire_1
            if as_fourni >= As_mm2_ml:
                return round(as_fourni, 1), f"HA{diam} esp. {esp} mm ({as_fourni:.0f} mm²/ml)"
    return round(1000/100*804.2, 1), f"HA32 esp. 100 mm"


@dataclass
class EntreeVoile:
    # Géométrie
    L: float          # longueur du voile (m)
    h: float          # hauteur du voile (m) — hauteur d'étage
    e: float          # épaisseur (mm)

    # Conditions aux appuis
    appui: str = "encastre-rotule"   # encastre-rotule / rotule-rotule / encastre-encastre

    # Chargement
    N_k: float = 500.0    # effort normal caractéristique (kN)
    M_k: float = 50.0     # moment fléchissant caractéristique (kN.m)
    V_k: float = 20.0     # effort tranchant caractéristique (kN)
    pct_G: float = 0.7    # fraction permanente

    # Matériaux
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"


@dataclass
class ResultatVoile:
    norme: str = "EC2"

    # Géométrie
    d: float = 0.0          # hauteur utile (mm)
    l0: float = 0.0         # longueur de flambement (m)
    lambda_: float = 0.0    # élancement
    lambda_lim: float = 0.0
    elance: bool = False

    # Efforts ELU
    NEd: float = 0.0
    MEd: float = 0.0
    VEd: float = 0.0
    e0: float = 0.0         # excentricité 1er ordre (mm)
    e2: float = 0.0         # excentricité 2nd ordre (mm)
    etot: float = 0.0       # excentricité totale (mm)
    MEd_tot: float = 0.0    # moment total (kN.m)

    # Armatures verticales (2 nappes)
    As_vert_calc: float = 0.0
    As_vert_min: float = 0.0
    As_vert_max: float = 0.0
    As_vert_retenu: float = 0.0
    choix_vert: str = ""

    # Armatures horizontales
    As_horiz_min: float = 0.0
    As_horiz_retenu: float = 0.0
    choix_horiz: str = ""

    # Armatures d'about (about de voile)
    As_about_calc: float = 0.0
    As_about_retenu: float = 0.0
    choix_about: str = ""

    # Cisaillement
    tau_u: float = 0.0
    VRd_c: float = 0.0
    cisaillement_ok: bool = True

    messages: List[str] = field(default_factory=list)


def calculer_voile(e: EntreeVoile) -> ResultatVoile:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatVoile(norme=e.norme)
    msgs = r.messages

    # ── Matériaux ─────────────────────────────────────────────────────────────
    bet  = BETONS[e.beton]
    acr  = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)

    fck = bet.fck
    fcd = fck / 1.5
    fyk = acr.fyk
    fyd = fyk / 1.15
    E_s = 200000.0
    E_cm = 22000 * ((fck + 8) / 10) ** 0.3

    # ── Géométrie ─────────────────────────────────────────────────────────────
    ep = e.e          # mm
    d  = ep - c_nom - 8
    d  = max(d, ep * 0.8)
    r.d = round(d, 0)

    # Longueur de flambement
    coeffs = {"encastre-rotule": 0.7, "rotule-rotule": 1.0, "encastre-encastre": 0.5}
    coeff_l0 = coeffs.get(e.appui, 0.7)
    l0 = coeff_l0 * e.h          # m
    r.l0 = round(l0, 2)

    # Élancement selon l'épaisseur
    lambda_ = l0 * 1000 / (ep / math.sqrt(12))
    r.lambda_ = round(lambda_, 1)

    # Limite élancement EC2 §5.8.3
    n = (e.N_k * 1.35) / (e.L * 1000 * ep * fcd / 1000)
    n = min(max(n, 0.01), 1.0)
    lambda_lim = 20 * 0.7 * 1.1 * 0.7 / math.sqrt(n)
    r.lambda_lim = round(lambda_lim, 1)
    r.elance = lambda_ > lambda_lim

    if r.elance:
        msgs.append(f"⚠️ Voile élancé : λ={lambda_:.1f} > λlim={lambda_lim:.1f} — effets du 2nd ordre pris en compte")
    else:
        msgs.append(f"✅ Voile court : λ={lambda_:.1f} ≤ λlim={lambda_lim:.1f}")

    # ── Efforts ELU ───────────────────────────────────────────────────────────
    gamma_G, gamma_Q = 1.35, 1.50
    pct_Q = 1 - e.pct_G
    NEd = gamma_G * e.N_k * e.pct_G + gamma_Q * e.N_k * pct_Q
    MEd = gamma_G * e.M_k * e.pct_G + gamma_Q * e.M_k * pct_Q
    VEd = gamma_G * e.V_k * e.pct_G + gamma_Q * e.V_k * pct_Q

    r.NEd = round(NEd, 1)
    r.MEd = round(MEd, 1)
    r.VEd = round(VEd, 1)

    # Excentricités
    e0 = MEd / NEd * 1000 if NEd > 0 else 0    # mm
    e_min = max(ep / 30, 20)                     # mm EC2 §6.1(4)
    e0 = max(e0, e_min)

    # Excentricité 2nd ordre (si élancé)
    if r.elance:
        # Méthode simplifiée EC2 §5.8.8
        c_factor = 10
        K_phi = max(1.0, 1 + 0.35 * math.sqrt(fck/200 + lambda_/150))
        e2 = (1/c_factor) * (fyd/E_s) * (l0*1000)**2 / d
    else:
        e2 = 0.0

    etot = e0 + e2
    MEd_tot = NEd * etot / 1000    # kN.m

    r.e0 = round(e0, 1)
    r.e2 = round(e2, 1)
    r.etot = round(etot, 1)
    r.MEd_tot = round(MEd_tot, 2)

    # ── Armatures verticales (compression composée) ───────────────────────────
    b_m = e.L * 1000    # mm (longueur voile = base de calcul)
    d_m = d / 1000
    b_calc = b_m / 1000  # m

    # Moment réduit
    mu = MEd_tot / (b_calc * (d/1000)**2 * fcd * 1000)
    mu = min(mu, 0.372)
    alpha = (1 - math.sqrt(max(0, 1 - 2*mu)))
    z = d_m * (1 - 0.4 * alpha)

    # Armature de flexion
    As_flex = MEd_tot / (z * fyd / 1000) if z > 0 else 0

    # Armature de compression
    As_comp = max(0, (NEd - b_calc * 1000 * (d/1000) * 0.8 * fcd) / (fyd / 1000))

    As_vert_calc = max(As_flex, As_comp)

    # Minimums EC2 §9.6
    As_vert_min = max(0.002 * ep * e.L * 1000, 0.001 * ep * e.L * 1000)  # mm² total
    As_vert_min_ml = As_vert_min / (e.L * 1000) * 1000                    # mm²/ml par nappe × 2 nappes
    As_vert_max = 0.04 * ep * e.L * 1000                                   # mm² total

    # Par ml par nappe (2 nappes)
    As_vert_ml = max(As_vert_calc / (e.L * 1000) * 1000, As_vert_min / (e.L * 1000) * 1000) / 2

    r.As_vert_calc   = round(As_vert_calc, 0)
    r.As_vert_min    = round(As_vert_min, 0)
    r.As_vert_max    = round(As_vert_max, 0)

    ret, ch = _choisir_armatures_ml(As_vert_ml)
    r.As_vert_retenu = ret
    r.choix_vert     = ch

    # ── Armatures horizontales EC2 §9.6.3 ────────────────────────────────────
    As_horiz_min_ml = max(0.001 * ep * 1000, 25 * ret / 1000)  # mm²/ml
    As_horiz_min_ml = max(As_horiz_min_ml, 0.25 * ret)

    ret_h, ch_h = _choisir_armatures_ml(As_horiz_min_ml)
    r.As_horiz_min    = round(As_horiz_min_ml, 0)
    r.As_horiz_retenu = ret_h
    r.choix_horiz     = ch_h

    # ── Armatures d'about EC2 §9.6.2 ─────────────────────────────────────────
    As_about = max(0.002 * ep * ep, As_vert_calc * 0.25)
    ret_a, ch_a = _choisir_armatures_ml(As_about / ep * 1000)
    r.As_about_calc   = round(As_about, 0)
    r.As_about_retenu = round(ret_a * ep / 1000, 0)
    r.choix_about     = ch_a

    # ── Cisaillement EC2 §6.2 ─────────────────────────────────────────────────
    b_v = ep / 1000
    d_v = d / 1000
    tau_u = VEd / (b_v * d_v * 1000)

    rho_l = min(r.As_vert_retenu / (ep * d), 0.02)
    k_val = min(1 + math.sqrt(200 / d), 2.0)

    if e.norme == "EC2":
        VRd_c = (0.18/1.5) * k_val * (100 * rho_l * fck)**(1/3) * b_v * d_v * 1000
        VRd_c = max(VRd_c, (0.035 * k_val**1.5 * math.sqrt(fck)) * b_v * d_v * 1000)
    else:
        VRd_c = (0.07 + 40 * rho_l) * fcd * b_v * d_v * 1000

    r.tau_u = round(tau_u, 2)
    r.VRd_c = round(VRd_c, 1)
    r.cisaillement_ok = VEd <= VRd_c

    if not r.cisaillement_ok:
        msgs.append(f"⚠️ Cisaillement : VEd={VEd:.1f} kN > VRd,c={VRd_c:.1f} kN — armatures d'effort tranchant requises")
    else:
        msgs.append(f"✅ Cisaillement vérifié : VEd={VEd:.1f} kN ≤ VRd,c={VRd_c:.1f} kN")

    msgs.append(f"Excentricité totale : e0={e0:.1f} + e2={e2:.1f} = etot={etot:.1f} mm")
    msgs.append(f"Armature verticale minimale totale : {round(As_vert_min, 0)} mm² (répartie sur 2 nappes)")

    return r
