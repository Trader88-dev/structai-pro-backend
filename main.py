from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
