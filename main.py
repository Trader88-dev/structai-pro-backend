from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
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
    generer_note_poutre,
    generer_note_poteau,
    generer_note_semelle,
    generer_note_radier,
    generer_note_dalle,
    generer_note_poutre_continue,
    generer_note_voile,
    generer_note_escalier,
    generer_note_linteau,
    generer_note_semelle_isolee,
    generer_note_acrotere,
    generer_note_mur_soutenement,
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

# -----------------------
# Endpoints PDF
# -----------------------
class PDFMeta(BaseModel):
    projet: str = "Projet"
    ingenieur: str = "Ingénieur"

class PoutrePDFRequest(EntreePoutre, PDFMeta): pass
class PoteauPDFRequest(EntreePoteau, PDFMeta): pass
class SemellePDFRequest(EntreeSemelle, PDFMeta): pass
class RadierPDFRequest(EntreeRadier, PDFMeta): pass
class DallePDFRequest(EntreeDalle, PDFMeta): pass
class PoutreContinuePDFRequest(EntreePoutreContinue, PDFMeta): pass
class VoilePDFRequest(EntreeVoile, PDFMeta): pass
class EscalierPDFRequest(EntreeEscalier, PDFMeta): pass
class LinteauPDFRequest(EntreeLinteau, PDFMeta): pass
class SemIsoleePDFRequest(EntreeSemIsolee, PDFMeta): pass
class AcroterePDFRequest(EntreeAcrotere, PDFMeta): pass
class MurSoutenementPDFRequest(EntreeMurSoutenement, PDFMeta): pass

def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'}
    )

@app.post("/pdf/poutre")
def pdf_poutre(req: PoutrePDFRequest):
    res = calculer_poutre(req)
    return _pdf_response(generer_note_poutre(req, res, req.projet, req.ingenieur), f"note_poutre_{req.projet}")

@app.post("/pdf/poteau")
def pdf_poteau(req: PoteauPDFRequest):
    res = calculer_poteau(req)
    return _pdf_response(generer_note_poteau(req, res, req.projet, req.ingenieur), f"note_poteau_{req.projet}")

@app.post("/pdf/semelle")
def pdf_semelle(req: SemellePDFRequest):
    res = calculer_semelle(req)
    return _pdf_response(generer_note_semelle(req, res, req.projet, req.ingenieur), f"note_semelle_{req.projet}")

@app.post("/pdf/radier")
def pdf_radier(req: RadierPDFRequest):
    res = calculer_radier(req)
    return _pdf_response(generer_note_radier(req, res, req.projet, req.ingenieur), f"note_radier_{req.projet}")

@app.post("/pdf/dalle")
def pdf_dalle(req: DallePDFRequest):
    res = calculer_dalle(req)
    return _pdf_response(generer_note_dalle(req, res, req.projet, req.ingenieur), f"note_dalle_{req.projet}")

@app.post("/pdf/poutre-continue")
def pdf_poutre_continue(req: PoutreContinuePDFRequest):
    res = calculer_poutre_continue(req)
    return _pdf_response(generer_note_poutre_continue(req, res, req.projet, req.ingenieur), f"note_poutre_continue_{req.projet}")

@app.post("/pdf/voile")
def pdf_voile(req: VoilePDFRequest):
    res = calculer_voile(req)
    return _pdf_response(generer_note_voile(req, res, req.projet, req.ingenieur), f"note_voile_{req.projet}")

@app.post("/pdf/escalier")
def pdf_escalier(req: EscalierPDFRequest):
    res = calculer_escalier(req)
    return _pdf_response(generer_note_escalier(req, res, req.projet, req.ingenieur), f"note_escalier_{req.projet}")

@app.post("/pdf/linteau")
def pdf_linteau(req: LinteauPDFRequest):
    res = calculer_linteau(req)
    return _pdf_response(generer_note_linteau(req, res, req.projet, req.ingenieur), f"note_linteau_{req.projet}")

@app.post("/pdf/semelle-isolee")
def pdf_semelle_isolee(req: SemIsoleePDFRequest):
    res = calculer_semelle_isolee(req)
    return _pdf_response(generer_note_semelle_isolee(req, res, req.projet, req.ingenieur), f"note_semelle_isolee_{req.projet}")

@app.post("/pdf/acrotere")
def pdf_acrotere(req: AcroterePDFRequest):
    res = calculer_acrotere(req)
    return _pdf_response(generer_note_acrotere(req, res, req.projet, req.ingenieur), f"note_acrotere_{req.projet}")

@app.post("/pdf/mur-soutenement")
def pdf_mur_soutenement(req: MurSoutenementPDFRequest):
    res = calculer_mur_soutenement(req)
    return _pdf_response(generer_note_mur_soutenement(req, res, req.projet, req.ingenieur), f"note_mur_soutenement_{req.projet}")
