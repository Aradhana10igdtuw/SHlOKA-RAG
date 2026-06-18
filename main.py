import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

from ingest import ingest_documents
from retrieval import retrieve_context, generate_rag_answer, search_documents

load_dotenv()

app = FastAPI(
    title="Shloka-afi2 API",
    description="FastAPI Backend for Ayurvedic Text RAG and Shloka Analysis",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    k: int = 4
    generate_answer: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    raw_results: List[Dict[str, Any]]

class IngestResponse(BaseModel):
    status: str
    message: str
    chunks_count: int

class AnalyzeRequest(BaseModel):
    shloka: Optional[str] = None
    image_base64: Optional[str] = None
    top_k: int = 5
    target_language: Optional[str] = "English"

class WordMeaning(BaseModel):
    word: str
    transliteration: Optional[str] = ""
    meaning: str

class Ingredient(BaseModel):
    sanskrit_name: Optional[str] = ""
    transliteration: Optional[str] = ""
    common_name: Optional[str] = ""
    botanical_name: Optional[str] = ""
    part_used: Optional[str] = ""
    quantity: Optional[str] = ""

class DosageInfo(BaseModel):
    amount: Optional[str] = ""
    frequency: Optional[str] = ""
    anupana: Optional[str] = ""

class AnalyzeResponse(BaseModel):
    # Basic
    translation: str
    word_meanings: List[WordMeaning]
    # Formulation
    formulation_name: Optional[str] = ""
    formulation_type: Optional[str] = ""
    source_reference: Optional[str] = ""
    # Ingredients
    ingredients: Optional[List[Ingredient]] = []
    # Herb & Dosha
    herbs: List[str]
    doshas: List[str]
    dosha_influence: Optional[Dict[str, int]] = {"vata": 0, "pitta": 0, "kapha": 0}
    # Rasa Panchaka
    rasa: Optional[List[str]] = []
    virya: Optional[str] = ""
    vipaka: Optional[str] = ""
    guna: Optional[List[str]] = []
    # Medical
    body_systems: List[str]
    diseases: List[str]
    actions: List[str]
    contraindications: Optional[List[str]] = []
    # Dosage
    dosage: Optional[DosageInfo] = None
    # Interpretation
    modern_interpretation: str
    source_text: str
    confidence: float
    # Meta
    transcribed_text: Optional[str] = None
    sources: Optional[List[str]] = []

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here"),
        "gemini_configured": bool((os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_API_KEY") != "your_key_here") or (os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your_key_here")),
        "groq_configured": bool(os.getenv("GROQ_API_KEY") and os.getenv("GROQ_API_KEY") != "your_key_here")
    }

