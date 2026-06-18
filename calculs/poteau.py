"""
Calcul de poteau béton armé
EC2 (EN 1992-1-1) §5.8 et BAEL 91 révisé 99

Cas traités :
- Compression centrée
- Compression composée (N + M)
- Vérification élancement
"""

import math
from dataclasses import dataclass, field
from .materiaux import Beton, Acier, BETONS, ACIERS, ENROBAGES


@dataclass
class EntreePoteau:
    """Données d'entrée pour le calcul de poteau"""
    # Géométrie
    b: float          # largeur section (mm)
    h: float          # hauteur section (mm)
    longueur: float   # longueur de flambement (m)

    # Chargement
    N_k: float        # effort normal caractéristique total (kN)
    M_k: float = 0.0  # moment caractéristique (kN.m)

    # Pondération (% charges permanentes sur N total)
    pct_G: float = 0.7   # 70% permanentes par défaut

    # Matériaux
    beton: str = "C25/30"
    acier: str = "HA500"
    enrobage_classe: str = "XC1"

    # Options
    norme: str = "EC2"
    conditions_appui: str = "encastre-rotule"  # "encastre-rotule" | "rotule-rotule" | "encastre-encastre"


@dataclass
class ResultatPoteau:
    """Résultats du calcul de poteau"""
    norme: str
    # Sollicitations ELU
    NEd: float = 0.0
    MEd: float = 0.0

    # Géométrie
    d: float = 0.0
    enrobage: float = 0.0
    Ac: float = 0.0     # aire section béton (mm²)

    # Élancement
    l0: float = 0.0     # longueur de flambement (m)
    lambda_: float = 0.0
    lambda_lim: float = 0.0
    elastique: bool = False

    # Excentricités
    e0: float = 0.0     # excentricité de premier ordre (mm)
    e2: float = 0.0     # excentricité du second ordre (mm)
    etot: float = 0.0   # excentricité totale (mm)
    MEd_tot: float = 0.0  # moment total (kN.m)

    # Armatures
    As_calc: float = 0.0
    As_min: float = 0.0
    As_max: float = 0.0
    As_retenu: float = 0.0
    choix_armatures: str = ""

    messages: list = field(default_factory=list)
    verification: dict = field(default_factory=dict)


