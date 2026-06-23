# ════════════════════════════════════════════════════════════════════════════
#  NOTE VOILE BA
# ════════════════════════════════════════════════════════════════════════════
def generer_note_voile(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de voile BA — Flexion composée",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Longueur L",              f"{entree.L} m"],
        ["Hauteur h",               f"{entree.h} m"],
        ["Épaisseur e",             f"{entree.e} mm"],
        ["Conditions d'appui",      entree.appui],
        ["Effort normal Nk",        f"{entree.N_k} kN"],
        ["Moment Mk",               f"{entree.M_k} kN.m"],
        ["Effort tranchant Vk",     f"{entree.V_k} kN"],
        ["Béton",                   entree.beton],
        ["Acier",                   entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Élancement", [
        ["Hauteur utile d",         f"{res.d}",          "mm"],
        ["Longueur de flambement l₀", f"{res.l0}",       "m"],
        ["Élancement λ",            f"{res.lambda_}",    "—"],
        ["Élancement limite λlim",  f"{res.lambda_lim}", "—"],
        ["Type voile",              "Élancé" if res.elance else "Court", "—"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Efforts ELU", [
        ["NEd",                     f"{res.NEd}",        "kN"],
        ["MEd 1er ordre",           f"{res.MEd}",        "kN.m"],
        ["VEd",                     f"{res.VEd}",        "kN"],
        ["Excentricité 1er ordre e₀", f"{res.e0}",       "mm"],
        ["Excentricité 2nd ordre e₂", f"{res.e2}",       "mm"],
        ["Excentricité totale etot", f"{res.etot}",       "mm"],
        ["Moment total MEd,tot",    f"{res.MEd_tot}",    "kN.m"],
    ], st):
        els.append(e)

    for e in _table_resultats("4. Armatures", [
        ["As vertical calculé",     f"{res.As_vert_calc}",   "mm²"],
        ["As vertical minimum",     f"{res.As_vert_min}",    "mm²"],
        ["As vertical maximum",     f"{res.As_vert_max}",    "mm²"],
        ["As vertical retenu",      f"{res.As_vert_retenu}", "mm²/ml/nappe"],
        ["Choix vertical",          res.choix_vert,           "—"],
        ["As horizontal minimum",   f"{res.As_horiz_min}",   "mm²/ml"],
        ["As horizontal retenu",    f"{res.As_horiz_retenu}", "mm²/ml"],
        ["Choix horizontal",        res.choix_horiz,          "—"],
        ["As about calculé",        f"{res.As_about_calc}",  "mm²"],
        ["As about retenu",         f"{res.As_about_retenu}", "mm²"],
        ["Choix about",             res.choix_about,          "—"],
    ], st):
        els.append(e)

    for e in _table_resultats("5. Cisaillement", [
        ["Contrainte τu",           f"{res.tau_u}",      "MPa"],
        ["Résistance VRd,c",        f"{res.VRd_c}",      "kN"],
        ["Vérification",            "✅ OK" if res.cisaillement_ok else "❌ NON", "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("6. Récapitulatif des vérifications", st["h2"]))
    els.append(_verification(not res.elance, f"Voile court : λ={res.lambda_} ≤ λlim={res.lambda_lim}", st))
    els.append(_verification(res.cisaillement_ok, f"Cisaillement : VEd={res.VEd} kN ≤ VRd,c={res.VRd_c} kN", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))
    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE ESCALIER
# ════════════════════════════════════════════════════════════════════════════
def generer_note_escalier(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul d'escalier BA — Flexion simple",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Longueur horizontale L_h",    f"{entree.L_h} m"],
        ["Hauteur totale",              f"{entree.hauteur} m"],
        ["Giron",                       f"{entree.g_giron} m"],
        ["Hauteur contre-marche",       f"{entree.h_contre} m"],
        ["Épaisseur paillasse",         f"{entree.ep} mm"],
        ["Charge permanente Gk",        f"{entree.g_k} kN/m²"],
        ["Charge variable Qk",          f"{entree.q_k} kN/m²"],
        ["Béton",                       entree.beton],
        ["Acier",                       entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Géométrie et sollicitations", [
        ["Angle inclinaison α",         f"{res.alpha_deg}",  "°"],
        ["Longueur inclinée",           f"{res.L_inclinee}", "m"],
        ["Hauteur utile d",             f"{res.d}",          "mm"],
        ["Charge ELU",                  f"{res.q_ELU}",      "kN/m²"],
        ["Moment MEd",                  f"{res.MEd}",        "kN.m"],
        ["Effort tranchant VEd",        f"{res.VEd}",        "kN"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Armatures", [
        ["As principales calculé",      f"{res.As_princ_calc}",   "mm²/ml"],
        ["As principales minimum",      f"{res.As_princ_min}",    "mm²/ml"],
        ["As principales retenu",       f"{res.As_princ_retenu}", "mm²/ml"],
        ["Choix armatures principales", res.choix_princ,           "—"],
        ["As répartition retenu",       f"{res.As_rep_retenu}",   "mm²/ml"],
        ["Choix répartition",           res.choix_rep,             "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("4. Vérifications", st["h2"]))
    els.append(_verification(res.fleche_ok, f"Flèche : fléche calculée={res.fleche_calc} mm ≤ adm={res.fleche_adm} mm", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))
    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE LINTEAU
# ════════════════════════════════════════════════════════════════════════════
def generer_note_linteau(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de linteau BA — Flexion simple",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Largeur b",               f"{entree.b} mm"],
        ["Hauteur h",               f"{entree.h} mm"],
        ["Portée L",                f"{entree.L} m"],
        ["Charge permanente Gk",    f"{entree.g_k} kN/m"],
        ["Charge variable Qk",      f"{entree.q_k} kN/m"],
        ["Béton",                   entree.beton],
        ["Acier",                   entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Sollicitations ELU", [
        ["Hauteur utile d",         f"{res.d}",       "mm"],
        ["Moment MEd",              f"{res.MEd}",     "kN.m"],
        ["Effort tranchant VEd",    f"{res.VEd}",     "kN"],
        ["Moment réduit μ",         f"{res.mu}",      "—"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Armatures", [
        ["As calculé",              f"{res.As_calc}",   "mm²"],
        ["As minimum",              f"{res.As_min}",    "mm²"],
        ["As retenu",               f"{res.As_retenu}", "mm²"],
        ["Choix armatures",         res.choix,           "—"],
    ], st):
        els.append(e)

    for e in _table_resultats("4. Cisaillement", [
        ["Contrainte τu",           f"{res.tau_u}",  "MPa"],
        ["Résistance VRd,c",        f"{res.VRd_c}",  "kN"],
        ["Cadres nécessaires",      "OUI ⚠️" if res.armatures_cis else "NON ✅", "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("5. Vérifications", st["h2"]))
    mu_lim = 0.372 if res.norme == "EC2" else 0.186
    els.append(_verification(res.mu <= mu_lim, f"Section simplement armée : μ={res.mu} ≤ {mu_lim}", st))
    els.append(_verification(not res.armatures_cis, f"Cisaillement béton seul : VEd={res.VEd} kN ≤ VRd,c={res.VRd_c} kN", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))
    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE SEMELLE ISOLÉE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_semelle_isolee(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de semelle isolée — Sous poteau",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Section poteau b×h",      f"{entree.b_p}×{entree.h_p} mm"],
        ["Hauteur semelle",         f"{entree.h_sem} mm"],
        ["Charge normale Nk",       f"{entree.N_k} kN"],
        ["Moment Mkx",              f"{entree.M_kx} kN.m"],
        ["Moment Mky",              f"{entree.M_ky} kN.m"],
        ["Contrainte sol admissible", f"{entree.sigma_sol} kPa"],
        ["Béton",                   entree.beton],
        ["Acier",                   entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Dimensionnement en plan", [
        ["Dimension Ax",            f"{res.Ax}",         "m"],
        ["Dimension Ay",            f"{res.Ay}",         "m"],
        ["Surface",                 f"{res.surface}",    "m²"],
        ["Hauteur utile d",         f"{res.d}",          "mm"],
        ["Pression moyenne σmoy",   f"{res.sigma_moy}",  "kPa"],
        ["Pression maximale σmax",  f"{res.sigma_max}",  "kPa"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Armatures", [
        ["As x calculé",            f"{res.As_x_calc}",   "mm²/ml"],
        ["As x minimum",            f"{res.As_x_min}",    "mm²/ml"],
        ["As x retenu",             f"{res.As_x_retenu}", "mm²/ml"],
        ["Choix x",                 res.choix_x,           "—"],
        ["As y calculé",            f"{res.As_y_calc}",   "mm²/ml"],
        ["As y retenu",             f"{res.As_y_retenu}", "mm²/ml"],
        ["Choix y",                 res.choix_y,           "—"],
    ], st):
        els.append(e)

    for e in _table_resultats("4. Poinçonnement", [
        ["Périmètre critique u1",   f"{res.perimetre_crit}", "m"],
        ["VEd poinçonnement",       f"{res.VEd_poinc}",     "kN"],
        ["VRd,c poinçonnement",     f"{res.VRd_c_poinc}",   "kN"],
        ["Vérification",            "✅ OK" if res.poinconnement_ok else "❌ NON", "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("5. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok, f"Pression sol : σmax={res.sigma_max} kPa ≤ σadm={entree.sigma_sol} kPa", st))
    els.append(_verification(res.poinconnement_ok, f"Poinçonnement : VEd={res.VEd_poinc} kN ≤ VRd,c={res.VRd_c_poinc} kN", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))
    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE ACROTÈRE
# ════════════════════════════════════════════════════════════════════════════
def generer_note_acrotere(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul d'acrotère BA — Flexion composée + séisme",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Hauteur acrotère h",      f"{entree.h} m"],
        ["Épaisseur e",             f"{entree.e} mm"],
        ["Charge permanente Gk",    f"{entree.g_k} kN/ml"],
        ["Pression vent",           f"{entree.q_vent} kN/m²"],
        ["Zone sismique",           entree.zone_sismique],
        ["Béton",                   entree.beton],
        ["Acier",                   entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Efforts ELU", [
        ["NEd vent",                f"{res.NEd_vent}",   "kN"],
        ["MEd vent",                f"{res.MEd_vent}",   "kN.m"],
        ["NEd sismique",            f"{res.NEd_seis}",   "kN"],
        ["MEd sismique",            f"{res.MEd_seis}",   "kN.m"],
        ["Cas dimensionnant",       res.cas_dim,          "—"],
        ["NEd retenu",              f"{res.NEd}",        "kN"],
        ["MEd retenu",              f"{res.MEd}",        "kN.m"],
        ["Excentricité totale",     f"{res.etot}",       "mm"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Armatures", [
        ["Hauteur utile d",         f"{res.d}",              "mm"],
        ["As calculé",              f"{res.As_calc}",        "mm²/ml"],
        ["As minimum",              f"{res.As_min}",         "mm²/ml"],
        ["As retenu",               f"{res.As_retenu}",      "mm²/ml"],
        ["Choix principal",         res.choix,                "—"],
        ["As répartition",          f"{res.As_rep_retenu}",  "mm²/ml"],
        ["Choix répartition",       res.choix_rep,            "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("4. Vérifications", st["h2"]))
    els.append(_verification(res.sigma_ok, f"Contrainte béton encastrement : {res.sigma_beton} MPa ≤ 0.6fck", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))
    doc.build(els)
    return buf.getvalue()


# ════════════════════════════════════════════════════════════════════════════
#  NOTE MUR DE SOUTÈNEMENT
# ════════════════════════════════════════════════════════════════════════════
def generer_note_mur_soutenement(entree, res, projet="—", ingenieur="—") -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    st = _styles()
    els = []

    _entete(els, st, "Calcul de mur de soutènement BA",
            projet, ingenieur, res.norme)

    for e in _table_donnees("1. Données d'entrée", [
        ["Hauteur totale H",            f"{entree.H} m"],
        ["Épaisseur voile",             f"{entree.e_voile} mm"],
        ["Largeur semelle B",           f"{entree.B_semelle} m"],
        ["Épaisseur semelle",           f"{entree.e_semelle} mm"],
        ["Profondeur encastrement",     f"{entree.d_encastrement} m"],
        ["Poids volumique terre γ",     f"{entree.gamma_terre} kN/m³"],
        ["Angle frottement interne φ",  f"{entree.phi_deg}°"],
        ["Surcharge derrière mur",      f"{entree.q_surcharge} kN/m²"],
        ["Contrainte sol admissible",   f"{entree.sigma_sol} kPa"],
        ["Béton",                       entree.beton],
        ["Acier",                       entree.acier],
    ], st):
        els.append(e)

    for e in _table_resultats("2. Poussée des terres", [
        ["Coefficient Ka",              f"{res.Ka}",    "—"],
        ["Poussée active Ea",           f"{res.Ea}",    "kN/ml"],
        ["Poussée surcharge Eq",        f"{res.Eq}",    "kN/ml"],
    ], st):
        els.append(e)

    for e in _table_resultats("3. Stabilité", [
        ["Coefficient glissement Fg",   f"{res.stabilite_glissement}",   "≥ 1.5"],
        ["Coefficient renversement Fr", f"{res.stabilite_renversement}", "≥ 2.0"],
        ["Pression sol σmax",           f"{res.sigma_max}",              "kPa"],
        ["Pression sol σmin",           f"{res.sigma_min}",              "kPa"],
    ], st):
        els.append(e)

    for e in _table_resultats("4. Ferraillage voile", [
        ["As voile calculé",            f"{res.As_voile_calc}",   "mm²/ml"],
        ["As voile retenu",             f"{res.As_voile_retenu}", "mm²/ml"],
        ["Choix voile vertical",        res.choix_voile,           "—"],
        ["As voile horizontal",         f"{res.As_voile_horiz}",  "mm²/ml"],
        ["Choix voile horizontal",      res.choix_voile_horiz,     "—"],
    ], st):
        els.append(e)

    for e in _table_resultats("5. Ferraillage talon semelle", [
        ["As talon calculé",            f"{res.As_talon_calc}",   "mm²/ml"],
        ["As talon retenu",             f"{res.As_talon_retenu}", "mm²/ml"],
        ["Choix talon",                 res.choix_talon,           "—"],
    ], st):
        els.append(e)

    els.append(Paragraph("6. Récapitulatif des vérifications", st["h2"]))
    els.append(_verification(res.glissement_ok, f"Glissement : Fg={res.stabilite_glissement} ≥ 1.5", st))
    els.append(_verification(res.renversement_ok, f"Renversement : Fr={res.stabilite_renversement} ≥ 2.0", st))
    els.append(_verification(res.portance_ok, f"Portance : σmax={res.sigma_max} kPa ≤ σadm={entree.sigma_sol} kPa", st))

    els.append(Spacer(1, 6*mm))
    for msg in res.messages:
        els.append(Paragraph(f"→ {msg}", st["body"]))

    els.append(Spacer(1, 8*mm))
    els.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    els.append(Spacer(1, 3*mm))
    els.append(Paragraph("Note générée par StructAI Pro — Usage professionnel — Vérifier conformité réglementaire locale", st["footer"]))
    doc.build(els)
    return buf.getvalue()
