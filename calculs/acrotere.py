"""
Module de calcul — Acrotère BA
Flexion composée (compression + vent) — EC2 / BAEL 91 + EC8 sismique simplifié
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
        for esp in [80,100,120,150,160,200,250,300]:
            nb = 1000/esp
            af = nb*aire
            if af >= As_mm2_ml:
                return round(af,1), f"HA{diam} esp. {esp} mm ({af:.0f} mm²/ml)"
    return round(1000/80*804.2,1), "HA32 esp. 80 mm"

@dataclass
class EntreeAcrotere:
    h: float = 0.80        # hauteur acrotère (m)
    e: float = 150         # épaisseur (mm)
    g_k: float = 3.5       # charge permanente linéique (kN/ml) — poids propre + étanchéité
    q_vent: float = 1.0    # pression vent (kN/m²)
    zone_sismique: str = "2"  # zone sismique France (1,2,3,4)
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

@dataclass
class ResultatAcrotere:
    norme: str = "EC2"
    d: float = 0.0
    # ELU vent
    NEd_vent: float = 0.0
    MEd_vent: float = 0.0
    # ELU sismique
    NEd_seis: float = 0.0
    MEd_seis: float = 0.0
    # Cas dimensionnant
    cas_dim: str = ""
    NEd: float = 0.0
    MEd: float = 0.0
    etot: float = 0.0
    # Armatures
    As_calc: float = 0.0
    As_min: float = 0.0
    As_retenu: float = 0.0
    choix: str = ""
    As_rep_retenu: float = 0.0
    choix_rep: str = ""
    # Vérification encastrement
    sigma_beton: float = 0.0
    sigma_ok: bool = True
    messages: List[str] = field(default_factory=list)

def calculer_acrotere(e: EntreeAcrotere) -> ResultatAcrotere:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatAcrotere(norme=e.norme)
    msgs = r.messages

    bet = BETONS[e.beton]; acr = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)
    fck = bet.fck; fcd = fck/1.5; fyk = acr.fyk; fyd = fyk/1.15

    d = e.e - c_nom - 8
    d = max(d, 60)
    r.d = round(d, 0)

    # Poids propre
    G_pp = 25 * e.e/1000 * e.h  # kN/ml

    # ── CAS 1 : Vent ──────────────────────────────────────────────────────────
    F_vent = e.q_vent * e.h   # kN/ml (force horizontale en tête)
    NEd_vent = 1.35 * (e.g_k + G_pp)
    MEd_vent = 1.5 * F_vent * e.h / 2   # moment en pied
    r.NEd_vent = round(NEd_vent, 2)
    r.MEd_vent = round(MEd_vent, 2)

    # ── CAS 2 : Séisme EC8 simplifié ─────────────────────────────────────────
    agR = {"1": 0.4, "2": 0.7, "3": 1.1, "4": 1.6}.get(e.zone_sismique, 0.7)  # m/s²
    S = 1.15   # sol type B
    ag = agR * S / 9.81   # en g
    # Fa = Sa * W (amplification en toiture = 2.5 × ag pour EC8 §4.3.5)
    Sa = 2.5 * ag
    W = (e.g_k + G_pp) * e.h   # kN/ml
    F_seis = Sa * W
    NEd_seis = 1.0 * (e.g_k + G_pp)
    MEd_seis = F_seis * e.h / 2
    r.NEd_seis = round(NEd_seis, 2)
    r.MEd_seis = round(MEd_seis, 2)

    # ── Cas dimensionnant ─────────────────────────────────────────────────────
    if MEd_seis >= MEd_vent:
        r.cas_dim = "Séismique EC8"
        NEd, MEd = NEd_seis, MEd_seis
    else:
        r.cas_dim = "Vent"
        NEd, MEd = NEd_vent, MEd_vent

    r.NEd = round(NEd, 2)
    r.MEd = round(MEd, 2)

    # Excentricité
    etot = MEd / NEd * 1000 if NEd > 0 else e.h*1000/2
    r.etot = round(etot, 1)
    msgs.append(f"Cas dimensionnant : {r.cas_dim} | MEd={MEd:.2f} kN.m | NEd={NEd:.2f} kN")

    # ── Armatures ────────────────────────────────────────────────────────────
    d_m = d/1000
    mu = MEd / (1.0 * d_m**2 * fcd * 1000)
    mu = min(mu, 0.372)
    alpha_c = (1 - math.sqrt(max(0, 1-2*mu)))
    z = d_m*(1-0.4*alpha_c)
    As_flex = MEd/(z*fyd/1000) if z > 0 else 0
    As_comp = max(0, (NEd - 1.0*(d/1000)*0.8*fcd*1000)/(fyd/1000))
    As_calc = max(As_flex, As_comp)

    rho_min = max(0.26*0.30*fck**(2/3)/fyk, 0.0013)
    As_min = rho_min*1000*d
    As_calc = max(As_calc, As_min)

    r.As_calc = round(As_calc, 0)
    r.As_min = round(As_min, 0)
    ret, ch = _choisir(As_calc)
    r.As_retenu, r.choix = ret, ch

    # Armatures de répartition
    ret_r, ch_r = _choisir(max(As_calc*0.2, As_min*0.2))
    r.As_rep_retenu, r.choix_rep = ret_r, ch_r

    # ── Vérification encastrement ─────────────────────────────────────────────
    # Contrainte de compression à l'encastrement
    sigma_b = NEd/(e.e*1000/1000) + MEd*6/(e.e/1000)**2/1000  # MPa approx
    sigma_lim = 0.6*fck
    r.sigma_beton = round(sigma_b, 2)
    r.sigma_ok = sigma_b <= sigma_lim

    if not r.sigma_ok:
        msgs.append(f"⚠️ Contrainte béton encastrement : {sigma_b:.2f} MPa > 0.6fck={sigma_lim:.1f} MPa")
    else:
        msgs.append(f"✅ Contrainte béton encastrement : {sigma_b:.2f} MPa ≤ 0.6fck={sigma_lim:.1f} MPa")

    return r
