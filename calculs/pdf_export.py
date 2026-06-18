"""
Génération de notes de calcul PDF
StructAI Platform — Module 1
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import io


# ── Couleurs ────────────────────────────────────────────────────────────────
BLEU      = colors.HexColor("#1a3a5c")
BLEU_CLAIR= colors.HexColor("#2e6da4")
GRIS      = colors.HexColor("#f5f5f5")
VERT_OK   = colors.HexColor("#2e7d32")
ROUGE_ERR = colors.HexColor("#c62828")
BLANC     = colors.white


def _styles():
    s = getSampleStyleSheet()
    return {
        "titre":   ParagraphStyle("titre",   fontSize=16, textColor=BLANC,
                                   fontName="Helvetica-Bold", alignment=TA_CENTER,
                                   spaceAfter=4),
        "sous":    ParagraphStyle("sous",    fontSize=10, textColor=BLANC,
                                   fontName="Helvetica", alignment=TA_CENTER),
        "h2":      ParagraphStyle("h2",      fontSize=12, textColor=BLEU,
                                   fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4),
        "h3":      ParagraphStyle("h3",      fontSize=10, textColor=BLEU_CLAIR,
                                   fontName="Helvetica-Bold", spaceBefore=6, spaceAfter=2),
        "body":    ParagraphStyle("body",    fontSize=9,  textColor=colors.black,
                                   fontName="Helvetica",  spaceAfter=2, leading=13),
        "ok":      ParagraphStyle("ok",      fontSize=9,  textColor=VERT_OK,
                                   fontName="Helvetica-Bold"),
        "err":     ParagraphStyle("err",     fontSize=9,  textColor=ROUGE_ERR,
                                   fontName="Helvetica-Bold"),
        "footer":  ParagraphStyle("footer",  fontSize=7,  textColor=colors.grey,
                                   fontName="Helvetica", alignment=TA_CENTER),
    }


def _entete(elements, styles, titre_calc, projet="—", ingenieur="—", norme="EC2"):
    """Bandeau titre coloré"""
    data = [[Paragraph(f"StructAI — {titre_calc}", styles["titre"])],
            [Paragraph(f"Projet : {projet}  |  Ingénieur : {ingenieur}  |  Norme : {norme}  |  Date : {datetime.today().strftime('%d/%m/%Y')}", styles["sous"])]]
    t = Table(data, colWidths=[170*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), BLEU),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [BLEU, BLEU]),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 8*mm))


def _table_donnees(titre, lignes, styles):
    """Tableau de données d'entrée 2 colonnes"""
    elements = []
    elements.append(Paragraph(titre, styles["h2"]))
    data = [["Paramètre", "Valeur"]] + lignes
    t = Table(data, colWidths=[90*mm, 80*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,0),  BLEU),
        ("TEXTCOLOR",    (0,0), (-1,0),  BLANC),
        ("FONTNAME",     (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [GRIS, BLANC]),
        ("GRID",         (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))
    return elements


def _table_resultats(titre, lignes, styles):
    """Tableau de résultats 3 colonnes"""
    elements = []
    elements.append(Paragraph(titre, styles["h2"]))
    data = [["Grandeur", "Valeur", "Unité"]] + lignes
    t = Table(data, colWidths=[80*mm, 50*mm, 40*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  BLEU_CLAIR),
        ("TEXTCOLOR",     (0,0), (-1,0),  BLANC),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [GRIS, BLANC]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("ALIGN",         (1,0), (2,-1),  "CENTER"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))
    return elements


def _verification(ok: bool, texte: str, styles):
    style = styles["ok"] if ok else styles["err"]
    sym   = "✓" if ok else "✗"
    return Paragraph(f"{sym}  {texte}", style)


# ════════════════════════════════════════════════════════════════════════════
#  NOTE POUTRE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_poutre(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de poutre — Flexion simple",
            projet, ingenieur, res.norme)

    # Données d'entrée
    for e in _table_donnees("1. Données d'entrée", [
        ["Largeur b",          f"{entree.b} mm"],
        ["Hauteur h",          f"{entree.h} mm"],
        ["Portée",             f"{entree.portee} m"],
        ["Charge permanente Gk", f"{entree.g_k} kN/m"],
        ["Charge variable Qk", f"{entree.q_k} kN/m"],
        ["Béton",              entree.beton],
        ["Acier",              entree.acier],
        ["Classe exposition",  entree.enrobage_classe],
        ["Enrobage nominal c", f"{res.enrobage} mm"],
    ], st):
        els.append(e)

    # Sollicitations
    for e in _table_resultats("2. Sollicitations ELU", [
        ["Combinaison",         "1.35G + 1.50Q", "—"],
        ["Moment de calcul MEd", f"{res.MEd}",    "kN.m"],
        ["Effort tranchant VEd", f"{res.VEd}",    "kN"],
    ], st):
        els.append(e)

    # Flexion
    for e in _table_resultats("3. Calcul en flexion", [
        ["Hauteur utile d",          f"{res.d}",      "mm"],
        ["Moment réduit μ",          f"{res.mu}",     "—"],
        ["Pivot",                    res.pivot,        "—"],
        ["Position axe neutre α",    f"{res.alpha}",  "—"],
        ["Section acier calculée As", f"{res.As_calc}", "mm²"],
        ["Section acier minimale",   f"{res.As_min}", "mm²"],
        ["Section acier retenue",    f"{res.As_retenu}", "mm²"],
        ["Choix armatures",          res.choix_armatures, "—"],
    ], st):
        els.append(e)

    # Cisaillement
    for e in _table_resultats("4. Vérification au cisaillement", [
        ["Contrainte τu",        f"{res.tau_u}",  "MPa"],
        ["Résistance VRd,c",     f"{res.VRd_c}",  "kN"],
        ["Armatures cisaillement", "Oui" if res.armatures_cisaillement else "Non", "—"],
    ], st):
        els.append(e)

    # Vérifications
    els.append(Paragraph("5. Récapitulatif des vérifications", st["h2"]))
    mu_lim = 0.372 if res.norme == "EC2" else 0.186
    els.append(_verification(res.mu <= mu_lim,
               f"Section simplement armée : μ={res.mu} ≤ μlim={mu_lim}", st))
    els.append(_verification(res.As_calc >= res.As_min,
               f"Armature minimale : As_calc={res.As_calc} mm² ≥ As_min={res.As_min} mm²", st))
    els.append(_verification(not res.armatures_cisaillement,
               f"Cisaillement : VEd={res.VEd} kN {'≤' if not res.armatures_cisaillement else '>'} VRd,c={res.VRd_c} kN", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Platform — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))

    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE POTEAU