@app.post("/ingest", response_model=IngestResponse)
def run_ingest():
    try:
        chunks_count = ingest_documents()
        if chunks_count == 0:
            return {"status": "warning", "message": "No new documents found.", "chunks_count": 0}
        return {"status": "success", "message": f"Ingested {chunks_count} chunks.", "chunks_count": chunks_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest):
    try:
        if request.generate_answer:
            res = generate_rag_answer(request.query, k=request.k)
            return {"answer": res.get("answer", ""), "sources": res.get("sources", []), "raw_results": res.get("raw_results", [])}
        else:
            res = search_documents(request.query, k=request.k)
            if "error" in res:
                raise HTTPException(status_code=500, detail=res["error"])
            results = res.get("results", [])
            summary = "\n\n".join([f"Source: {r['metadata'].get('source')}\nContent: {r['content']}" for r in results])
            sources = list(set([r["metadata"].get("source", "Unknown") for r in results]))
            return {"answer": summary if summary else "No matching chunks found.", "sources": sources, "raw_results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_shloka(request: AnalyzeRequest):
    groq_key = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    use_groq = bool(groq_key and groq_key != "your_key_here")
    use_gemini = bool(gemini_key and gemini_key != "your_key_here")

    if not use_groq and not use_gemini:
        raise HTTPException(status_code=400, detail="No LLM API key configured.")

    if use_groq:
        api_key = groq_key
        base_url = "https://api.groq.com/openai/v1"
        vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        text_model = "llama-3.3-70b-versatile"
    else:
        api_key = gemini_key
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        vision_model = "gemini-2.5-flash-lite"
        text_model = "gemini-2.5-flash-lite"

    client = OpenAI(api_key=api_key, base_url=base_url)
    shloka_input = ""

    if request.image_base64:
        img_url = request.image_base64
        if not img_url.startswith("data:image/"):
            img_url = f"data:image/jpeg;base64,{img_url}"
        try:
            ocr_response = client.chat.completions.create(
                model=vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcribe all Sanskrit text from this image. Return ONLY the Sanskrit text, nothing else."},
                        {"type": "image_url", "image_url": {"url": img_url}}
                    ]
                }],
                temperature=0.1
            )
            shloka_input = ocr_response.choices[0].message.content.strip()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image transcription failed: {str(e)}")
    else:
        shloka_input = request.shloka

    if not shloka_input or not shloka_input.strip():
        raise HTTPException(status_code=400, detail="Please provide shloka text or image.")

    try:
        context_passages = retrieve_context(shloka_input, top_k=request.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

    context_str = "\n\n".join([
        f"Source: {p.get('metadata', {}).get('source', 'Unknown')}\nContent: {p.get('page_content', '')}"
        for p in context_passages
    ]) if context_passages else "No database context found."

    try:
        system_prompt = (
            "You are a senior Ayurvedic scholar and pharmacognosist fluent in Sanskrit.\n"
            f"Analyze the given Sanskrit shloka or formulation text. Translate and write descriptive fields in {request.target_language}.\n"
            "Extract ALL available information including ingredients with botanical names, doses, transliterations.\n"
            "Return ONLY a valid JSON object. No markdown, no extra text."
        )

        user_prompt = (
            f"Context:\n{context_str}\n\n"
            f"Sanskrit text to analyze:\n{shloka_input}\n\n"
            f"Return JSON with EXACTLY these fields. Please translate descriptions, translations, and meanings into {request.target_language} (while keeping standard Sanskrit terms, botanical names, and ingredient names in their standard form or Roman transliteration):\n"
            "{\n"
            f"  \"translation\": \"Full translation in {request.target_language}\",\n"
            f"  \"word_meanings\": [{{\"word\": \"Sanskrit word\", \"transliteration\": \"Roman script\", \"meaning\": \"Meaning in {request.target_language}\"}}],\n"
            "  \"formulation_name\": \"Name of the Ayurvedic formulation if present, else empty string\",\n"
            "  \"formulation_type\": \"Type e.g. Churna, Kwath, Rishta, Vati, Taila, Ghrita, else empty\",\n"
            "  \"source_reference\": \"Exact book, chapter, verse reference e.g. Bhaisajyaratnavali 609-610\",\n"
            "  \"ingredients\": [\n"
            "    {\n"
            "      \"sanskrit_name\": \"Sanskrit name\",\n"
            "      \"transliteration\": \"Roman transliteration\",\n"
            "      \"common_name\": \"Common name\",\n"
            "      \"botanical_name\": \"Scientific/botanical name\",\n"
            "      \"part_used\": \"fruit/root/bark/leaf etc\",\n"
            "      \"quantity\": \"dose with unit e.g. 144g\"\n"
            "    }\n"
            "  ],\n"
            "  \"herbs\": [\"list of herb names\"],\n"
            "  \"doshas\": [\"Vata/Pitta/Kapha affected\"],\n"
            "  \"dosha_influence\": {\n"
            "    \"vata\": 30,\n"
            "    \"pitta\": 40,\n"
            "    \"kapha\": 30\n"
            "  },\n"
            "  \"rasa\": [\"taste e.g. Madhura, Tikta, Katu, Amla, Lavana, Kashaya\"],\n"
            "  \"virya\": \"potency - Ushna or Sheeta\",\n"
            "  \"vipaka\": \"post-digestive effect - Madhura/Katu/Amla\",\n"
            "  \"guna\": [\"qualities e.g. Laghu, Guru, Snigdha, Ruksha\"],\n"
            "  \"body_systems\": [\"body systems targeted\"],\n"
            "  \"diseases\": [\"diseases with Sanskrit name (English name) format\"],\n"
            "  \"actions\": [\"therapeutic actions e.g. Deepana, Pachana, Rasayana\"],\n"
            "  \"contraindications\": [\"when NOT to use, if mentioned\"],\n"
            "  \"dosage\": {\n"
            f"    \"amount\": \"dosage amount, translated to {request.target_language} if descriptive\",\n"
            f"    \"frequency\": \"frequency of intake, translated to {request.target_language}\",\n"
            f"    \"anupana\": \"vehicle, translated to {request.target_language} (e.g. warm water, milk, honey)\"\n"
            "  },\n"
            f"  \"modern_interpretation\": \"Modern pharmacological or scientific view translated to {request.target_language}\",\n"
            "  \"source_text\": \"Source scripture name\",\n"
            "  \"confidence\": 0.95\n"
            "}"
        )

        response = client.chat.completions.create(
            model=text_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )

        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:]
        if raw_response.endswith("```"):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()

        try:
            analysis_result = json.loads(raw_response)
        except json.JSONDecodeError as je:
            raise HTTPException(status_code=502, detail={"error": "JSON parse failed", "raw": raw_response})

        # Defaults for all fields
        required_keys = {
            "translation": "", "word_meanings": [], "formulation_name": "",
            "formulation_type": "", "source_reference": "", "ingredients": [],
            "herbs": [], "doshas": [], "dosha_influence": {"vata": 0, "pitta": 0, "kapha": 0},
            "rasa": [], "virya": "", "vipaka": "", "guna": [], "body_systems": [], "diseases": [], "actions": [],
            "contraindications": [], "dosage": {"amount": "", "frequency": "", "anupana": ""},
            "modern_interpretation": "", "source_text": "", "confidence": 0.0
        }

        for key, default in required_keys.items():
            if key not in analysis_result:
                analysis_result[key] = default
            else:
                if isinstance(default, list) and not isinstance(analysis_result[key], list):
                    analysis_result[key] = [analysis_result[key]]
                elif isinstance(default, float) and not isinstance(analysis_result[key], (float, int)):
                    try:
                        analysis_result[key] = float(analysis_result[key])
                    except:
                        analysis_result[key] = 0.0
                elif isinstance(default, str) and not isinstance(analysis_result[key], str):
                    analysis_result[key] = str(analysis_result[key])

        if not isinstance(analysis_result.get("dosage"), dict):
            analysis_result["dosage"] = {"amount": "", "frequency": "", "anupana": ""}

        if not isinstance(analysis_result.get("dosha_influence"), dict):
            analysis_result["dosha_influence"] = {"vata": 0, "pitta": 0, "kapha": 0}
        else:
            di = analysis_result["dosha_influence"]
            normalized_di = {}
            for k in ["vata", "pitta", "kapha"]:
                val = di.get(k, di.get(k.capitalize(), 0))
                try:
                    normalized_di[k] = int(val)
                except:
                    normalized_di[k] = 0
            analysis_result["dosha_influence"] = normalized_di

        sources = list(set([
            p.get('metadata', {}).get('source', 'Unknown')
            for p in context_passages
            if p.get('metadata', {}).get('source')
        ])) if context_passages else []

        analysis_result["transcribed_text"] = shloka_input
        analysis_result["sources"] = sources

        return analysis_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)