def calculer_poteau(entree: EntreePoteau) -> ResultatPoteau:
    """Calcul complet d'un poteau rectangulaire"""

    beton = BETONS.get(entree.beton, BETONS["C25/30"])
    acier = ACIERS.get(entree.acier, ACIERS["HA500"])
    enrobage = ENROBAGES.get(entree.enrobage_classe, 25)

    res = ResultatPoteau(norme=entree.norme)
    res.enrobage = enrobage
    res.Ac = entree.b * entree.h

    # Hauteur utile
    res.d = entree.h - enrobage - 8 - 10

    # --- 1. Sollicitations ELU ---
    g_k = entree.N_k * entree.pct_G
    q_k = entree.N_k * (1 - entree.pct_G)
    res.NEd = round(1.35 * g_k + 1.5 * q_k, 1)
    res.MEd = round(1.35 * entree.M_k * entree.pct_G +
                    1.5 * entree.M_k * (1 - entree.pct_G), 2)

    # --- 2. Longueur de flambement ---
    coeff = {"rotule-rotule": 1.0,
             "encastre-rotule": 0.7,
             "encastre-encastre": 0.5}.get(entree.conditions_appui, 0.7)
    res.l0 = round(coeff * entree.longueur, 2)

    # --- 3. Élancement ---
    i = math.sqrt(entree.b * entree.h ** 3 / 12 / (entree.b * entree.h))  # rayon de giration
    res.lambda_ = round((res.l0 * 1000) / i, 1)

    if entree.norme == "EC2":
        # λlim = 20*A*B*C / √n  (simplification A=0.7, B=1.1, C=0.7)
        n = res.NEd / (beton.fcd_ec2 * res.Ac)
        res.lambda_lim = round(20 * 0.7 * 1.1 * 0.7 / math.sqrt(max(n, 0.01)), 1)
    else:
        # BAEL : élancement λ = l0/i, limite 70 (poteau courant)
        res.lambda_lim = 70.0

    res.elastique = res.lambda_ > res.lambda_lim
    if res.elastique:
        res.messages.append(f"Poteau élancé (λ={res.lambda_} > λlim={res.lambda_lim}) — effets du 2nd ordre à prendre en compte")
    else:
        res.messages.append(f"Poteau court (λ={res.lambda_} ≤ λlim={res.lambda_lim}) — pas d'effets du 2nd ordre")

    # --- 4. Excentricités ---
    # Excentricité de 1er ordre
    if res.NEd > 0:
        res.e0 = round(res.MEd * 1e6 / (res.NEd * 1000), 1)  # mm
    else:
        res.e0 = 0.0

    # Excentricité minimale réglementaire
    e_min = max(entree.h / 30, 20)  # mm (EC2 et BAEL)

    # Excentricité additionnelle (imperfections géométriques)
    e_a = res.l0 * 1000 / 400  # mm

    # Effets du second ordre (méthode simplifiée)
    if res.elastique and entree.norme == "EC2":
        # Méthode de la courbure nominale EC2 §5.8.8
        nu = res.NEd / (beton.fcd_ec2 * res.Ac)
        phi_ef = 1.5  # fluage simplifié
        Kr = min(1.0, (nu - 0.4) / (0.6 - 0.4) if nu < 0.6 else 1.0)
        K_phi = max(1 + phi_ef * 0.35 + beton.fck / 200 - res.lambda_ / 150, 1.0)
        c = 10  # coeff distribution moments (cas uniforme)
        eps_yd = acier.fyd_ec2 / acier.Es
        r_min = 0.45 * res.d  # simplifié
        res.e2 = round(Kr * K_phi * (res.lambda_ ** 2 / c) * (eps_yd / 0.45) * res.d / 1000, 1)
    elif res.elastique:
        # BAEL : méthode forfaitaire
        res.e2 = round(3 * res.l0 ** 2 * 1e6 / (res.d * 10 * 100), 1)
    else:
        res.e2 = 0.0

    res.etot = round(max(res.e0, e_min) + res.e2 + e_a, 1)
    res.MEd_tot = round(res.NEd * res.etot / 1000, 2)  # kN.m

    # --- 5. Calcul des armatures ---
    if entree.norme == "EC2":
        fcd = beton.fcd_ec2
        fyd = acier.fyd_ec2
    else:
        fcd = beton.fcd_bael
        fyd = acier.fyd_bael

    # Méthode simplifiée : diagramme d'interaction rectangulaire
    # On cherche As symétrique (As' = As = Ast/2)
    d_prime = enrobage + 8 + 10  # enrobage armature comprimée
    z = res.d - d_prime

    MEd_Nmm = res.MEd_tot * 1e6
    NEd_N = res.NEd * 1000

    if z > 0:
        As_calc = (MEd_Nmm / z - (fcd * entree.b * entree.h * (res.d - entree.h / 2)) / z +
                   NEd_N / 2) / fyd
        res.As_calc = round(max(As_calc, 0), 1)
    else:
        res.As_calc = 0.0

    # Armatures minimales et maximales
    if entree.norme == "EC2":
        # EC2 §9.5.2
        As_min_1 = 0.10 * NEd_N / fyd
        As_min_2 = 0.002 * res.Ac
        res.As_min = round(max(As_min_1, As_min_2), 1)
        res.As_max = round(0.04 * res.Ac, 1)
    else:
        # BAEL A.8.1
        res.As_min = round(max(0.001 * res.Ac, 4 * res.Ac / 1000), 1)
        res.As_max = round(0.05 * res.Ac, 1)

    res.As_retenu = round(min(max(res.As_calc, res.As_min), res.As_max), 1)
    res.choix_armatures = _proposer_armatures_poteau(res.As_retenu)

    res.verification = {
        "NEd_kN": res.NEd,
        "MEd_total_kNm": res.MEd_tot,
        "excentricite_totale_mm": res.etot,
        "elancement": res.lambda_,
        "As_calc_mm2": res.As_calc,
        "As_min_mm2": res.As_min,
        "As_max_mm2": res.As_max,
        "As_retenu_mm2": res.As_retenu,
    }

    return res


def _proposer_armatures_poteau(As_total: float) -> str:
    """Propose des armatures réparties sur les 4 faces"""
    barres = {10: 78.5, 12: 113.1, 14: 153.9, 16: 201.1, 20: 314.2, 25: 490.9}
    meilleur = ""
    ecart_min = float('inf')
    for n in [4, 6, 8, 10, 12]:
        for diam, section in barres.items():
            total = n * section
            if total >= As_total:
                ecart = total - As_total
                if ecart < ecart_min:
                    ecart_min = ecart
                    meilleur = f"{n}HA{diam} ({round(total, 0)} mm²) réparties sur les 4 faces"
    return meilleur or "Section trop grande — revoir la géométrie"
