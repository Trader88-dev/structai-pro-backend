"""
Module de calcul — Poutre continue (2 à 5 travées)
Méthode : Caquot (règlement français) + vérifications EC2 / BAEL 91
"""

from dataclasses import dataclass, field
from typing import List
import math

CHOIX_BARRES = [
    (6, 28.3), (8, 50.3), (10, 78.5), (12, 113.1),
    (14, 153.9), (16, 201.1), (20, 314.2), (25, 490.9), (32, 804.2),
]

def _choisir_armatures(As_mm2: float, b_mm: float = 250) -> tuple:
    """Choix armatures avec limite de nb barres selon largeur (espacement min 40mm)"""
    # Nombre max de barres en 1 lit selon largeur
    # nb_max = (b - 2*enrobage - diam) / (diam + espacement_min) + 1
    for diam, aire_1 in CHOIX_BARRES:
        nb_max = max(2, int((b_mm - 2*30 - diam) / (diam + 40)) + 1)
        nb_max = min(nb_max, 8)  # max 8 barres par lit
        for nb in range(2, nb_max + 1):
            if nb * aire_1 >= As_mm2:
                return round(nb * aire_1, 1), f"{nb}HA{diam} ({nb*aire_1:.0f} mm²)"
    # Si pas trouvé avec 1 lit, essayer avec plus de barres
    for diam, aire_1 in CHOIX_BARRES:
        for nb in range(2, 15):
            if nb * aire_1 >= As_mm2:
                return round(nb * aire_1, 1), f"{nb}HA{diam} ({nb*aire_1:.0f} mm²)"
    return round(12 * 804.2, 1), f"12HA32 ({12*804.2:.0f} mm²)"

@dataclass
class Travee:
    L: float
    g_k: float
    q_k: float

@dataclass
class EntreePoutreContinue:
    b: float
    h: float
    travees: List[Travee]
    appui_gauche: str = "appuye"
    appui_droit:  str = "appuye"
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

@dataclass
class ResultatTravee:
    numero: int = 0
    L: float = 0.0
    q_ELU: float = 0.0
    q_ELS: float = 0.0
    M_trav: float = 0.0
    M_app_g: float = 0.0
    M_app_d: float = 0.0
    V_g: float = 0.0
    V_d: float = 0.0
    As_trav_calc: float = 0.0
    As_trav_retenu: float = 0.0
    choix_trav: str = ""
    As_chap_g_calc: float = 0.0
    As_chap_g_retenu: float = 0.0
    choix_chap_g: str = ""
    As_chap_d_calc: float = 0.0
    As_chap_d_retenu: float = 0.0
    choix_chap_d: str = ""
    tau_u: float = 0.0
    VRd_c: float = 0.0
    armatures_cis: bool = False
    fleche: float = 0.0
    fleche_adm: float = 0.0
    fleche_ok: bool = True
    wk: float = 0.0
    wk_lim: float = 0.3
    fissuration_ok: bool = True

@dataclass
class ResultatPoutreContinue:
    norme: str = "EC2"
    d: float = 0.0
    travees_res: List[ResultatTravee] = field(default_factory=list)
    As_min: float = 0.0
    messages: List[str] = field(default_factory=list)


