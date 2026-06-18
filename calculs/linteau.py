"""
Module de calcul — Linteau BA
Flexion simple + cisaillement — EC2 / BAEL 91
"""
from dataclasses import dataclass, field
from typing import List
import math

CHOIX_BARRES = [
    (6,28.3),(8,50.3),(10,78.5),(12,113.1),(14,153.9),
    (16,201.1),(20,314.2),(25,490.9),(32,804.2),
]

def _choisir(As_mm2):
    for diam, aire in CHOIX_BARRES:
        for nb in range(2,12):
            if nb*aire >= As_mm2:
                return round(nb*aire,1), f"{nb}HA{diam} ({nb*aire:.0f} mm²)"
    return round(8*804.2,1), f"8HA32"

@dataclass
class EntreeLinteau:
    b: float = 200       # largeur (mm)
    h: float = 300       # hauteur (mm)
    L: float = 1.5       # portée (m)
    g_k: float = 10.0    # charge permanente (kN/m)
    q_k: float = 5.0     # charge variable (kN/m)
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

@dataclass
class ResultatLinteau:
    norme: str = "EC2"
    d: float = 0.0
    MEd: float = 0.0
    VEd: float = 0.0
    mu: float = 0.0
    As_calc: float = 0.0
    As_min: float = 0.0
    As_retenu: float = 0.0
    choix: str = ""
    tau_u: float = 0.0
    VRd_c: float = 0.0
    armatures_cis: bool = False
    messages: List[str] = field(default_factory=list)

def calculer_linteau(e: EntreeLinteau) -> ResultatLinteau:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatLinteau(norme=e.norme)
    msgs = r.messages

    bet = BETONS[e.beton]; acr = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)
    fck = bet.fck; fcd = fck/1.5; fyk = acr.fyk; fyd = fyk/1.15

    d = e.h - c_nom - 10
    d = max(d, 80)
    r.d = round(d, 0)

    q_ELU = 1.35*e.g_k + 1.5*e.q_k
    MEd = q_ELU * e.L**2 / 8
    VEd = q_ELU * e.L / 2
    r.MEd = round(MEd, 2)
    r.VEd = round(VEd, 1)

    b_m = e.b/1000; d_m = d/1000
    mu = MEd/(b_m*d_m**2*fcd*1000)
    mu = min(mu, 0.372)
    r.mu = round(mu, 3)
    alpha_c = (1-math.sqrt(max(0,1-2*mu)))
    z = d_m*(1-0.4*alpha_c)
    As_calc = MEd/(z*fyd/1000) if z > 0 else 0

    rho_min = max(0.26*0.30*fck**(2/3)/fyk, 0.0013)
    As_min = rho_min*e.b*d
    As_calc = max(As_calc, As_min)

    r.As_calc = round(As_calc, 0)
    r.As_min = round(As_min, 0)
    ret, ch = _choisir(As_calc)
    r.As_retenu, r.choix = ret, ch

    rho_l = min(ret/(e.b*d), 0.02)
    k_val = min(1+math.sqrt(200/d), 2.0)
    tau_u = VEd/(b_m*d_m*1000)

    if e.norme == "EC2":
        VRd_c = (0.18/1.5)*k_val*(100*rho_l*fck)**(1/3)*b_m*d_m*1000
        VRd_c = max(VRd_c, (0.035*k_val**1.5*math.sqrt(fck))*b_m*d_m*1000)
    else:
        VRd_c = (0.07+40*rho_l)*fcd*b_m*d_m*1000

    r.tau_u = round(tau_u, 2)
    r.VRd_c = round(VRd_c, 1)
    r.armatures_cis = VEd > VRd_c

    mu_lim = 0.372 if e.norme == "EC2" else 0.186
    if mu <= mu_lim:
        msgs.append(f"✅ Section simplement armée : μ={mu:.3f} ≤ {mu_lim}")
    else:
        msgs.append(f"❌ Section doublement armée nécessaire : μ={mu:.3f} > {mu_lim}")

    if r.armatures_cis:
        msgs.append(f"⚠️ Cadres nécessaires : VEd={VEd:.1f} kN > VRd,c={VRd_c:.1f} kN")
    else:
        msgs.append(f"✅ Cisaillement béton seul : VEd={VEd:.1f} kN ≤ VRd,c={VRd_c:.1f} kN")

    return r
