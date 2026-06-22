"""
StructAI Pro — Backend FastAPI
Lancement : uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

from calculs import (
    BETONS, ACIERS, ENROBAGES,
    EntreePoutre, calculer_poutre,
    EntreePoteau, calculer_poteau,
    EntreeSemelle, calculer_semelle,
    EntreeRadier, calculer_radier,
    EntreeDalle, calculer_dalle,
    EntreePoutreContinue, Travee, calculer_poutre_continue,
    EntreeVoile, calculer_voile,
    EntreeEscalier, calculer_escalier,
    EntreeLinteau, calculer_linteau,
    EntreeSemIsolee, calculer_semelle_isolee,
    EntreeAcrotere, calculer_acrotere,
    EntreeMurSoutenement, calculer_mur_soutenement,
)

app = FastAPI(title="StructAI Pro API", version="1.0.0")

# ── CORS — autoriser React (port 3000) à appeler le backend ─────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://structai-pro.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route de test ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "app": "StructAI Pro API", "version": "1.0.0"}

@app.get("/materiaux")
def get_materiaux():
    return {
        "betons":   list(BETONS.keys()),
        "aciers":   list(ACIERS.keys()),
        "enrobages": list(ENROBAGES.keys()),
    }

# ── Modèles Pydantic ──────────────────────────────────────────────────────────

class PoutreRequest(BaseModel):
    b: float
    h: float
    portee: float
    g_k: float
    q_k: float
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

class PoteauRequest(BaseModel):
    b: float
    h: float
    longueur: float
    N_k: float
    M_k: float
    pct_G: float = 0.7
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"
    conditions_appui: str = "encastre-rotule"

class SemelleRequest(BaseModel):
    b_mur: float
    h_semelle: float
    N_k: float
    M_k: float = 0.0
    sigma_sol: float
    beton: str = "C25/30"
    acier: str = "B500B"
    norme: str = "EC2"
    pct_G: float = 0.7

class RadierRequest(BaseModel):
    Lx: float
    Ly: float
    epaisseur: float
    debord: float = 300
    N_k: float
    M_kx: float = 0.0
    M_ky: float = 0.0
    sigma_sol: float
    ks: float = 30000
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"
    pct_G: float = 0.7

class DalleRequest(BaseModel):
    Lx: float
    Ly: float
    epaisseur: float
    appui_x1: str = "appuye"
    appui_x2: str = "appuye"
    appui_y1: str = "appuye"
    appui_y2: str = "appuye"
    g_k: float
    q_k: float
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"
    classe_fissuration: str = "XC1"

class TraveeModel(BaseModel):
    L: float
    g_k: float
    q_k: float

class PoutreContinueRequest(BaseModel):
    b: float
    h: float
    travees: List[TraveeModel]
    appui_gauche: str = "appuye"
    appui_droit: str = "appuye"
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

# ── Routes calcul ─────────────────────────────────────────────────────────────

@app.post("/calcul/poutre")
def calc_poutre(req: PoutreRequest):
    try:
        entree = EntreePoutre(**req.dict())
        res = calculer_poutre(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/poteau")
def calc_poteau(req: PoteauRequest):
    try:
        entree = EntreePoteau(**req.dict())
        res = calculer_poteau(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/semelle")
def calc_semelle(req: SemelleRequest):
    try:
        entree = EntreeSemelle(**req.dict())
        res = calculer_semelle(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/radier")
def calc_radier(req: RadierRequest):
    try:
        entree = EntreeRadier(**req.dict())
        res = calculer_radier(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/dalle")
def calc_dalle(req: DalleRequest):
    try:
        entree = EntreeDalle(**req.dict())
        res = calculer_dalle(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/poutre-continue")
def calc_poutre_continue(req: PoutreContinueRequest):
    try:
        travees = [Travee(L=t.L, g_k=t.g_k, q_k=t.q_k) for t in req.travees]
        data = req.dict()
        data.pop("travees")
        entree = EntreePoutreContinue(travees=travees, **data)
        res = calculer_poutre_continue(entree)
        # Sérialiser les travées
        result = {
            "norme": res.norme,
            "d": res.d,
            "As_min": res.As_min,
            "messages": res.messages,
            "travees_res": [t.__dict__ for t in res.travees_res],
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# ── Routes calculs supplémentaires ───────────────────────────────────────────

class VoileRequest(BaseModel):
    L: float
    h: float
    e: float
    appui: str = "encastre-rotule"
    N_k: float = 500.0
    M_k: float = 50.0
    V_k: float = 20.0
    pct_G: float = 0.7
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

class EscalierRequest(BaseModel):
    L_h: float = 3.0
    hauteur: float = 2.7
    g_giron: float = 0.28
    h_contre: float = 0.17
    ep: float = 150
    g_k: float = 6.0
    q_k: float = 2.5
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

class LinteauRequest(BaseModel):
    b: float = 200
    h: float = 300
    L: float = 1.5
    g_k: float = 10.0
    q_k: float = 5.0
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

class SemelleIsoleeRequest(BaseModel):
    b_p: float = 300
    h_p: float = 300
    h_sem: float = 500
    N_k: float = 800.0
    M_kx: float = 0.0
    M_ky: float = 0.0
    sigma_sol: float = 200.0
    pct_G: float = 0.7
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

class AcrotereRequest(BaseModel):
    h: float = 0.80
    e: float = 150
    g_k: float = 3.5
    q_vent: float = 1.0
    zone_sismique: str = "2"
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC1"
    norme: str = "EC2"

class MurSoutenementRequest(BaseModel):
    H: float = 3.0
    e_voile: float = 250
    B_semelle: float = 2.0
    e_semelle: float = 400
    d_encastrement: float = 0.5
    gamma_terre: float = 18.0
    phi_deg: float = 30.0
    delta_deg: float = 0.0
    q_surcharge: float = 10.0
    sigma_sol: float = 200.0
    mu_glissement: float = 0.5
    beton: str = "C25/30"
    acier: str = "B500B"
    enrobage_classe: str = "XC2"
    norme: str = "EC2"

@app.post("/calcul/voile")
def calc_voile(req: VoileRequest):
    try:
        entree = EntreeVoile(**req.dict())
        res = calculer_voile(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/escalier")
def calc_escalier(req: EscalierRequest):
    try:
        entree = EntreeEscalier(**req.dict())
        res = calculer_escalier(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/linteau")
def calc_linteau(req: LinteauRequest):
    try:
        entree = EntreeLinteau(**req.dict())
        res = calculer_linteau(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/semelle-isolee")
def calc_semelle_isolee(req: SemelleIsoleeRequest):
    try:
        entree = EntreeSemIsolee(**req.dict())
        res = calculer_semelle_isolee(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/acrotere")
def calc_acrotere(req: AcrotereRequest):
    try:
        entree = EntreeAcrotere(**req.dict())
        res = calculer_acrotere(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/calcul/mur-soutenement")
def calc_mur_soutenement(req: MurSoutenementRequest):
    try:
        entree = EntreeMurSoutenement(**req.dict())
        res = calculer_mur_soutenement(entree)
        return res.__dict__
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Routes IA ─────────────────────────────────────────────────────────────────
from fastapi import UploadFile, File, Form
import anthropic as anthropic_lib
import base64

def get_ai_client():
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise HTTPException(status_code=400, detail="Clé API Anthropic introuvable")
    return anthropic_lib.Anthropic(api_key=key)

SYSTEM_PROMPT = """Tu es StructAI, un ingénieur structural expert en béton armé, spécialisé EC2 et BAEL 91.
Réponds toujours en français, de façon structurée et professionnelle.
Pour les calculs, propose des valeurs numériques concrètes.
Pour les vérifications, classe par niveau : 🔴 CRITIQUE / 🟠 AVERTISSEMENT / 🟢 OK."""

class ChatRequest(BaseModel):
    messages: list
    norme: str = "EC2"
    beton: str = "C25/30"
    acier: str = "B500B"

class AnalyseRequest(BaseModel):
    element: str
    donnees: dict
    resultats: dict

@app.post("/ia/chat")
def ia_chat(req: ChatRequest):
    client = get_ai_client()
    system = f"{SYSTEM_PROMPT}\nNorme: {req.norme} | Béton: {req.beton} | Acier: {req.acier}"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system,
        messages=req.messages,
    )
    return {"response": response.content[0].text}

@app.post("/ia/analyser")
def ia_analyser(req: AnalyseRequest):
    client = get_ai_client()
    prompt = f"""Analyse ces résultats de calcul pour un {req.element} :
