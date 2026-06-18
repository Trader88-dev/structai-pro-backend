"""
Module de calcul — Mur de soutènement BA (voile + semelle)
Stabilité (glissement, renversement, portance) + ferraillage EC2 / BAEL 91
"""
from dataclasses import dataclass, field
from typing import List
import math

CHOIX_BARRES = [
    (8,50.3),(10,78.5),(12,113.1),(14,153.9),
    (16,201.1),(20,314.2),(25,490.9),(32,804.2),
]

def _choisir_ml(As_mm2_ml):
    for diam, aire in CHOIX_BARRES:
        for esp in [100,120,150,160,200,250,300]:
            nb = 1000/esp; af = nb*aire
            if af >= As_mm2_ml:
                return round(af,1), f"HA{diam} esp. {esp} mm ({af:.0f} mm²/ml)"
    return round(1000/100*804.2,1), "HA32 esp. 100 mm"

@dataclass
class EntreeMurSoutenement:
    H: float = 3.0          # hauteur totale (m)
    e_voile: float = 250    # épaisseur voile (mm)
    B_semelle: float = 2.0  # largeur semelle (m)
    e_semelle: float = 400  # épaisseur semelle (mm)
    d_encastrement: float = 0.5  # profondeur encastrement (m)
    gamma_terre: float = 18.0    # poids volumique terre (kN/m³)
    phi_deg: float = 30.0        # angle frottement interne (°)
    delta_deg: float = 0.0       # angle frottement mur-sol (°)
    q_surcharge: float = 10.0    # surcharge derrière mur (kN/m²)
    sigma_sol: float = 200.0     # contrainte sol admissible (kPa)
    mu_glissement: float = 0.5   # coefficient frottement semelle/sol
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC2"
    norme: str = "EC2"

@dataclass
class ResultatMurSoutenement:
    norme: str = "EC2"
    # Poussée des terres
    Ka: float = 0.0
    Ea: float = 0.0      # poussée active (kN/ml)
    Eq: float = 0.0      # poussée surcharge (kN/ml)
    # Stabilité
    stabilite_glissement: float = 0.0
    stabilite_renversement: float = 0.0
    stabilite_portance: float = 0.0
    glissement_ok: bool = True
    renversement_ok: bool = True
    portance_ok: bool = True
    sigma_max: float = 0.0
    sigma_min: float = 0.0
    # Ferraillage voile (pied de voile)
    As_voile_calc: float = 0.0
    As_voile_retenu: float = 0.0
    choix_voile: str = ""
    As_voile_horiz: float = 0.0
    choix_voile_horiz: str = ""
    # Ferraillage semelle (talon)
    As_talon_calc: float = 0.0
    As_talon_retenu: float = 0.0
    choix_talon: str = ""
    messages: List[str] = field(default_factory=list)

