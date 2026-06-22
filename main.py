from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
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
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=system_prompt,
        messages=messages,
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