Données : {req.donnees}
Résultats : {req.resultats}

Fournis :
1. Commentaire sur les résultats (normal/attention/critique)
2. Anomalies détectées avec niveau 🔴/🟠/🟢
3. Suggestions d'optimisation si pertinent
4. Conclusion en 1 phrase"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return {"commentaire": response.content[0].text}

@app.post("/ia/lecture-plan")
async def ia_lecture_plan(
    file: UploadFile = File(...),
    mode: str = Form("Extraction automatique des dimensions"),
    norme: str = Form("EC2"),
    beton: str = Form("C25/30"),
    acier: str = Form("B500B"),
):
    client = get_ai_client()
    file_bytes = await file.read()
    b64 = base64.standard_b64encode(file_bytes).decode()
    media_type = file.content_type or "image/jpeg"

    prompts = {
        "Extraction automatique des dimensions": "Extrait toutes les dimensions (b, h, portées en mm et m) dans un tableau clair.",
        "Lecture du ferraillage": "Extrait tous les aciers (nombre×diamètre, espacements, sections mm²) par élément.",
        "Analyse complète (coffrage + ferraillage)": "Analyse complète : dimensions + ferraillage + matériaux + cartouche.",
        "Vérification et détection d'erreurs": "Vérifie la conformité EC2/BAEL et liste les anomalies par niveau 🔴/🟠/🟢.",
    }

    prompt = f"Norme: {norme} | Béton: {beton} | Acier: {acier}\n\n{prompts.get(mode, prompts['Extraction automatique des dimensions'])}"

    if media_type == "application/pdf":
        content = [{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":b64}},{"type":"text","text":prompt}]
    else:
        content = [{"type":"image","source":{"type":"base64","media_type":media_type,"data":b64}},{"type":"text","text":prompt}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role":"user","content":content}],
    )
    return {"analyse": response.content[0].text}