def calculer_mur_soutenement(e: EntreeMurSoutenement) -> ResultatMurSoutenement:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatMurSoutenement(norme=e.norme)
    msgs = r.messages

    bet = BETONS[e.beton]; acr = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 30)
    fck = bet.fck; fcd = fck/1.5; fyk = acr.fyk; fyd = fyk/1.15

    phi = math.radians(e.phi_deg)
    delta = math.radians(e.delta_deg)

    # ── Coefficient de poussée active (Coulomb) ────────────────────────────────
    Ka = math.cos(phi)**2 / (math.cos(delta)*(1+math.sqrt(
        math.sin(phi+delta)*math.sin(phi)/(math.cos(delta))))**2)
    r.Ka = round(Ka, 3)

    # Hauteur de poussée totale (voile + semelle)
    H_tot = e.H + e.d_encastrement

    # Poussée active des terres
    Ea = 0.5 * Ka * e.gamma_terre * H_tot**2
    # Poussée de la surcharge
    Eq = Ka * e.q_surcharge * H_tot

    r.Ea = round(Ea, 2)
    r.Eq = round(Eq, 2)

    F_horiz = Ea + Eq  # kN/ml

    # Point d'application
    y_Ea = H_tot / 3
    y_Eq = H_tot / 2

    # ── Poids propres ─────────────────────────────────────────────────────────
    G_voile = 25 * e.e_voile/1000 * e.H           # kN/ml
    G_sem   = 25 * e.B_semelle * e.e_semelle/1000  # kN/ml

    # Largeur talon (derrière voile)
    b_talon = e.B_semelle - e.e_voile/1000 - 0.3  # m (semelle avant = 0.3m)
    b_talon = max(b_talon, 0.3)
    G_terre = e.gamma_terre * b_talon * e.H        # kN/ml
    G_surcharge = e.q_surcharge * b_talon          # kN/ml

    W_tot = G_voile + G_sem + G_terre + G_surcharge   # kN/ml

    # ── Stabilité au glissement ───────────────────────────────────────────────
    F_resist_gliss = e.mu_glissement * W_tot
    Fg = F_resist_gliss / F_horiz
    r.stabilite_glissement = round(Fg, 2)
    r.glissement_ok = Fg >= 1.5
    if not r.glissement_ok:
        msgs.append(f"❌ Glissement : Fg={Fg:.2f} < 1.5 — augmenter B ou ajouter clé anti-glissement")
    else:
        msgs.append(f"✅ Glissement : Fg={Fg:.2f} ≥ 1.5")

    # ── Stabilité au renversement ─────────────────────────────────────────────
    # Point de rotation = bout avant de la semelle
    x_voile = 0.3 + e.e_voile/1000/2     # m depuis bout avant
    x_sem_cdg = e.B_semelle/2
    x_terre = e.B_semelle - b_talon/2

    M_stabilisant = (G_voile*x_voile + G_sem*x_sem_cdg + G_terre*x_terre +
                     G_surcharge*x_terre)
    M_renversant = Ea*y_Ea + Eq*y_Eq

    Fr = M_stabilisant / M_renversant
    r.stabilite_renversement = round(Fr, 2)
    r.renversement_ok = Fr >= 2.0
    if not r.renversement_ok:
        msgs.append(f"❌ Renversement : Fr={Fr:.2f} < 2.0 — augmenter B")
    else:
        msgs.append(f"✅ Renversement : Fr={Fr:.2f} ≥ 2.0")

    # ── Contraintes sous semelle (ELS) ────────────────────────────────────────
    e_excentricite = e.B_semelle/2 - M_stabilisant/W_tot + M_renversant/W_tot
    sigma_moy = W_tot / e.B_semelle
    sigma_max = W_tot/e.B_semelle + 6*W_tot*e_excentricite/e.B_semelle**2
    sigma_min = W_tot/e.B_semelle - 6*W_tot*e_excentricite/e.B_semelle**2
    r.sigma_max = round(abs(sigma_max), 1)
    r.sigma_min = round(sigma_min, 1)

    Fp = e.sigma_sol / abs(sigma_max)
    r.stabilite_portance = round(Fp, 2)
    r.portance_ok = abs(sigma_max) <= e.sigma_sol
    if not r.portance_ok:
        msgs.append(f"❌ Portance : σmax={abs(sigma_max):.1f} kPa > σadm={e.sigma_sol} kPa")
    else:
        msgs.append(f"✅ Portance : σmax={abs(sigma_max):.1f} kPa ≤ σadm={e.sigma_sol} kPa")

    # ── Ferraillage voile (flexion en pied) ───────────────────────────────────
    d_voile = e.e_voile - c_nom - 8
    d_voile = max(d_voile, 100)
    d_m = d_voile/1000

    # Moment en pied de voile ELU
    MEd_voile = 1.35*(0.5*Ka*e.gamma_terre*e.H**3/3 +
                      Ka*e.q_surcharge*e.H**2/2)

    mu = MEd_voile/(1.0*d_m**2*fcd*1000)
    mu = min(mu, 0.372)
    alpha_c = (1-math.sqrt(max(0,1-2*mu)))
    z = d_m*(1-0.4*alpha_c)
    As_voile = MEd_voile/(z*fyd/1000) if z > 0 else 0

    rho_min = max(0.26*0.30*fck**(2/3)/fyk, 0.0013)
    As_min_voile = rho_min*1000*d_voile
    As_voile = max(As_voile, As_min_voile)

    r.As_voile_calc = round(As_voile, 0)
    ret_v, ch_v = _choisir_ml(As_voile)
    r.As_voile_retenu, r.choix_voile = ret_v, ch_v

    # Armatures horizontales voile (minimum)
    As_horiz = max(0.001*e.e_voile*1000, 0.25*As_voile)
    ret_vh, ch_vh = _choisir_ml(As_horiz)
    r.As_voile_horiz, r.choix_voile_horiz = ret_vh, ch_vh

    # ── Ferraillage talon semelle ─────────────────────────────────────────────
    d_sem = e.e_semelle - c_nom - 10
    d_sem = max(d_sem, 200)
    d_ms = d_sem/1000

    # Moment en encastrement du talon
    q_talon = sigma_max   # kPa approx (réaction sol)
    G_talon = e.gamma_terre*e.H + e.q_surcharge
    MEd_talon = abs((q_talon - G_talon)*b_talon**2/2)

    mu_t = MEd_talon/(1.0*d_ms**2*fcd*1000)
    mu_t = min(mu_t, 0.372)
    alpha_t = (1-math.sqrt(max(0,1-2*mu_t)))
    z_t = d_ms*(1-0.4*alpha_t)
    As_talon = MEd_talon/(z_t*fyd/1000) if z_t > 0 else 0
    As_talon = max(As_talon, rho_min*1000*d_sem)

    r.As_talon_calc = round(As_talon, 0)
    ret_t, ch_t = _choisir_ml(As_talon)
    r.As_talon_retenu, r.choix_talon = ret_t, ch_t

    msgs.append(f"Ka={Ka:.3f} | Ea={Ea:.1f} kN/ml | W={W_tot:.1f} kN/ml")
    return r
