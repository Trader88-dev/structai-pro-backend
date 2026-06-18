"""
Calcul de poutre béton armé en flexion simple
EC2 (EN 1992-1-1) et BAEL 91 révisé 99

Hypothèses :
- Section rectangulaire
- Flexion simple (pas d'effort normal)
- Etat limite ultime (ELU)
- Diagramme parabole-rectangle (EC2) / rectangulaire simplifié (BAEL)
"""

import math
from dataclasses import dataclass, field
from typing import Optional
from .materiaux import Beton, Acier, BETONS, ACIERS, ENROBAGES


@dataclass
class EntreePoutre:
    """Données d'entrée pour le calcul de poutre"""
    # Géométrie
    b: float          # largeur de la section (mm)
    h: float          # hauteur totale de la section (mm)
    portee: float     # portée (m)

    # Chargement
    g_k: float        # charge permanente caractéristique (kN/m)
    q_k: float        # charge variable caractéristique (kN/m)

    # Matériaux
    beton: str = "C25/30"   # classe de béton
    acier: str = "HA500"    # nuance d'acier
    enrobage_classe: str = "XC1"  # classe d'exposition

    # Options
    norme: str = "EC2"      # "EC2" ou "BAEL"


@dataclass
class ResultatPoutre:
    """Résultats du calcul de poutre"""
    norme: str
    # Sollicitations
    MEd: float = 0.0          # moment de calcul ELU (kN.m)
    VEd: float = 0.0          # effort tranchant ELU (kN)

    # Géométrie utile
    d: float = 0.0            # hauteur utile (mm)
    enrobage: float = 0.0     # enrobage nominal (mm)

    # Résultats flexion
    mu: float = 0.0           # moment réduit
    pivot: str = ""           # pivot A ou B
    alpha: float = 0.0        # position axe neutre relatif (x/d)
    As_calc: float = 0.0      # section d'acier calculée (mm²)
    As_min: float = 0.0       # section d'acier minimale (mm²)
    As_retenu: float = 0.0    # section d'acier retenue (mm²)

    # Résultats cisaillement
    tau_u: float = 0.0        # contrainte de cisaillement (MPa)
    VRd_c: float = 0.0        # résistance cisaillement béton seul (kN)
    armatures_cisaillement: bool = False

    # Proposition armatures
    choix_armatures: str = ""
    verification: dict = field(default_factory=dict)
    messages: list = field(default_factory=list)