# ════════════════════════════════════════════════════════════════════════════
def generer_note_poteau(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de poteau — Compression composée",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Section b × h",        f"{entree.b} × {entree.h} mm"],
        ["Longueur",             f"{entree.longueur} m"],
        ["Conditions d'appui",   entree.conditions_appui],
        ["Effort normal Nk",     f"{entree.N_k} kN"],
        ["Moment Mk",            f"{entree.M_k} kN.m"],
        ["Béton",                entree.beton],
        ["Acier",                entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Sollicitations ELU", [
        ["Effort normal NEd",  f"{res.NEd}",      "kN"],
        ["Moment MEd",         f"{res.MEd}",       "kN.m"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Élancement", [
        ["Longueur de flambement l₀", f"{res.l0}",        "m"],
        ["Élancement λ",               f"{res.lambda_}",   "—"],
        ["Élancement limite λlim",     f"{res.lambda_lim}", "—"],
        ["Type poteau",                "Élancé" if res.elastique else "Court", "—"],
        ["Excentricité 1er ordre e₀", f"{res.e0}",        "mm"],
        ["Excentricité 2nd ordre e₂", f"{res.e2}",        "mm"],
        ["Excentricité totale etot",  f"{res.etot}",      "mm"],
        ["Moment total MEd,tot",       f"{res.MEd_tot}",   "kN.m"],
    ], st):
        els.append(e)

    for e in _table_resultats("4. Armatures", [
        ["Section calculée As",  f"{res.As_calc}",   "mm²"],
        ["Section minimale",     f"{res.As_min}",    "mm²"],
        ["Section maximale",     f"{res.As_max}",    "mm²"],
        ["Section retenue",      f"{res.As_retenu}", "mm²"],
        ["Choix armatures",      res.choix_armatures, "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("5. Vérifications", st["h2"]))
    els.append(_verification(not res.elastique or res.e2 > 0,
               f"Élancement : λ={res.lambda_} {'>' if res.elastique else '≤'} λlim={res.lambda_lim} — {'effets 2nd ordre pris en compte' if res.elastique else 'OK'}", st))
    els.append(_verification(res.As_retenu <= res.As_max,
               f"Taux d'armature : As={res.As_retenu} mm² ≤ As,max={res.As_max} mm²", st))
    els.append(_verification(res.As_retenu >= res.As_min,
               f"Armature minimale : As={res.As_retenu} mm² ≥ As,min={res.As_min} mm²", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Platform — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))

    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE SEMELLE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_semelle(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de semelle filante",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Largeur mur/voile",        f"{entree.b_mur} mm"],
        ["Hauteur semelle h",        f"{entree.h_semelle} mm"],
        ["Charge Nk",                f"{entree.N_k} kN/ml"],
        ["Moment Mk",                f"{entree.M_k} kN.m/ml"],
        ["Contrainte sol admissible", f"{entree.sigma_sol} kPa"],
        ["Béton",                    entree.beton],
        ["Acier",                    entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Dimensionnement en plan (ELS)", [
        ["Largeur minimale calculée", f"{res.B_requise}",  "m"],
        ["Largeur retenue B",         f"{res.B_retenue}",  "m"],
        ["Débord de chaque côté",     f"{res.debord}",     "mm"],
        ["Pression moyenne σmoy",     f"{res.sigma_moy}",  "kPa"],
        ["Pression maximale σmax",    f"{res.sigma_max}",  "kPa"],
        ["Contrainte admissible",     f"{entree.sigma_sol}", "kPa"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Sollicitations ELU", [
        ["Effort normal NEd",         f"{res.NEd}",           "kN/ml"],
        ["Pression ELU σELU",        f"{res.sigma_ELU}",     "kN/m²"],
        ["Moment semelle MEd",        f"{res.MEd_semelle}",   "kN.m/ml"],
        ["Effort tranchant VEd",      f"{res.VEd_semelle}",   "kN/ml"],
    ], st):
        els.append(e)

    for e in _table_resultats("4. Armatures", [
        ["As transversal calculé",  f"{res.As_trans_calc}",   "mm²/ml"],
        ["As transversal minimum",  f"{res.As_trans_min}",    "mm²/ml"],
        ["As transversal retenu",   f"{res.As_trans_retenu}", "mm²/ml"],
        ["Choix transversal",       res.choix_trans,           "—"],
        ["As longitudinal minimum", f"{res.As_long_min}",     "mm²/ml"],
        ["Choix longitudinal",      res.choix_long,            "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("5. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok,
               f"Pression sol : σmax={res.sigma_max} kPa {'≤' if res.sigma_ok else '>'} σadm={entree.sigma_sol} kPa", st))
    els.append(_verification(res.debord >= 150,
               f"Débord minimal 150 mm : débord={res.debord} mm", st))
    els.append(_verification(res.As_trans_retenu >= res.As_trans_min,
               f"Armature minimale : As={res.As_trans_retenu} mm²/ml ≥ As,min={res.As_trans_min} mm²/ml", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Platform — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))

    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE RADIER GÉNÉRAL
# ════════════════════════════════════════════════════════════════════════════
def generer_note_radier(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de radier général — Dalle pleine",
            projet, ingenieur, entree.norme)

    # 1. Données d'entrée
    for e in _table_donnees("1. Données d'entrée", [
        ["Longueur Lx",                   f"{entree.Lx} m"],
        ["Largeur Ly",                    f"{entree.Ly} m"],
        ["Épaisseur",                     f"{entree.epaisseur} mm"],
        ["Débord périphérique",           f"{entree.debord} mm"],
        ["Charge totale Nk",              f"{entree.N_k} kN"],
        ["Moment Mkx",                    f"{entree.M_kx} kN.m"],
        ["Moment Mky",                    f"{entree.M_ky} kN.m"],
        ["Contrainte sol admissible",     f"{entree.sigma_sol} kPa"],
        ["Module de réaction ks",         f"{entree.ks} kN/m³"],
        ["% charges permanentes",         f"{int(entree.pct_G * 100)} %"],
        ["Béton",                         entree.beton],
        ["Acier",                         entree.acier],
        ["Classe d'exposition",           entree.enrobage_classe],
    ], st):
        els.append(e)

    # 2. Géométrie retenue
    for e in _table_resultats("2. Géométrie retenue", [
        ["Longueur totale Lx (avec débords)", f"{res.Lx_retenu}",  "m"],
        ["Largeur totale Ly (avec débords)",  f"{res.Ly_retenu}",  "m"],
        ["Surface totale",                    f"{res.surface}",    "m²"],
        ["Poids propre radier",               f"{res.poids_propre}", "kN"],
        ["Rapport Lx/Ly",                     f"{round(res.Lx_retenu/res.Ly_retenu, 2)}", "—"],
    ], st):
        els.append(e)

    # 3. Pression sur sol ELS
    for e in _table_resultats("3. Pression sur sol (ELS)", [
        ["Effort normal total NEd ELS",  f"{round(entree.N_k + res.poids_propre, 1)}", "kN"],
        ["Excentricité ex",              f"{res.ex}",         "m"],
        ["Excentricité ey",              f"{res.ey}",         "m"],
        ["Pression moyenne σmoy",        f"{res.sigma_moy}",  "kPa"],
        ["Pression maximale σmax",       f"{res.sigma_max}",  "kPa"],
        ["Pression minimale σmin",       f"{res.sigma_min}",  "kPa"],
        ["Contrainte admissible σadm",   f"{entree.sigma_sol}", "kPa"],
    ], st):
        els.append(e)

    # 4. Longueurs élastiques
    for e in _table_resultats("4. Longueurs élastiques (modèle Winkler)", [
        ["Longueur élastique x",  f"{res.l_elastique_x}", "m"],
        ["Longueur élastique y",  f"{res.l_elastique_y}", "m"],
        ["Module de réaction ks", f"{entree.ks}",         "kN/m³"],
    ], st):
        els.append(e)

    # 5. Sollicitations ELU
    for e in _table_resultats("5. Sollicitations ELU (méthode forfaitaire)", [
        ["Effort normal NEd ELU",     f"{res.NEd}",          "kN"],
        ["MEd travée direction x",    f"{res.MEd_x_trav}",   "kN.m/ml"],
        ["MEd travée direction y",    f"{res.MEd_y_trav}",   "kN.m/ml"],
        ["MEd appui direction x",     f"{res.MEd_x_app}",    "kN.m/ml"],
        ["MEd appui direction y",     f"{res.MEd_y_app}",    "kN.m/ml"],
    ], st):
        els.append(e)

    # 6. Armatures
    for e in _table_resultats("6. Armatures (4 nappes)", [
        ["As x inf calculé",     f"{res.As_x_inf_calc}",   "mm²/ml"],
        ["As x inf minimum",     f"{res.As_x_inf_min}",    "mm²/ml"],
        ["As x inf retenu",      f"{res.As_x_inf_retenu}", "mm²/ml"],
        ["Choix nappe x inf",    res.choix_x_inf,           "—"],
        ["As y inf calculé",     f"{res.As_y_inf_calc}",   "mm²/ml"],
        ["As y inf minimum",     f"{res.As_y_inf_min}",    "mm²/ml"],
        ["As y inf retenu",      f"{res.As_y_inf_retenu}", "mm²/ml"],
        ["Choix nappe y inf",    res.choix_y_inf,           "—"],
        ["As x sup calculé",     f"{res.As_x_sup_calc}",   "mm²/ml"],
        ["As x sup retenu",      f"{res.As_x_sup_retenu}", "mm²/ml"],
        ["Choix nappe x sup",    res.choix_x_sup,           "—"],
        ["As y sup calculé",     f"{res.As_y_sup_calc}",   "mm²/ml"],
        ["As y sup retenu",      f"{res.As_y_sup_retenu}", "mm²/ml"],
        ["Choix nappe y sup",    res.choix_y_sup,           "—"],
    ], st):
        els.append(e)

    # 7. Vérifications
    els.append(Paragraph("7. Récapitulatif des vérifications", st["h2"]))
    els.append(_verification(
        res.sigma_ok,
        f"Pression sol : σmax={res.sigma_max} kPa {'≤' if res.sigma_ok else '>'} σadm={entree.sigma_sol} kPa", st))
    els.append(_verification(
        res.sigma_min >= 0,
        f"Pas de décollement : σmin={res.sigma_min} kPa {'≥' if res.sigma_min >= 0 else '<'} 0", st))
    els.append(_verification(
        res.lx_ly_ok,
        f"Rapport Lx/Ly={round(res.Lx_retenu/res.Ly_retenu, 2)} {'≤' if res.lx_ly_ok else '>'} 2.0 (dalle bidirectionnelle)", st))
    els.append(_verification(
        res.As_x_inf_retenu >= res.As_x_inf_min,
        f"Armature minimale x : As_inf={res.As_x_inf_retenu} mm²/ml ≥ As,min={res.As_x_inf_min} mm²/ml", st))
    els.append(_verification(
        res.As_y_inf_retenu >= res.As_y_inf_min,
        f"Armature minimale y : As_inf={res.As_y_inf_retenu} mm²/ml ≥ As,min={res.As_y_inf_min} mm²/ml", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Platform — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))

    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE DALLE PLEINE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_dalle(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de dalle pleine — Flexion bidirectionnelle",
            projet, ingenieur, entree.norme)

    # 1. Données
    for e in _table_donnees("1. Données d'entrée", [
        ["Petit côté Lx",              f"{entree.Lx} m"],
        ["Grand côté Ly",              f"{entree.Ly} m"],
        ["Épaisseur",                  f"{entree.epaisseur} mm"],
        ["Appui rive x=0",             entree.appui_x1],
        ["Appui rive x=Lx",            entree.appui_x2],
        ["Appui rive y=0",             entree.appui_y1],
        ["Appui rive y=Ly",            entree.appui_y2],
        ["Charge permanente Gk",       f"{entree.g_k} kN/m²"],
        ["Charge variable Qk",         f"{entree.q_k} kN/m²"],
        ["Classe fissuration",         entree.classe_fissuration],
        ["Béton",                      entree.beton],
        ["Acier",                      entree.acier],
        ["Enrobage",                   entree.enrobage_classe],
    ], st):
        els.append(e)

    # 2. Type et chargement
    for e in _table_resultats("2. Type et chargement ELU", [
        ["Type de dalle",   "Bidirectionnelle" if res.bidirectionnelle else "Unidirectionnelle", "—"],
        ["ρ = Lx/Ly",       f"{res.rho}", "—"],
        ["Hauteur utile dx", f"{res.d_x}", "mm"],
        ["Hauteur utile dy", f"{res.d_y}", "mm"],
        ["Charge ELU",      f"{res.q_ELU}", "kN/m²"],
        ["Charge ELS",      f"{res.q_ELS}", "kN/m²"],
    ], st):
        els.append(e)

    # 3. Moments ELU
    for e in _table_resultats("3. Moments ELU — Méthode Marcus", [
        ["Mx travée",  f"{res.Mx_trav}", "kN.m/ml"],
        ["My travée",  f"{res.My_trav}", "kN.m/ml"],
        ["Mx appui",   f"{res.Mx_app}",  "kN.m/ml"],
        ["My appui",   f"{res.My_app}",  "kN.m/ml"],
    ], st):
        els.append(e)

    # 4. Armatures
    for e in _table_resultats("4. Armatures (4 nappes)", [
        ["As x inf calculé",   f"{res.As_x_inf_calc}",   "mm²/ml"],
        ["As x inf minimum",   f"{res.As_x_inf_min}",    "mm²/ml"],
        ["As x inf retenu",    f"{res.As_x_inf_retenu}", "mm²/ml"],
        ["Choix x inf",        res.choix_x_inf,           "—"],
        ["As y inf calculé",   f"{res.As_y_inf_calc}",   "mm²/ml"],
        ["As y inf minimum",   f"{res.As_y_inf_min}",    "mm²/ml"],
        ["As y inf retenu",    f"{res.As_y_inf_retenu}", "mm²/ml"],
        ["Choix y inf",        res.choix_y_inf,           "—"],
        ["As x sup retenu",    f"{res.As_x_sup_retenu}", "mm²/ml"],
        ["Choix x sup",        res.choix_x_sup,           "—"],
        ["As y sup retenu",    f"{res.As_y_sup_retenu}", "mm²/ml"],
        ["Choix y sup",        res.choix_y_sup,           "—"],
    ], st):
        els.append(e)

    # 5. ELS
    for e in _table_resultats("5. Vérifications ELS", [
        ["Flèche admissible L/250",  f"{res.fleche_admissible}", "mm"],
        ["Flèche calculée",          f"{res.fleche_calculee}",   "mm"],
        ["wk,x (fissuration)",       f"{res.wk_x}",             "mm"],
        ["wk,y (fissuration)",       f"{res.wk_y}",             "mm"],
        ["wk,lim",                   f"{res.wk_lim}",           "mm"],
        ["σc béton ELS",             f"{res.sigma_c}",          "MPa"],
        ["σs acier ELS",             f"{res.sigma_s}",          "MPa"],
    ], st):
        els.append(e)

    # 6. Vérifications
    els.append(Paragraph("6. Récapitulatif des vérifications", st["h2"]))
    els.append(_verification(res.fleche_ok,
        f"Flèche : {res.fleche_calculee} mm {'≤' if res.fleche_ok else '>'} {res.fleche_admissible} mm (L/250)", st))
    els.append(_verification(res.fissuration_ok,
        f"Fissuration : wk,x={res.wk_x} mm, wk,y={res.wk_y} mm ≤ wk,lim={res.wk_lim} mm", st))
    els.append(_verification(res.bidirectionnelle,
        f"Dalle bidirectionnelle : ρ={res.rho} {'≥' if res.bidirectionnelle else '<'} 0.4", st))
    els.append(_verification(
        res.As_x_inf_retenu >= res.As_x_inf_min,
        f"Armature min x : {res.As_x_inf_retenu} mm²/ml ≥ {res.As_x_inf_min} mm²/ml", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Platform — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))

    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE POUTRE CONTINUE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_poutre_continue(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, f"Calcul de poutre continue — {len(entree.travees)} travées — Méthode Caquot",
            projet, ingenieur, entree.norme)

    # 1. Données
    donnees = [
        ["Section b × h",          f"{entree.b} × {entree.h} mm"],
        ["Hauteur utile d",         f"{res.d} mm"],
        ["Appui gauche",            entree.appui_gauche],
        ["Appui droit",             entree.appui_droit],
        ["Béton",                   entree.beton],
        ["Acier",                   entree.acier],
        ["Armature minimale",       f"{res.As_min} mm²"],
    ]
    for i, t in enumerate(entree.travees):
        donnees.append([f"Travée {i+1} — L / Gk / Qk", f"{t.L} m / {t.g_k} kN/m / {t.q_k} kN/m"])

    for e in _table_donnees("1. Données d'entrée", donnees, st):
        els.append(e)

    # 2. Résultats par travée
    for rt in res.travees_res:
        for e in _table_resultats(f"2.{rt.numero} Travée {rt.numero} — L={rt.L}m", [
            ["Charge ELU",          f"{rt.q_ELU}",        "kN/m"],
            ["Charge ELS",          f"{rt.q_ELS}",        "kN/m"],
            ["M travée ELU",        f"{rt.M_trav}",       "kN.m"],
            ["M appui gauche",      f"{rt.M_app_g}",      "kN.m"],
            ["M appui droit",       f"{rt.M_app_d}",      "kN.m"],
            ["V gauche",            f"{rt.V_g}",          "kN"],
            ["V droit",             f"{rt.V_d}",          "kN"],
            ["As travée calculé",   f"{rt.As_trav_calc}", "mm²"],
            ["As travée retenu",    f"{rt.As_trav_retenu}","mm²"],
            ["Choix travée",        rt.choix_trav,         "—"],
            ["Chapeau gauche",      rt.choix_chap_g,       "—"],
            ["Chapeau droit",       rt.choix_chap_d,       "—"],
            ["τu cisaillement",     f"{rt.tau_u}",        "MPa"],
            ["VRd,c",               f"{rt.VRd_c}",        "kN"],
            ["Armatures cis.",      "OUI ⚠️" if rt.armatures_cis else "NON ✅", "—"],
            ["Flèche calculée",     f"{rt.fleche}",       "mm"],
            ["Flèche admissible",   f"{rt.fleche_adm}",   "mm"],
            ["wk fissuration",      f"{rt.wk}",           "mm"],
        ], st):
            els.append(e)

    # 3. Vérifications globales
    els.append(Paragraph("3. Récapitulatif des vérifications", st["h2"]))
    for rt in res.travees_res:
        els.append(_verification(rt.fleche_ok,
            f"Travée {rt.numero} — Flèche : {rt.fleche}mm ≤ {rt.fleche_adm}mm (L/500)", st))
        els.append(_verification(rt.fissuration_ok,
            f"Travée {rt.numero} — Fissuration : wk={rt.wk}mm ≤ {rt.wk_lim}mm", st))
        els.append(_verification(not rt.armatures_cis,
            f"Travée {rt.numero} — Cisaillement béton seul : V={max(rt.V_g,rt.V_d):.1f}kN {'≤' if not rt.armatures_cis else '>'} VRd,c={rt.VRd_c:.1f}kN", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Platform — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))

    doc.build(els)
    return buf.getvalue()
