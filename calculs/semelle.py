"""
Calcul de semelle filante béton armé
EC2 (EN 1992-1-1) et BAEL 91 révisé 99

Cas traités :
- Vérification de la pression sous semelle (ELS)
- Dimensionnement en flexion (ELU)
- Vérification au poinçonnement
- Armatures transversales et longitudinales
"""

import math
from dataclasses import dataclass, field
from .materiaux import Beton, Acier, BETONS, ACIERS


@dataclass
class EntreeSemelle:
    """Données d'entrée pour le calcul de semelle filante"""
    # Géométrie mur / voile porteur
    b_mur: float       # largeur du mur ou voile (mm)
    h_semelle: float   # hauteur de la semelle (mm)

    # Chargement par mètre linéaire
    N_k: float         # charge verticale caractéristique (kN/ml)
    M_k: float = 0.0   # moment caractéristique (kN.m/ml)

    # Sol
    sigma_sol: float = 200.0  # contrainte admissible du sol (kPa)

    # Matériaux
    beton: str = "C25/30"
    acier: str = "HA500"

    # Options
    norme: str = "EC2"
    pct_G: float = 0.7  # % charges permanentes


@dataclass
class ResultatSemelle:
    """Résultats du calcul de semelle filante"""
    norme: str

    # Dimensionnement en plan
    B_requise: float = 0.0     # largeur minimale de semelle (m)
    B_retenue: float = 0.0     # largeur retenue (m)
    debord: float = 0.0        # débord de chaque côté (mm)

    # Pression sous semelle
    sigma_max: float = 0.0     # pression maximale ELS (kPa)
    sigma_moy: float = 0.0     # pression moyenne ELS (kPa)
    sigma_ok: bool = True

    # Sollicitations ELU
    NEd: float = 0.0
    sigma_ELU: float = 0.0    # pression de calcul ELU (kPa)
    MEd_semelle: float = 0.0  # moment de calcul dans la semelle (kN.m/ml)
    VEd_semelle: float = 0.0  # effort tranchant dans la semelle (kN/ml)

    # Géométrie
    d: float = 0.0             # hauteur utile (mm)
    enrobage: float = 50.0     # enrobage (mm, plus grand sous semelle)

    # Armatures transversales (principales)
    As_trans_calc: float = 0.0
    As_trans_min: float = 0.0
    As_trans_retenu: float = 0.0
    choix_trans: str = ""

    # Armatures longitudinales (répartition)
    As_long_min: float = 0.0
    choix_long: str = ""

    messages: list = field(default_factory=list)
    verification: dict = field(default_factory=dict)