def _caquot(travees: List[Travee], appui_g: str, appui_d: str,
            gamma_G: float, gamma_Q: float) -> tuple:
    """
    Méthode de Caquot corrigée.
    Portées fictives : L'i = max(Li, 0.8 * Li+1) côté gauche de l'appui
                       L'i+1 = max(Li+1, 0.8 * Li) côté droit de l'appui
    """
    n = len(travees)
    q = [gamma_G * t.g_k + gamma_Q * t.q_k for t in travees]

    M = [0.0] * (n + 1)
    # Conditions aux limites
    M[0] = 0.0 if appui_g == "appuye" else -q[0] * travees[0].L**2 / 16
    M[n] = 0.0 if appui_d == "appuye" else -q[-1] * travees[-1].L**2 / 16

    # Portées fictives CORRIGÉES
    # Pour l'appui i : côté gauche = travée i-1, côté droit = travée i
    # L'g = max(L_{i-1}, 0.8 * L_i)  — portée fictive côté gauche
    # L'd = max(L_i, 0.8 * L_{i-1})  — portée fictive côté droit

    for iteration in range(100):
        M_old = M[:]
        for i in range(1, n):
            L_g = travees[i-1].L   # portée travée gauche
            L_d = travees[i].L     # portée travée droite
            q_g = q[i-1]
            q_d = q[i]

            # Portées fictives Caquot (CORRECTION)
            Lf_g = max(L_g, 0.8 * L_d)   # côté gauche de l'appui i
            Lf_d = max(L_d, 0.8 * L_g)   # côté droit de l'appui i

            # Equation de 3 moments de Caquot
            # Lf_g * M[i-1] + 2*(Lf_g + Lf_d) * M[i] + Lf_d * M[i+1]
            #   = -q_g*Lf_g³/4 - q_d*Lf_d³/4
            rhs = -(q_g * Lf_g**3 / 4 + q_d * Lf_d**3 / 4)
            M[i] = (rhs - Lf_g * M[i-1] - Lf_d * M[i+1]) / (2 * (Lf_g + Lf_d))

        if all(abs(M[i] - M_old[i]) < 1e-6 for i in range(n+1)):
            break

    # Efforts tranchants et moments en travée
    V_g_list, V_d_list, M_trav_list = [], [], []

    for i in range(n):
        L  = travees[i].L
        qi = q[i]
        Mg = M[i]      # moment appui gauche (négatif)
        Md = M[i+1]    # moment appui droit (négatif)

        # Réactions (équilibre)
        V_g = qi * L / 2 - (Md - Mg) / L
        V_d = qi * L - V_g

        # Position du moment max en travée (V=0)
        x_max = V_g / qi if qi > 0 else L / 2
        x_max = max(0.0, min(L, x_max))

        # Moment max en travée
        M_trav = Mg + V_g * x_max - qi * x_max**2 / 2
        M_trav = max(M_trav, qi * L**2 / 14)   # min forfaitaire (1/14 ≈ 0.07)

        V_g_list.append(abs(V_g))
        V_d_list.append(abs(V_d))
        M_trav_list.append(M_trav)

    return M, M_trav_list, V_g_list, V_d_list


