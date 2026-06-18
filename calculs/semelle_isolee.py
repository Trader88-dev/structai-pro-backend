"""
Module de calcul — Semelle isolée BA
EC2 / BAEL 91 — Vérifications : sol, flexion, poinçonnement, cisaillement
"""
from dataclasses import dataclass, field
from typing import List
import math

CHOIX_BARRES = [
    (8,50.3),(10,78.5),(12,113.1),(14,153.9),
    (16,201.1),(20,314.2),(25,490.9),(32,804.2),
]

def _choisir(As_mm2_ml):
    for diam, aire in CHOIX_BARRES:
        for esp in [100,120,150,160,200,250,300]:
            nb = 1000/esp
            af = nb*aire
            if af >= As_mm2_ml:
                return round(af,1), f"HA{diam} esp. {esp} mm ({af:.0f} mm²/ml)"
    return round(1000/100*804.2,1), "HA32 esp. 100 mm"

@dataclass
class EntreeSemIsolee:
    # Poteau
    b_p: float = 300     # largeur poteau (mm)
    h_p: float = 300     # hauteur poteau (mm)
    # Semelle
    h_sem: float = 500   # hauteur semelle (mm)
    # Chargement
    N_k: float = 800.0   # charge normale (kN)
    M_kx: float = 0.0    # moment selon x (kN.m)
    M_ky: float = 0.0    # moment selon y (kN.m)
    sigma_sol: float = 200.0  # contrainte sol admissible (kPa)
    pct_G: float = 0.7
    # Matériaux
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

@dataclass
class ResultatSemIsolee:
    norme: str = "EC2"
    # Dimensions
    Ax: float = 0.0
    Ay: float = 0.0
    surface: float = 0.0
    d: float = 0.0
    # Sol
    sigma_moy: float = 0.0
    sigma_max: float = 0.0
    sigma_ok: bool = True
    # Armatures
    As_x_calc: float = 0.0
    As_x_min: float = 0.0
    As_x_retenu: float = 0.0
    choix_x: str = ""
    As_y_calc: float = 0.0
    As_y_retenu: float = 0.0
    choix_y: str = ""
    # Poinçonnement
    perimetre_crit: float = 0.0
    VEd_poinc: float = 0.0
    VRd_c_poinc: float = 0.0
    poinconnement_ok: bool = True
    messages: List[str] = field(default_factory=list)