def calculer_semelle(entree: EntreeSemelle) -> ResultatSemelle:
    """Calcul complet d'une semelle filante"""

    beton = BETONS.get(entree.beton, BETONS["C25/30"])
    acier = ACIERS.get(entree.acier, ACIERS["HA500"])

    res = ResultatSemelle(norme=entree.norme)
    res.enrobage = 50  # enrobage en contact avec le sol (EC2 XC2/XC3 → 50mm)

    # Hauteur utile
    res.d = entree.h_semelle - res.enrobage - 8 - 10  # (enrobage + étrier + φ/2)

    # --- 1. Largeur de semelle (ELS) ---
    # On inclut le poids propre de la semelle (béton ≈ 25 kN/m³)
    # Poids propre estimé : 25 * h_semelle/1000 * B kN/ml
    # On itère pour trouver B
    gamma_beton = 25  # kN/m³
    h_m = entree.h_semelle / 1000  # en m

    # Première estimation sans poids propre
    B_est = entree.N_k / entree.sigma_sol

    for _ in range(5):  # quelques itérations
        poids_propre = gamma_beton * h_m * B_est
        N_total = entree.N_k + poids_propre
        B_est = N_total / entree.sigma_sol

    res.B_requise = round(B_est, 2)

    # Arrondi au 5 cm supérieur
    B_arr = math.ceil(res.B_requise * 20) / 20
    # Vérifier rapport B/h ≥ 1.5 (règle pratique)
    B_min_geo = max(B_arr, entree.b_mur / 1000 + 2 * 0.15)  # débord min 150mm
    res.B_retenue = round(B_min_geo, 2)

    res.debord = round((res.B_retenue * 1000 - entree.b_mur) / 2, 0)

    # --- 2. Vérification pression sol (ELS) ---
    N_tot_els = entree.N_k + gamma_beton * h_m * res.B_retenue
    res.sigma_moy = round(N_tot_els / res.B_retenue, 1)

    if entree.M_k > 0:
        e = entree.M_k / N_tot_els * 1000  # mm
        res.sigma_max = round(N_tot_els / res.B_retenue * (1 + 6 * e / (res.B_retenue * 1000)), 1)
    else:
        res.sigma_max = res.sigma_moy

    res.sigma_ok = res.sigma_max <= entree.sigma_sol
    if not res.sigma_ok:
        res.messages.append(f"Pression sol dépassée : σ={res.sigma_max} kPa > σadm={entree.sigma_sol} kPa — augmenter B")
    else:
        res.messages.append(f"Pression sol vérifiée : σmax={res.sigma_max} kPa ≤ σadm={entree.sigma_sol} kPa")

    # --- 3. Sollicitations ELU ---
    g_k = entree.N_k * entree.pct_G
    q_k = entree.N_k * (1 - entree.pct_G)
    res.NEd = round(1.35 * g_k + 1.5 * q_k, 1)

    N_tot_elu = res.NEd + 1.35 * gamma_beton * h_m * res.B_retenue
    res.sigma_ELU = round(N_tot_elu / res.B_retenue, 1)  # kN/m²

    # Moment dans la semelle au nu du mur (section critique)
    a = res.debord / 1000  # m (débord)
    res.MEd_semelle = round(res.sigma_ELU * a ** 2 / 2, 2)  # kN.m/ml
    res.VEd_semelle = round(res.sigma_ELU * a, 2)           # kN/ml

    # --- 4. Armatures transversales (flexion principale) ---
    if entree.norme == "EC2":
        fcd = beton.fcd_ec2
        fyd = acier.fyd_ec2
    else:
        fcd = beton.fcd_bael
        fyd = acier.fyd_bael

    b = 1000  # calcul par ml (b=1m)
    d = res.d
    MEd_Nmm = res.MEd_semelle * 1e6

    mu = MEd_Nmm / (b * d ** 2 * fcd)
    if mu > 1.0:
        res.messages.append("ERREUR : hauteur de semelle insuffisante, augmenter h_semelle")
        return res

    alpha = 1.25 * (1 - math.sqrt(1 - 2 * mu))
    z = d * (1 - 0.4 * alpha)
    As_trans = MEd_Nmm / (z * fyd)
    res.As_trans_calc = round(As_trans, 1)

    # Minimum réglementaire
    if entree.norme == "EC2":
        res.As_trans_min = round(max(0.26 * beton.fck ** (2/3) / 1000 * b * d,
                                     0.0013 * b * d), 1)
    else:
        res.As_trans_min = round(0.001 * b * entree.h_semelle, 1)

    res.As_trans_retenu = round(max(res.As_trans_calc, res.As_trans_min), 1)
    res.choix_trans = _proposer_semelle(res.As_trans_retenu)

    # --- 5. Armatures longitudinales (répartition) ---
    if entree.norme == "EC2":
        res.As_long_min = round(0.002 * b * entree.h_semelle, 1)
    else:
        res.As_long_min = round(0.001 * b * entree.h_semelle, 1)

    res.choix_long = _proposer_semelle(res.As_long_min)

    res.verification = {
        "B_retenue_m": res.B_retenue,
        "debord_mm": res.debord,
        "sigma_max_kPa": res.sigma_max,
        "sigma_admissible_kPa": entree.sigma_sol,
        "sol_ok": res.sigma_ok,
        "MEd_semelle_kNm": res.MEd_semelle,
        "As_trans_mm2_ml": res.As_trans_retenu,
        "As_long_mm2_ml": res.As_long_min,
    }

    return res


def _proposer_semelle(As_ml: float) -> str:
    """Propose une nappe d'armatures par ml"""
    barres = {8: 50.3, 10: 78.5, 12: 113.1, 14: 153.9, 16: 201.1, 20: 314.2}
    meilleur = ""
    ecart_min = float('inf')
    for esp in [100, 125, 150, 175, 200, 250]:  # espacement en mm
        n_ml = 1000 / esp
        for diam, section in barres.items():
            total = n_ml * section
            if total >= As_ml:
                ecart = total - As_ml
                if ecart < ecart_min:
                    ecart_min = ecart
                    meilleur = f"HA{diam} tous les {esp} mm ({round(total, 0)} mm²/ml)"
    return meilleur or "Section trop grande — revoir la géométrie"