def calculer_poutre_continue(e: EntreePoutreContinue) -> ResultatPoutreContinue:
    from .materiaux import BETONS, ACIERS, ENROBAGES
    r = ResultatPoutreContinue(norme=e.norme)
    msgs = r.messages

    if not (2 <= len(e.travees) <= 5):
        msgs.append("ERREUR : nombre de travées doit être entre 2 et 5.")
        return r

    bet   = BETONS[e.beton]
    acr   = ACIERS[e.acier]
    c_nom = ENROBAGES.get(e.enrobage_classe, 25)

    fck = bet.fck
    fcd = fck / 1.5
    fyk = acr.fyk
    fyd = fyk / 1.15
    E_s = 200000.0
    E_cm = 22000 * ((fck + 8) / 10) ** 0.3

    phi_l = 20
    d = e.h - c_nom - phi_l / 2
    d = max(d, 100)
    r.d = round(d, 0)

    gamma_G, gamma_Q = 1.35, 1.50

    M_appuis, M_travees, V_g_list, V_d_list = _caquot(
        e.travees, e.appui_gauche, e.appui_droit, gamma_G, gamma_Q
    )

    rho_min = max(0.26 * 0.30 * fck**(2/3) / fyk, 0.0013)
    As_min  = rho_min * e.b * d
    r.As_min = round(As_min, 0)

    def _as_flexion(Med_kNm: float) -> float:
        d_m = d / 1000
        b_m = e.b / 1000
        if Med_kNm <= 0:
            return 0.0
        mu = Med_kNm / (b_m * d_m**2 * fcd * 1000)
        mu = min(mu, 0.372)
        alpha = (1 - math.sqrt(max(0, 1 - 2 * mu)))
        z = d_m * (1 - 0.4 * alpha)
        return Med_kNm / (z * fyd / 1000) if z > 0 else 0.0

    wk_lim = 0.3

    for i, trav in enumerate(e.travees):
        rt = ResultatTravee(numero=i+1, L=trav.L)
        q_ELU = gamma_G * trav.g_k + gamma_Q * trav.q_k
        q_ELS = trav.g_k + trav.q_k
        rt.q_ELU = round(q_ELU, 2)
        rt.q_ELS = round(q_ELS, 2)

        rt.M_trav  = round(M_travees[i], 2)
        rt.M_app_g = round(abs(M_appuis[i]),   2)
        rt.M_app_d = round(abs(M_appuis[i+1]), 2)
        rt.V_g     = round(V_g_list[i], 1)
        rt.V_d     = round(V_d_list[i], 1)

        # Armatures travée
        as_t = max(_as_flexion(rt.M_trav), As_min)
        rt.As_trav_calc = round(as_t, 0)
        rt.As_trav_retenu, rt.choix_trav = _choisir_armatures(as_t, e.b)

        # Chapeaux
        as_g = max(_as_flexion(rt.M_app_g), As_min * 0.5)
        rt.As_chap_g_calc = round(as_g, 0)
        rt.As_chap_g_retenu, rt.choix_chap_g = _choisir_armatures(as_g, e.b)

        as_d = max(_as_flexion(rt.M_app_d), As_min * 0.5)
        rt.As_chap_d_calc = round(as_d, 0)
        rt.As_chap_d_retenu, rt.choix_chap_d = _choisir_armatures(as_d, e.b)

        # Cisaillement
        V_max = max(rt.V_g, rt.V_d)
        b_m = e.b / 1000
        d_m = d / 1000
        tau_u = V_max / (b_m * d_m * 1000)
        rho_l = min(rt.As_trav_retenu / (e.b * d), 0.02)
        k_val = min(1 + math.sqrt(200 / d), 2.0)

        if e.norme == "EC2":
            VRd_c = (0.18/1.5) * k_val * (100*rho_l*fck)**(1/3) * b_m * d_m * 1000
            VRd_c = max(VRd_c, 0.035 * k_val**1.5 * math.sqrt(fck) * b_m * d_m * 1000)
        else:
            VRd_c = min((0.07+40*rho_l)*fcd*b_m*d_m*1000, 0.267*fcd*b_m*d_m*1000)

        rt.tau_u = round(tau_u, 2)
        rt.VRd_c = round(VRd_c, 1)
        rt.armatures_cis = V_max > VRd_c

        if rt.armatures_cis:
            msgs.append(f"⚠️ Travée {i+1} : cisaillement nécessite armatures transversales (V={V_max:.1f} kN > VRd,c={VRd_c:.1f} kN)")

        # Flèche
        fleche_adm = trav.L * 1000 / 500
        Ig = e.b * e.h**3 / 12
        fleche = 5/48 * q_ELS * (trav.L*1000)**4 / (E_cm * Ig) * 1e-3
        rt.fleche     = round(fleche, 1)
        rt.fleche_adm = round(fleche_adm, 1)
        rt.fleche_ok  = fleche <= fleche_adm

        if not rt.fleche_ok:
            msgs.append(f"⚠️ Travée {i+1} : flèche={fleche:.1f}mm > L/500={fleche_adm:.1f}mm")

        # Fissuration
        M_ELS = q_ELS / q_ELU * rt.M_trav if q_ELU > 0 else 0
        As_m  = rt.As_trav_retenu / 1e6
        z_els = 0.9 * d_m
        sigma_s = M_ELS / (As_m * z_els * 1000) if As_m > 0 else 0
        c_m = c_nom / 1000
        rho_eff = max(rt.As_trav_retenu / (e.b * min(2.5*(e.h-d), e.h/2)), 1e-4)
        sr_max = 3.4*c_m + 0.425*0.8*(phi_l/1000)/rho_eff
        eps_sm = max(sigma_s/E_s - 0.4*bet.fctm/(E_s*rho_eff), 0.6*sigma_s/E_s)
        wk = sr_max * eps_sm * 1000
        rt.wk = round(wk, 3)
        rt.wk_lim = wk_lim
        rt.fissuration_ok = wk <= wk_lim

        if not rt.fissuration_ok:
            msgs.append(f"⚠️ Travée {i+1} : fissuration wk={wk:.3f}mm > {wk_lim}mm")

        r.travees_res.append(rt)

    msgs.append(f"Calcul par méthode de Caquot — {len(e.travees)} travées")
    msgs.append(f"Armature minimale : {r.As_min:.0f} mm²")
    return r