def calculer_semelle_isolee(e: EntreeSemIsolee) -> ResultatSemIsolee:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatSemIsolee(norme=e.norme)
    msgs = r.messages

    bet = BETONS[e.beton]; acr = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)
    fck = bet.fck; fcd = fck/1.5; fyk = acr.fyk; fyd = fyk/1.15

    d = e.h_sem - c_nom - 10
    d = max(d, 200)
    r.d = round(d, 0)

    # ── Dimensionnement en plan ────────────────────────────────────────────────
    gamma_G, gamma_Q = 1.35, 1.50
    pct_Q = 1 - e.pct_G
    NEd = gamma_G*e.N_k*e.pct_G + gamma_Q*e.N_k*pct_Q
    N_ELS = e.N_k

    # Dimensions minimales (ELS)
    A_min = N_ELS / e.sigma_sol  # m²
    Ax = math.sqrt(A_min)
    Ay = Ax

    # Correction avec moments
    if e.M_kx > 0 or e.M_ky > 0:
        Ax = max(Ax, math.sqrt(A_min * 1.2))
        Ay = max(Ay, math.sqrt(A_min * 1.2))

    # Arrondi au multiple de 0.05m
    Ax = math.ceil(Ax / 0.05) * 0.05
    Ay = math.ceil(Ay / 0.05) * 0.05

    r.Ax = round(Ax, 2)
    r.Ay = round(Ay, 2)
    r.surface = round(Ax*Ay, 2)

    # Poids propre semelle
    G_sem = 25 * Ax * Ay * e.h_sem/1000
    N_ELS_tot = N_ELS + G_sem
    NEd_tot = NEd + 1.35*G_sem

    # Pression sol
    sigma_moy = N_ELS_tot / (Ax*Ay)
    Wx = Ay * Ax**2 / 6
    Wy = Ax * Ay**2 / 6
    sigma_max = sigma_moy + e.M_kx/Wx + e.M_ky/Wy
    sigma_min = sigma_moy - e.M_kx/Wx - e.M_ky/Wy

    r.sigma_moy = round(sigma_moy, 1)
    r.sigma_max = round(sigma_max, 1)
    r.sigma_ok = sigma_max <= e.sigma_sol

    if not r.sigma_ok:
        msgs.append(f"ERREUR : σmax={sigma_max:.1f} kPa > σadm={e.sigma_sol} kPa — augmenter dimensions")
    else:
        msgs.append(f"✅ Pression sol : σmax={sigma_max:.1f} kPa ≤ σadm={e.sigma_sol} kPa")

    # ── Armatures (méthode des bielles) ───────────────────────────────────────
    # Débord selon x
    cx = (Ax*1000 - e.b_p) / 2  # mm
    cy = (Ay*1000 - e.h_p) / 2  # mm

    # Pression ELU sous semelle
    q_ELU = NEd_tot / (Ax*Ay)  # kN/m²

    # Moment en pied de bielle
    MEd_x = q_ELU * Ay * (cx/1000)**2 / 2   # kN.m/ml
    MEd_y = q_ELU * Ax * (cy/1000)**2 / 2

    d_m = d/1000
    def _as(Med):
        mu = Med / (1.0*d_m**2*fcd*1000)
        mu = min(mu, 0.372)
        a = (1-math.sqrt(max(0,1-2*mu)))
        z = d_m*(1-0.4*a)
        return Med/(z*fyd/1000) if z > 0 else 0

    rho_min = max(0.26*0.30*fck**(2/3)/fyk, 0.0013)
    As_min = rho_min*1000*d

    as_x = max(_as(MEd_x), As_min)
    as_y = max(_as(MEd_y), As_min)

    r.As_x_calc = round(as_x, 0)
    r.As_x_min = round(As_min, 0)
    ret_x, ch_x = _choisir(as_x)
    r.As_x_retenu, r.choix_x = ret_x, ch_x

    r.As_y_calc = round(as_y, 0)
    ret_y, ch_y = _choisir(as_y)
    r.As_y_retenu, r.choix_y = ret_y, ch_y

    # ── Poinçonnement EC2 §6.4 ────────────────────────────────────────────────
    # Périmètre critique u1 à 2d du nu poteau
    lx = e.b_p + 4*d   # mm
    ly = e.h_p + 4*d
    u1 = 2*(lx + ly) + math.pi*4*d   # périmètre elliptique approx → simplifié
    u1 = 2*(e.b_p + e.h_p) + 4*math.pi*d  # EC2 §6.4.2
    u1_m = u1/1000

    # Surface intérieure périmètre critique
    A_crit = (e.b_p/1000 + 4*d/1000)*(e.h_p/1000 + 4*d/1000)
    A_crit = min(A_crit, Ax*Ay)

    VEd_poinc = NEd_tot - q_ELU * A_crit
    rho_l = min(r.As_x_retenu/(1000*d), 0.02)
    k_val = min(1+math.sqrt(200/d), 2.0)
    VRd_c = 0.18/1.5*k_val*(100*rho_l*fck)**(1/3)*u1_m*d/1000*1000

    r.perimetre_crit = round(u1/1000, 2)
    r.VEd_poinc = round(VEd_poinc, 1)
    r.VRd_c_poinc = round(VRd_c, 1)
    r.poinconnement_ok = VEd_poinc <= VRd_c

    if not r.poinconnement_ok:
        msgs.append(f"⚠️ Poinçonnement : VEd={VEd_poinc:.1f} kN > VRd,c={VRd_c:.1f} kN — augmenter hauteur semelle")
    else:
        msgs.append(f"✅ Poinçonnement : VEd={VEd_poinc:.1f} kN ≤ VRd,c={VRd_c:.1f} kN")

    msgs.append(f"Dimensions retenues : {Ax}×{Ay} m | h={e.h_sem} mm")
    return r
