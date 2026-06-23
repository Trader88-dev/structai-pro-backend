"""
Génération de notes de calcul PDF
StructAI Platform — Tous modules
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
    data = [[Paragraph(f"StructAI Pro — {titre_calc}", styles["titre"])],
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
    sym   = "OK" if ok else "NON"
    return Paragraph(f"[{sym}]  {texte}", style)


def _footer(els, st):
    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))


# ════════════════════════════════════════════════════════════════════════════
#  NOTE POUTRE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_poutre(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de poutre — Flexion simple", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Largeur b", f"{entree.b} mm"], ["Hauteur h", f"{entree.h} mm"],
        ["Portée", f"{entree.portee} m"], ["Charge permanente Gk", f"{entree.g_k} kN/m"],
        ["Charge variable Qk", f"{entree.q_k} kN/m"], ["Béton", entree.beton],
        ["Acier", entree.acier], ["Enrobage nominal c", f"{res.enrobage} mm"],
    ], st): els.append(e)
    for e in _table_resultats("2. Sollicitations ELU", [
        ["Combinaison", "1.35G + 1.50Q", "—"],
        ["Moment de calcul MEd", f"{res.MEd}", "kN.m"],
        ["Effort tranchant VEd", f"{res.VEd}", "kN"],
    ], st): els.append(e)
    for e in _table_resultats("3. Calcul en flexion", [
        ["Hauteur utile d", f"{res.d}", "mm"], ["Moment réduit μ", f"{res.mu}", "—"],
        ["Pivot", res.pivot, "—"], ["Position axe neutre α", f"{res.alpha}", "—"],
        ["Section acier calculée As", f"{res.As_calc}", "mm²"],
        ["Section acier minimale", f"{res.As_min}", "mm²"],
        ["Section acier retenue", f"{res.As_retenu}", "mm²"],
        ["Choix armatures", res.choix_armatures, "—"],
    ], st): els.append(e)
    for e in _table_resultats("4. Cisaillement", [
        ["Contrainte τu", f"{res.tau_u}", "MPa"], ["Résistance VRd,c", f"{res.VRd_c}", "kN"],
        ["Armatures cisaillement", "Oui" if res.armatures_cisaillement else "Non", "—"],
    ], st): els.append(e)
    els.append(Paragraph("5. Vérifications", st["h2"]))
    mu_lim = 0.372 if res.norme == "EC2" else 0.186
    els.append(_verification(res.mu <= mu_lim, f"Section simplement armée : μ={res.mu} ≤ μlim={mu_lim}", st))
    els.append(_verification(res.As_calc >= res.As_min, f"Armature minimale : As={res.As_calc} mm² ≥ As_min={res.As_min} mm²", st))
    els.append(_verification(not res.armatures_cisaillement, f"Cisaillement : VEd={res.VEd} kN ≤ VRd,c={res.VRd_c} kN", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE POTEAU
# ════════════════════════════════════════════════════════════════════════════
def generer_note_poteau(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de poteau — Compression composée", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Section b × h", f"{entree.b} × {entree.h} mm"], ["Longueur", f"{entree.longueur} m"],
        ["Conditions d'appui", entree.conditions_appui], ["Effort normal Nk", f"{entree.N_k} kN"],
        ["Moment Mk", f"{entree.M_k} kN.m"], ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Sollicitations ELU", [
        ["Effort normal NEd", f"{res.NEd}", "kN"], ["Moment MEd", f"{res.MEd}", "kN.m"],
    ], st): els.append(e)
    for e in _table_resultats("3. Élancement", [
        ["Longueur de flambement l₀", f"{res.l0}", "m"], ["Élancement λ", f"{res.lambda_}", "—"],
        ["Élancement limite λlim", f"{res.lambda_lim}", "—"],
        ["Type poteau", "Élancé" if res.elastique else "Court", "—"],
        ["Excentricité totale etot", f"{res.etot}", "mm"], ["Moment total MEd,tot", f"{res.MEd_tot}", "kN.m"],
    ], st): els.append(e)
    for e in _table_resultats("4. Armatures", [
        ["Section calculée As", f"{res.As_calc}", "mm²"], ["Section minimale", f"{res.As_min}", "mm²"],
        ["Section maximale", f"{res.As_max}", "mm²"], ["Section retenue", f"{res.As_retenu}", "mm²"],
        ["Choix armatures", res.choix_armatures, "—"],
    ], st): els.append(e)
    els.append(Paragraph("5. Vérifications", st["h2"]))
    els.append(_verification(res.As_retenu <= res.As_max, f"Taux d'armature : As={res.As_retenu} mm² ≤ As,max={res.As_max} mm²", st))
    els.append(_verification(res.As_retenu >= res.As_min, f"Armature minimale : As={res.As_retenu} mm² ≥ As,min={res.As_min} mm²", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE SEMELLE FILANTE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_semelle(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de semelle filante", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Largeur mur/voile", f"{entree.b_mur} mm"], ["Hauteur semelle h", f"{entree.h_semelle} mm"],
        ["Charge Nk", f"{entree.N_k} kN/ml"], ["Moment Mk", f"{entree.M_k} kN.m/ml"],
        ["Contrainte sol admissible", f"{entree.sigma_sol} kPa"],
        ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Dimensionnement en plan (ELS)", [
        ["Largeur minimale calculée", f"{res.B_requise}", "m"], ["Largeur retenue B", f"{res.B_retenue}", "m"],
        ["Débord de chaque côté", f"{res.debord}", "mm"], ["Pression moyenne σmoy", f"{res.sigma_moy}", "kPa"],
        ["Pression maximale σmax", f"{res.sigma_max}", "kPa"],
    ], st): els.append(e)
    for e in _table_resultats("3. Armatures", [
        ["As transversal calculé", f"{res.As_trans_calc}", "mm²/ml"],
        ["As transversal retenu", f"{res.As_trans_retenu}", "mm²/ml"],
        ["Choix transversal", res.choix_trans, "—"],
        ["Choix longitudinal", res.choix_long, "—"],
    ], st): els.append(e)
    els.append(Paragraph("4. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok, f"Pression sol : σmax={res.sigma_max} kPa ≤ σadm={entree.sigma_sol} kPa", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE RADIER
# ════════════════════════════════════════════════════════════════════════════
def generer_note_radier(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de radier général — Dalle pleine", projet, ingenieur, entree.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Longueur Lx", f"{entree.Lx} m"], ["Largeur Ly", f"{entree.Ly} m"],
        ["Épaisseur", f"{entree.epaisseur} mm"], ["Charge totale Nk", f"{entree.N_k} kN"],
        ["Contrainte sol admissible", f"{entree.sigma_sol} kPa"],
        ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Pression sur sol (ELS)", [
        ["Pression moyenne σmoy", f"{res.sigma_moy}", "kPa"],
        ["Pression maximale σmax", f"{res.sigma_max}", "kPa"],
        ["Pression minimale σmin", f"{res.sigma_min}", "kPa"],
    ], st): els.append(e)
    for e in _table_resultats("3. Armatures", [
        ["As x inf retenu", f"{res.As_x_inf_retenu}", "mm²/ml"], ["Choix x inf", res.choix_x_inf, "—"],
        ["As y inf retenu", f"{res.As_y_inf_retenu}", "mm²/ml"], ["Choix y inf", res.choix_y_inf, "—"],
        ["As x sup retenu", f"{res.As_x_sup_retenu}", "mm²/ml"], ["Choix x sup", res.choix_x_sup, "—"],
        ["As y sup retenu", f"{res.As_y_sup_retenu}", "mm²/ml"], ["Choix y sup", res.choix_y_sup, "—"],
    ], st): els.append(e)
    els.append(Paragraph("4. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok, f"Pression sol : σmax={res.sigma_max} kPa ≤ σadm={entree.sigma_sol} kPa", st))
    els.append(_verification(res.sigma_min >= 0, f"Pas de décollement : σmin={res.sigma_min} kPa ≥ 0", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE DALLE PLEINE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_dalle(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de dalle pleine — Flexion bidirectionnelle", projet, ingenieur, entree.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Petit côté Lx", f"{entree.Lx} m"], ["Grand côté Ly", f"{entree.Ly} m"],
        ["Épaisseur", f"{entree.epaisseur} mm"], ["Charge permanente Gk", f"{entree.g_k} kN/m²"],
        ["Charge variable Qk", f"{entree.q_k} kN/m²"], ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Type et chargement ELU", [
        ["Type de dalle", "Bidirectionnelle" if res.bidirectionnelle else "Unidirectionnelle", "—"],
        ["Charge ELU", f"{res.q_ELU}", "kN/m²"],
    ], st): els.append(e)
    for e in _table_resultats("3. Moments ELU", [
        ["Mx travée", f"{res.Mx_trav}", "kN.m/ml"], ["My travée", f"{res.My_trav}", "kN.m/ml"],
        ["Mx appui", f"{res.Mx_app}", "kN.m/ml"], ["My appui", f"{res.My_app}", "kN.m/ml"],
    ], st): els.append(e)
    for e in _table_resultats("4. Armatures", [
        ["As x inf retenu", f"{res.As_x_inf_retenu}", "mm²/ml"], ["Choix x inf", res.choix_x_inf, "—"],
        ["As y inf retenu", f"{res.As_y_inf_retenu}", "mm²/ml"], ["Choix y inf", res.choix_y_inf, "—"],
    ], st): els.append(e)
    els.append(Paragraph("5. Vérifications", st["h2"]))
    els.append(_verification(res.fleche_ok, f"Flèche : {res.fleche_calculee} mm ≤ {res.fleche_admissible} mm", st))
    els.append(_verification(res.fissuration_ok, f"Fissuration : wk={res.wk_x} mm ≤ wk,lim={res.wk_lim} mm", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE POUTRE CONTINUE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_poutre_continue(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, f"Calcul de poutre continue — {len(entree.travees)} travées", projet, ingenieur, entree.norme)
    donnees = [["Section b × h", f"{entree.b} × {entree.h} mm"], ["Béton", entree.beton], ["Acier", entree.acier]]
    for i, t in enumerate(entree.travees):
        donnees.append([f"Travée {i+1} — L / Gk / Qk", f"{t.L} m / {t.g_k} kN/m / {t.q_k} kN/m"])
    for e in _table_donnees("1. Données d'entrée", donnees, st): els.append(e)
    for rt in res.travees_res:
        for e in _table_resultats(f"2.{rt.numero} Travée {rt.numero} — L={rt.L}m", [
            ["Charge ELU", f"{rt.q_ELU}", "kN/m"], ["M travée ELU", f"{rt.M_trav}", "kN.m"],
            ["As travée retenu", f"{rt.As_trav_retenu}", "mm²"], ["Choix travée", rt.choix_trav, "—"],
        ], st): els.append(e)
    els.append(Paragraph("3. Vérifications", st["h2"]))
    for rt in res.travees_res:
        els.append(_verification(rt.fleche_ok, f"Travée {rt.numero} — Flèche : {rt.fleche}mm ≤ {rt.fleche_adm}mm", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE VOILE BA
# ════════════════════════════════════════════════════════════════════════════
def generer_note_voile(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de voile BA — Flexion composée", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Longueur L", f"{entree.L} m"], ["Hauteur h", f"{entree.h} m"],
        ["Épaisseur e", f"{entree.e} mm"], ["Conditions d'appui", entree.appui],
        ["Effort normal Nk", f"{entree.N_k} kN"], ["Moment Mk", f"{entree.M_k} kN.m"],
        ["Effort tranchant Vk", f"{entree.V_k} kN"], ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Élancement", [
        ["Hauteur utile d", f"{res.d}", "mm"], ["Longueur de flambement l0", f"{res.l0}", "m"],
        ["Élancement lambda", f"{res.lambda_}", "—"], ["Élancement limite lambda_lim", f"{res.lambda_lim}", "—"],
        ["Type voile", "Élancé" if res.elance else "Court", "—"],
    ], st): els.append(e)
    for e in _table_resultats("3. Efforts ELU", [
        ["NEd", f"{res.NEd}", "kN"], ["MEd", f"{res.MEd}", "kN.m"], ["VEd", f"{res.VEd}", "kN"],
        ["Excentricité e0", f"{res.e0}", "mm"], ["Excentricité e2", f"{res.e2}", "mm"],
        ["Excentricité totale etot", f"{res.etot}", "mm"], ["Moment total MEd_tot", f"{res.MEd_tot}", "kN.m"],
    ], st): els.append(e)
    for e in _table_resultats("4. Armatures", [
        ["As vertical calculé", f"{res.As_vert_calc}", "mm²"],
        ["As vertical minimum", f"{res.As_vert_min}", "mm²"],
        ["As vertical retenu", f"{res.As_vert_retenu}", "mm²/ml/nappe"],
        ["Choix vertical", res.choix_vert, "—"],
        ["As horizontal retenu", f"{res.As_horiz_retenu}", "mm²/ml"],
        ["Choix horizontal", res.choix_horiz, "—"],
        ["As about retenu", f"{res.As_about_retenu}", "mm²"],
        ["Choix about", res.choix_about, "—"],
    ], st): els.append(e)
    for e in _table_resultats("5. Cisaillement", [
        ["Contrainte tau_u", f"{res.tau_u}", "MPa"], ["Résistance VRd_c", f"{res.VRd_c}", "kN"],
        ["Vérification", "OK" if res.cisaillement_ok else "NON VERIFIE", "—"],
    ], st): els.append(e)
    els.append(Paragraph("6. Vérifications", st["h2"]))
    els.append(_verification(not res.elance, f"Voile court : lambda={res.lambda_} ≤ lambda_lim={res.lambda_lim}", st))
    els.append(_verification(res.cisaillement_ok, f"Cisaillement : VEd={res.VEd} kN ≤ VRd_c={res.VRd_c} kN", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE ESCALIER
# ════════════════════════════════════════════════════════════════════════════
def generer_note_escalier(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul d'escalier BA — Flexion simple", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Longueur horizontale L_h", f"{entree.L_h} m"], ["Hauteur totale", f"{entree.hauteur} m"],
        ["Giron", f"{entree.g_giron} m"], ["Hauteur contre-marche", f"{entree.h_contre} m"],
        ["Épaisseur paillasse", f"{entree.ep} mm"], ["Charge permanente Gk", f"{entree.g_k} kN/m²"],
        ["Charge variable Qk", f"{entree.q_k} kN/m²"], ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Géométrie et sollicitations", [
        ["Angle inclinaison alpha", f"{res.alpha_deg}", "°"], ["Longueur inclinée", f"{res.L_inclinee}", "m"],
        ["Hauteur utile d", f"{res.d}", "mm"], ["Charge ELU", f"{res.q_ELU}", "kN/m²"],
        ["Moment MEd", f"{res.MEd}", "kN.m"], ["Effort tranchant VEd", f"{res.VEd}", "kN"],
    ], st): els.append(e)
    for e in _table_resultats("3. Armatures", [
        ["As principales calculé", f"{res.As_princ_calc}", "mm²/ml"],
        ["As principales retenu", f"{res.As_princ_retenu}", "mm²/ml"],
        ["Choix armatures principales", res.choix_princ, "—"],
        ["As répartition retenu", f"{res.As_rep_retenu}", "mm²/ml"],
        ["Choix répartition", res.choix_rep, "—"],
    ], st): els.append(e)
    els.append(Paragraph("4. Vérifications", st["h2"]))
    els.append(_verification(res.fleche_ok, f"Flèche : {res.fleche_calc} mm ≤ {res.fleche_adm} mm", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE LINTEAU
# ════════════════════════════════════════════════════════════════════════════
def generer_note_linteau(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de linteau BA — Flexion simple", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Largeur b", f"{entree.b} mm"], ["Hauteur h", f"{entree.h} mm"],
        ["Portée L", f"{entree.L} m"], ["Charge permanente Gk", f"{entree.g_k} kN/m"],
        ["Charge variable Qk", f"{entree.q_k} kN/m"], ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Sollicitations ELU", [
        ["Hauteur utile d", f"{res.d}", "mm"], ["Moment MEd", f"{res.MEd}", "kN.m"],
        ["Effort tranchant VEd", f"{res.VEd}", "kN"], ["Moment réduit mu", f"{res.mu}", "—"],
    ], st): els.append(e)
    for e in _table_resultats("3. Armatures", [
        ["As calculé", f"{res.As_calc}", "mm²"], ["As minimum", f"{res.As_min}", "mm²"],
        ["As retenu", f"{res.As_retenu}", "mm²"], ["Choix armatures", res.choix, "—"],
    ], st): els.append(e)
    for e in _table_resultats("4. Cisaillement", [
        ["Contrainte tau_u", f"{res.tau_u}", "MPa"], ["Résistance VRd_c", f"{res.VRd_c}", "kN"],
        ["Cadres nécessaires", "OUI" if res.armatures_cis else "NON", "—"],
    ], st): els.append(e)
    els.append(Paragraph("5. Vérifications", st["h2"]))
    mu_lim = 0.372 if res.norme == "EC2" else 0.186
    els.append(_verification(res.mu <= mu_lim, f"Section simplement armée : mu={res.mu} ≤ {mu_lim}", st))
    els.append(_verification(not res.armatures_cis, f"Cisaillement béton seul : VEd={res.VEd} kN ≤ VRd_c={res.VRd_c} kN", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE SEMELLE ISOLÉE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_semelle_isolee(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de semelle isolée — Sous poteau", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Section poteau b×h", f"{entree.b_p}×{entree.h_p} mm"], ["Hauteur semelle", f"{entree.h_sem} mm"],
        ["Charge normale Nk", f"{entree.N_k} kN"], ["Contrainte sol admissible", f"{entree.sigma_sol} kPa"],
        ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Dimensionnement en plan", [
        ["Dimension Ax", f"{res.Ax}", "m"], ["Dimension Ay", f"{res.Ay}", "m"],
        ["Surface", f"{res.surface}", "m²"], ["Hauteur utile d", f"{res.d}", "mm"],
        ["Pression moyenne sigma_moy", f"{res.sigma_moy}", "kPa"],
        ["Pression maximale sigma_max", f"{res.sigma_max}", "kPa"],
    ], st): els.append(e)
    for e in _table_resultats("3. Armatures", [
        ["As x calculé", f"{res.As_x_calc}", "mm²/ml"], ["As x retenu", f"{res.As_x_retenu}", "mm²/ml"],
        ["Choix x", res.choix_x, "—"], ["As y calculé", f"{res.As_y_calc}", "mm²/ml"],
        ["As y retenu", f"{res.As_y_retenu}", "mm²/ml"], ["Choix y", res.choix_y, "—"],
    ], st): els.append(e)
    for e in _table_resultats("4. Poinçonnement", [
        ["Périmètre critique u1", f"{res.perimetre_crit}", "m"],
        ["VEd poinçonnement", f"{res.VEd_poinc}", "kN"],
        ["VRd_c poinçonnement", f"{res.VRd_c_poinc}", "kN"],
    ], st): els.append(e)
    els.append(Paragraph("5. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok, f"Pression sol : sigma_max={res.sigma_max} kPa ≤ sigma_adm={entree.sigma_sol} kPa", st))
    els.append(_verification(res.poinconnement_ok, f"Poinçonnement : VEd={res.VEd_poinc} kN ≤ VRd_c={res.VRd_c_poinc} kN", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE ACROTÈRE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_acrotere(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul d'acrotère BA — Flexion composée + séisme", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Hauteur acrotère h", f"{entree.h} m"], ["Épaisseur e", f"{entree.e} mm"],
        ["Charge permanente Gk", f"{entree.g_k} kN/ml"], ["Pression vent", f"{entree.q_vent} kN/m²"],
        ["Zone sismique", entree.zone_sismique], ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Efforts ELU", [
        ["NEd vent", f"{res.NEd_vent}", "kN"], ["MEd vent", f"{res.MEd_vent}", "kN.m"],
        ["NEd sismique", f"{res.NEd_seis}", "kN"], ["MEd sismique", f"{res.MEd_seis}", "kN.m"],
        ["Cas dimensionnant", res.cas_dim, "—"], ["NEd retenu", f"{res.NEd}", "kN"],
        ["MEd retenu", f"{res.MEd}", "kN.m"], ["Excentricité totale", f"{res.etot}", "mm"],
    ], st): els.append(e)
    for e in _table_resultats("3. Armatures", [
        ["Hauteur utile d", f"{res.d}", "mm"], ["As calculé", f"{res.As_calc}", "mm²/ml"],
        ["As minimum", f"{res.As_min}", "mm²/ml"], ["As retenu", f"{res.As_retenu}", "mm²/ml"],
        ["Choix principal", res.choix, "—"], ["As répartition", f"{res.As_rep_retenu}", "mm²/ml"],
        ["Choix répartition", res.choix_rep, "—"],
    ], st): els.append(e)
    els.append(Paragraph("4. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok, f"Contrainte béton encastrement : {res.sigma_beton} MPa ≤ 0.6fck", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE MUR DE SOUTÈNEMENT
# ════════════════════════════════════════════════════════════════════════════
def generer_note_mur_soutenement(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm)
    st = _styles(); els = []
    _entete(els, st, "Calcul de mur de soutènement BA", projet, ingenieur, res.norme)
    for e in _table_donnees("1. Données d'entrée", [
        ["Hauteur totale H", f"{entree.H} m"], ["Épaisseur voile", f"{entree.e_voile} mm"],
        ["Largeur semelle B", f"{entree.B_semelle} m"], ["Épaisseur semelle", f"{entree.e_semelle} mm"],
        ["Poids volumique terre gamma", f"{entree.gamma_terre} kN/m³"],
        ["Angle frottement phi", f"{entree.phi_deg}°"],
        ["Surcharge derrière mur", f"{entree.q_surcharge} kN/m²"],
        ["Contrainte sol admissible", f"{entree.sigma_sol} kPa"],
        ["Béton", entree.beton], ["Acier", entree.acier],
    ], st): els.append(e)
    for e in _table_resultats("2. Poussée des terres", [
        ["Coefficient Ka", f"{res.Ka}", "—"], ["Poussée active Ea", f"{res.Ea}", "kN/ml"],
        ["Poussée surcharge Eq", f"{res.Eq}", "kN/ml"],
    ], st): els.append(e)
    for e in _table_resultats("3. Stabilité", [
        ["Coefficient glissement Fg", f"{res.stabilite_glissement}", "≥ 1.5"],
        ["Coefficient renversement Fr", f"{res.stabilite_renversement}", "≥ 2.0"],
        ["Pression sol sigma_max", f"{res.sigma_max}", "kPa"],
        ["Pression sol sigma_min", f"{res.sigma_min}", "kPa"],
    ], st): els.append(e)
    for e in _table_resultats("4. Ferraillage voile", [
        ["As voile calculé", f"{res.As_voile_calc}", "mm²/ml"],
        ["As voile retenu", f"{res.As_voile_retenu}", "mm²/ml"],
        ["Choix voile vertical", res.choix_voile, "—"],
        ["As voile horizontal", f"{res.As_voile_horiz}", "mm²/ml"],
        ["Choix voile horizontal", res.choix_voile_horiz, "—"],
    ], st): els.append(e)
    for e in _table_resultats("5. Ferraillage talon semelle", [
        ["As talon calculé", f"{res.As_talon_calc}", "mm²/ml"],
        ["As talon retenu", f"{res.As_talon_retenu}", "mm²/ml"],
        ["Choix talon", res.choix_talon, "—"],
    ], st): els.append(e)
    els.append(Paragraph("6. Vérifications", st["h2"]))
    els.append(_verification(res.glissement_ok, f"Glissement : Fg={res.stabilite_glissement} ≥ 1.5", st))
    els.append(_verification(res.renversement_ok, f"Renversement : Fr={res.stabilite_renversement} ≥ 2.0", st))
    els.append(_verification(res.portance_ok, f"Portance : sigma_max={res.sigma_max} kPa ≤ sigma_adm={entree.sigma_sol} kPa", st))
    els.append(Spacer(1, 6*mm))
    for msg in res.messages: els.append(Paragraph(f"→ {msg}", st["body"]))
    _footer(els, st); doc.build(els); return buf.getvalue()
