"""
Module de calcul — Escalier BA
Volée droite — Flexion simple — EC2 / BAEL 91
"""
from dataclasses import dataclass, field
from typing import List
import math

CHOIX_BARRES = [
    (6,28.3),(8,50.3),(10,78.5),(12,113.1),(14,153.9),
    (16,201.1),(20,314.2),(25,490.9),(32,804.2),
]

def _choisir(As_mm2_ml):
    for diam, aire in CHOIX_BARRES:
        for esp in [80,100,120,150,160,200,250]:
            nb = 1000/esp
            af = nb*aire
            if af >= As_mm2_ml:
                return round(af,1), f"HA{diam} esp. {esp} mm ({af:.0f} mm²/ml)"
    return round(1000/80*804.2,1), "HA32 esp. 80 mm"

@dataclass
class EntreeEscalier:
    L_h: float = 3.0       # longueur horizontale projetée (m)
    hauteur: float = 2.7   # hauteur totale (m)
    g_giron: float = 0.28  # giron (m)
    h_contre: float = 0.17 # hauteur contre-marche (m)
    ep: float = 150        # épaisseur paillasse (mm)
    g_k: float = 6.0       # charge permanente (kN/m²)
    q_k: float = 2.5       # charge variable (kN/m²)
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

@dataclass
class ResultatEscalier:
    norme: str = "EC2"
    alpha_deg: float = 0.0    # angle inclinaison (°)
    L_inclinee: float = 0.0   # longueur inclinée (m)
    d: float = 0.0
    q_ELU: float = 0.0
    MEd: float = 0.0
    VEd: float = 0.0
    As_princ_calc: float = 0.0
    As_princ_min: float = 0.0
    As_princ_retenu: float = 0.0
    choix_princ: str = ""
    As_rep_retenu: float = 0.0
    choix_rep: str = ""
    fleche_ok: bool = True
    fleche_calc: float = 0.0
    fleche_adm: float = 0.0
    messages: List[str] = field(default_factory=list)

def calculer_escalier(e: EntreeEscalier) -> ResultatEscalier:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatEscalier(norme=e.norme)
    msgs = r.messages

    bet = BETONS[e.beton]; acr = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)
    fck = bet.fck; fcd = fck/1.5; fyk = acr.fyk; fyd = fyk/1.15
    E_cm = 22000*((fck+8)/10)**0.3

    # Angle
    alpha = math.atan(e.hauteur / e.L_h)
    alpha_deg = math.degrees(alpha)
    L_inc = e.L_h / math.cos(alpha)
    r.alpha_deg = round(alpha_deg, 1)
    r.L_inclinee = round(L_inc, 2)

    if alpha_deg > 45:
        msgs.append("⚠️ Angle > 45° — escalier très raide")

    # Hauteur utile
    d = e.ep - c_nom - 8
    d = max(d, 80)
    r.d = round(d, 0)

    # Charges sur paillasse inclinée
    poids_pp = 25 * e.ep/1000 / math.cos(alpha)  # kN/m²
    g_tot = e.g_k + poids_pp
    q_ELU = 1.35*g_tot + 1.5*e.q_k
    r.q_ELU = round(q_ELU, 2)

    # Moments (appuis simples)
    MEd = q_ELU * e.L_h**2 / 8
    VEd = q_ELU * e.L_h / 2
    r.MEd = round(MEd, 2)
    r.VEd = round(VEd, 1)

    # Armatures principales
    d_m = d/1000
    mu = MEd / (1.0 * d_m**2 * fcd * 1000)
    mu = min(mu, 0.372)
    alpha_c = (1 - math.sqrt(max(0, 1-2*mu)))
    z = d_m*(1-0.4*alpha_c)
    As_calc = MEd/(z*fyd/1000) if z > 0 else 0

    rho_min = max(0.26*0.30*fck**(2/3)/fyk, 0.0013)
    As_min = rho_min*1000*d
    As_calc = max(As_calc, As_min)

    r.As_princ_calc = round(As_calc, 0)
    r.As_princ_min = round(As_min, 0)
    ret, ch = _choisir(As_calc)
    r.As_princ_retenu, r.choix_princ = ret, ch

    # Armatures de répartition (20% des principales)
    As_rep = max(As_calc * 0.20, As_min * 0.20)
    ret_r, ch_r = _choisir(As_rep)
    r.As_rep_retenu, r.choix_rep = ret_r, ch_r

    # Flèche forfaitaire L/h ≥ 20 (dalles sur appuis simples)
    lh_reel = e.L_h * 1000 / d
    lh_lim = 20.0
    r.fleche_adm = round(e.L_h*1000/250, 1)
    r.fleche_calc = round(5/48*q_ELU*(e.L_h*1000)**4/(E_cm*(1000*e.ep**3/12))*1e-3, 1)
    r.fleche_ok = lh_reel <= lh_lim*1.3

    if not r.fleche_ok:
        msgs.append(f"⚠️ Flèche : L/d={lh_reel:.0f} > {lh_lim:.0f} — augmenter épaisseur")
    else:
        msgs.append(f"✅ Flèche : L/d={lh_reel:.0f} ≤ {lh_lim:.0f}")

    msgs.append(f"Angle paillasse : {alpha_deg:.1f}° | Longueur inclinée : {L_inc:.2f} m")
    return r
