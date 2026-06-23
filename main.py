from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import anthropic
from calculs import (
    BETONS, ACIERS, ENROBAGES,
    EntreePoutre, calculer_poutre,
    EntreePoteau, calculer_poteau,
    EntreeSemelle, calculer_semelle,
    EntreeRadier, calculer_radier,
    EntreeDalle, calculer_dalle,
    EntreePoutreContinue, Travee, calculer_poutre_continue,
    EntreeEscalier, calculer_escalier,
    EntreeLinteau, calculer_linteau,
    EntreeSemIsolee, calculer_semelle_isolee,
    EntreeAcrotere, calculer_acrotere,
    EntreeMurSoutenement, calculer_mur_soutenement,
)
from calculs.voile import EntreeVoile, calculer_voile
from calculs.pdf_export import (
    generer_note_poutre, generer_note_poteau, generer_note_semelle,
    generer_note_radier, generer_note_dalle, generer_note_poutre_continue,
    generer_note_voile, generer_note_escalier, generer_note_linteau,
    generer_note_semelle_isolee, generer_note_acrotere, generer_note_mur_soutenement,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.structaipro.com",
        "https://structaipro.com",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# Assistant IA
# -----------------------
class IAMessage(BaseModel):
    role: str
    content: str

class IAChatRequest(BaseModel):
    messages: List[IAMessage]
    norme: str = "EC2"
    beton: str = "C25/30"
    acier: str = "B500B"

@app.post("/ia/chat")
def ia_chat(req: IAChatRequest):
    client = anthropic.Anthropic()
    system_prompt = f"""Tu es un ingénieur structure expert en béton armé.
Tu travailles avec la norme {req.norme}, béton {req.beton}, acier {req.acier}.
Tu réponds en français, de manière précise et professionnelle.
Tu peux faire des calculs, optimiser des sections, comparer des variantes, détecter des anomalies et rédiger des notes de calcul.
Utilise des formules et des chiffres concrets dans tes réponses."""
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    response = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=1500,
        system=system_prompt, messages=messages,
    )
    return {"response": response.content[0].text}

# -----------------------
# Endpoints calcul
# -----------------------
@app.get("/")
def home():
    return {"status": "ok"}

@app.post("/calcul/poutre")
def api_poutre(req: EntreePoutre):
    return calculer_poutre(req)

@app.post("/calcul/poteau")
def api_poteau(req: EntreePoteau):
    return calculer_poteau(req)

@app.post("/calcul/semelle")
def api_semelle(req: EntreeSemelle):
    return calculer_semelle(req)

@app.post("/calcul/radier")
def api_radier(req: EntreeRadier):
    return calculer_radier(req)

@app.post("/calcul/dalle")
def api_dalle(req: EntreeDalle):
    return calculer_dalle(req)

@app.post("/calcul/poutre-continue")
def api_poutre_continue(req: EntreePoutreContinue):
    return calculer_poutre_continue(req)

@app.post("/calcul/voile")
def api_voile(req: EntreeVoile):
    return calculer_voile(req)

@app.post("/calcul/escalier")
def api_escalier(req: EntreeEscalier):
    return calculer_escalier(req)

@app.post("/calcul/linteau")
def api_linteau(req: EntreeLinteau):
    return calculer_linteau(req)

@app.post("/calcul/semelle-isolee")
def api_semelle_isolee(req: EntreeSemIsolee):
    return calculer_semelle_isolee(req)

@app.post("/calcul/acrotere")
def api_acrotere(req: EntreeAcrotere):
    return calculer_acrotere(req)

@app.post("/calcul/mur-soutenement")
def api_mur_soutenement(req: EntreeMurSoutenement):
    return calculer_mur_soutenement(req)

# -----------------------
# Helper PDF
# -----------------------
def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'}
    )

def _clean(data: dict, fields: list, extra: dict = {}) -> dict:
    """Garde uniquement les champs valides + applique les extras"""
    result = {k: v for k, v in data.items() if k in fields}
    result.update(extra)
    return result

POUTRE_FIELDS = [f for f in EntreePoutre.__dataclass_fields__]
POTEAU_FIELDS = [f for f in EntreePoteau.__dataclass_fields__]
SEMELLE_FIELDS = [f for f in EntreeSemelle.__dataclass_fields__]
RADIER_FIELDS = [f for f in EntreeRadier.__dataclass_fields__]
DALLE_FIELDS = [f for f in EntreeDalle.__dataclass_fields__]
VOILE_FIELDS = [f for f in EntreeVoile.__dataclass_fields__]
ESCALIER_FIELDS = [f for f in EntreeEscalier.__dataclass_fields__]
LINTEAU_FIELDS = [f for f in EntreeLinteau.__dataclass_fields__]
SEMISOLEE_FIELDS = [f for f in EntreeSemIsolee.__dataclass_fields__]
ACROTERE_FIELDS = [f for f in EntreeAcrotere.__dataclass_fields__]
MUR_FIELDS = [f for f in EntreeMurSoutenement.__dataclass_fields__]