def calculer_poutre(entree: EntreePoutre) -> ResultatPoutre:
    """Calcul complet d'une poutre rectangulaire en flexion simple"""

    beton = BETONS.get(entree.beton, BETONS["C25/30"])
    acier = ACIERS.get(entree.acier, ACIERS["HA500"])
    enrobage = ENROBAGES.get(entree.enrobage_classe, 25)

    res = ResultatPoutre(norme=entree.norme)
    res.enrobage = enrobage

    # --- 1. Sollicitations ELU ---
    if entree.norme == "EC2":
        # Combinaison ELU fondamentale : 1.35*G + 1.5*Q
        q_elu = 1.35 * entree.g_k + 1.5 * entree.q_k
    else:
        # BAEL : 1.35*G + 1.5*Q (même combinaison)
        q_elu = 1.35 * entree.g_k + 1.5 * entree.q_k

    res.MEd = round(q_elu * entree.portee ** 2 / 8, 2)   # kN.m (travée isostatique)
    res.VEd = round(q_elu * entree.portee / 2, 2)         # kN

    # --- 2. Hauteur utile ---
    # d = h - enrobage - φetrier - φlong/2 (estimé avec φ=20mm, étrier=8mm)
    res.d = entree.h - enrobage - 8 - 10
    d = res.d  # raccourci local

    # --- 3. Flexion simple ---
    if entree.norme == "EC2":
        fcd = beton.fcd_ec2
        fyd = acier.fyd_ec2
        # Moment réduit μ = MEd / (b * d² * fcd)
        MEd_Nmm = res.MEd * 1e6  # kN.m → N.mm
        mu = MEd_Nmm / (entree.b * d ** 2 * fcd)
        res.mu = round(mu, 4)

        # Limite pivot A/B (avec εs=10‰ et εu=3.5‰)
        mu_lim = 0.372  # valeur limite pivot A pour HA500
        res.pivot = "A" if mu <= mu_lim else "B"

        if mu > 1.0:
            res.messages.append("ERREUR : section insuffisante, augmenter b ou h")
            return res

        # Position axe neutre α = x/d
        alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu))
        res.alpha = round(alpha, 4)

        # Bras de levier z
        z = d * (1 - 0.4 * alpha)

        # Section d'acier
        As_calc = MEd_Nmm / (z * fyd)
        res.As_calc = round(As_calc, 1)

        # Armature minimale EC2 §9.2.1.1
        As_min_1 = 0.26 * (beton.fck ** (2/3) / 1000) * entree.b * d  # approximation
        As_min_2 = 0.0013 * entree.b * d
        res.As_min = round(max(As_min_1, As_min_2), 1)

    else:  # BAEL 91
        fbu = beton.fcd_bael
        fed = acier.fyd_bael
        MEd_Nmm = res.MEd * 1e6

        # Coefficient de pivot μbu (limite section simplement armée)
        # Pour HA500 : αl = 0.259, μbu = αl*(1 - 0.4*αl)*fbu*b*d²
        alpha_lim = 0.259  # BAEL pivot B pour Fe500
        mu_bu = alpha_lim * (1 - 0.4 * alpha_lim)
        mu = MEd_Nmm / (fbu * entree.b * d ** 2)
        res.mu = round(mu, 4)
        res.pivot = "A" if mu <= mu_bu else "B"

        if mu > 1.0:
            res.messages.append("ERREUR : section insuffisante, augmenter b ou h")
            return res

        alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu))
        res.alpha = round(alpha, 4)
        z = d * (1 - 0.4 * alpha)
        As_calc = MEd_Nmm / (z * fed)
        res.As_calc = round(As_calc, 1)

        # Armature minimale BAEL A.4.2
        res.As_min = round(max(0.001 * entree.b * entree.h,
                               0.23 * entree.b * d * beton.fck / acier.fyk), 1)

    res.As_retenu = round(max(res.As_calc, res.As_min), 1)

    # --- 4. Cisaillement ---
    VEd_N = res.VEd * 1000
    tau = VEd_N / (entree.b * d)
    res.tau_u = round(tau, 3)

    if entree.norme == "EC2":
        # VRd,c minimum EC2 §6.2.2
        k = min(1 + math.sqrt(200 / d), 2.0)
        rho_l = min(res.As_retenu / (entree.b * d), 0.02)
        VRd_c = (0.18 / 1.5) * k * (100 * rho_l * beton.fck) ** (1/3) * entree.b * d
        res.VRd_c = round(VRd_c / 1000, 2)
    else:
        # BAEL : τu = 0.2*fc28/γb ≤ 5 MPa
        tau_lim = min(0.2 * beton.fck / 1.5, 5.0)
        res.VRd_c = round(tau_lim * entree.b * d / 1000, 2)

    res.armatures_cisaillement = res.VEd > res.VRd_c

    # --- 5. Proposition armatures ---
    res.choix_armatures = _proposer_armatures(res.As_retenu)

    # --- 6. Vérifications ---
    res.verification = {
        "mu_ok": res.mu <= (0.372 if entree.norme == "EC2" else 0.259 * (1 - 0.4 * 0.259)),
        "As_calc_mm2": res.As_calc,
        "As_min_mm2": res.As_min,
        "As_retenu_mm2": res.As_retenu,
        "cisaillement_ok": not res.armatures_cisaillement,
    }

    if res.armatures_cisaillement:
        res.messages.append(f"Armatures de cisaillement nécessaires (VEd={res.VEd} kN > VRd,c={res.VRd_c} kN)")
    else:
        res.messages.append(f"Pas d'armatures de cisaillement nécessaires (VEd={res.VEd} kN ≤ VRd,c={res.VRd_c} kN)")

    return res


def _proposer_armatures(As_cm2_requis: float) -> str:
    """Propose une combinaison de barres HA pour couvrir la section requise"""
    As_mm2 = As_cm2_requis
    # Sections unitaires barres HA courantes (mm²)
    barres = {
        8:  50.3,
        10: 78.5,
        12: 113.1,
        14: 153.9,
        16: 201.1,
        20: 314.2,
        25: 490.9,
        32: 804.2,
    }
    meilleur = ""
    ecart_min = float('inf')
    for n in range(2, 8):
        for diam, section in barres.items():
            total = n * section
            if total >= As_mm2:
                ecart = total - As_mm2
                if ecart < ecart_min:
                    ecart_min = ecart
                    meilleur = f"{n}HA{diam} ({round(total, 0)} mm²)"
    return meilleur if meilleur else "Section trop grande — vérifier la géométrie"