# -----------------------
# Endpoints PDF
# -----------------------
@app.post("/pdf/poutre")
def pdf_poutre(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    if "portee" not in data and "L" in data:
        data["portee"] = data["L"]
    entree = EntreePoutre(**_clean(data, POUTRE_FIELDS))
    res = calculer_poutre(entree)
    return _pdf_response(generer_note_poutre(entree, res, projet, ingenieur), f"note_poutre_{projet}")

@app.post("/pdf/poteau")
def pdf_poteau(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    if "pct_G" in data and data["pct_G"] > 1:
        data["pct_G"] = data["pct_G"] / 100
    entree = EntreePoteau(**_clean(data, POTEAU_FIELDS))
    res = calculer_poteau(entree)
    return _pdf_response(generer_note_poteau(entree, res, projet, ingenieur), f"note_poteau_{projet}")

@app.post("/pdf/semelle")
def pdf_semelle(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    if "pct_G" in data and data["pct_G"] > 1:
        data["pct_G"] = data["pct_G"] / 100
    entree = EntreeSemelle(**_clean(data, SEMELLE_FIELDS))
    res = calculer_semelle(entree)
    return _pdf_response(generer_note_semelle(entree, res, projet, ingenieur), f"note_semelle_{projet}")

@app.post("/pdf/radier")
def pdf_radier(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    if "pct_G" in data and data["pct_G"] > 1:
        data["pct_G"] = data["pct_G"] / 100
    entree = EntreeRadier(**_clean(data, RADIER_FIELDS))
    res = calculer_radier(entree)
    return _pdf_response(generer_note_radier(entree, res, projet, ingenieur), f"note_radier_{projet}")

@app.post("/pdf/dalle")
def pdf_dalle(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    entree = EntreeDalle(**_clean(data, DALLE_FIELDS))
    res = calculer_dalle(entree)
    return _pdf_response(generer_note_dalle(entree, res, projet, ingenieur), f"note_dalle_{projet}")

@app.post("/pdf/poutre-continue")
def pdf_poutre_continue(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    travees_raw = data.get("travees", [])
    travees = [Travee(**t) for t in travees_raw]
    entree = EntreePoutreContinue(
        b=data.get("b", 200), h=data.get("h", 500),
        appui_gauche=data.get("appui_gauche", "appuye"),
        appui_droit=data.get("appui_droit", "appuye"),
        beton=data.get("beton", "C25/30"), acier=data.get("acier", "B500B"),
        enrobage_classe=data.get("enrobage_classe", "XC1"),
        norme=data.get("norme", "EC2"), travees=travees,
    )
    res = calculer_poutre_continue(entree)
    return _pdf_response(generer_note_poutre_continue(entree, res, projet, ingenieur), f"note_poutre_continue_{projet}")

@app.post("/pdf/voile")
def pdf_voile(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    if "pct_G" in data and data["pct_G"] > 1:
        data["pct_G"] = data["pct_G"] / 100
    entree = EntreeVoile(**_clean(data, VOILE_FIELDS))
    res = calculer_voile(entree)
    return _pdf_response(generer_note_voile(entree, res, projet, ingenieur), f"note_voile_{projet}")

@app.post("/pdf/escalier")
def pdf_escalier(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    entree = EntreeEscalier(**_clean(data, ESCALIER_FIELDS))
    res = calculer_escalier(entree)
    return _pdf_response(generer_note_escalier(entree, res, projet, ingenieur), f"note_escalier_{projet}")

@app.post("/pdf/linteau")
def pdf_linteau(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    entree = EntreeLinteau(**_clean(data, LINTEAU_FIELDS))
    res = calculer_linteau(entree)
    return _pdf_response(generer_note_linteau(entree, res, projet, ingenieur), f"note_linteau_{projet}")

@app.post("/pdf/semelle-isolee")
def pdf_semelle_isolee(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    if "pct_G" in data and data["pct_G"] > 1:
        data["pct_G"] = data["pct_G"] / 100
    entree = EntreeSemIsolee(**_clean(data, SEMISOLEE_FIELDS))
    res = calculer_semelle_isolee(entree)
    return _pdf_response(generer_note_semelle_isolee(entree, res, projet, ingenieur), f"note_semelle_isolee_{projet}")

@app.post("/pdf/acrotere")
def pdf_acrotere(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    entree = EntreeAcrotere(**_clean(data, ACROTERE_FIELDS))
    res = calculer_acrotere(entree)
    return _pdf_response(generer_note_acrotere(entree, res, projet, ingenieur), f"note_acrotere_{projet}")

@app.post("/pdf/mur-soutenement")
def pdf_mur_soutenement(data: Dict[str, Any] = Body(...)):
    projet = data.pop("projet", "Projet")
    ingenieur = data.pop("ingenieur", "Ingénieur")
    entree = EntreeMurSoutenement(**_clean(data, MUR_FIELDS))
    res = calculer_mur_soutenement(entree)
    return _pdf_response(generer_note_mur_soutenement(entree, res, projet, ingenieur), f"note_mur_soutenement_{projet}")
