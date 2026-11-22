"""Configuración central del RAG de gobierno de datos (DAMA-DMBOK) - Universidad Icesi.

Todos los valores se pueden cambiar con variables de entorno, sin tocar el código.
Ejemplo (PowerShell):  $env:RAG_LLM = "llama3.1:8b"
"""
import os
from pathlib import Path

# --- Rutas ---------------------------------------------------------------
RAIZ = Path(__file__).resolve().parent.parent
CORPUS = RAIZ / "corpus"
MANIFEST = RAIZ / "corpus_manifest.csv"
def _carpeta_chroma():
    """Ubicación de la base vectorial.

    Chroma no logra abrir su índice (hnswlib) cuando la ruta tiene caracteres no ASCII
    (por ejemplo "FORMACIÓN") y tampoco se lleva bien con carpetas sincronizadas como
    Google Drive. En esos casos, en Windows, la base se guarda en la carpeta local del
    usuario. Se puede fijar otra ubicación con la variable RAG_CHROMA_DIR.
    """
    if os.getenv("RAG_CHROMA_DIR"):
        return Path(os.getenv("RAG_CHROMA_DIR"))
    ruta = str(RAIZ)
    if os.name == "nt" and (not ruta.isascii() or "Mi unidad" in ruta or "My Drive" in ruta):
        return Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "rag-dama-icesi" / "chroma_db"
    return RAIZ / "chroma_db"


CHROMA_DIR = _carpeta_chroma()
FRAGMENTOS_JSONL = CHROMA_DIR / "fragmentos.jsonl"   # copia legible de lo indexado
EVAL_DIR = RAIZ / "eval"

# Subcarpetas del corpus que se indexan (interno/ y restringido/ se indexan
# si tienen documentos; están fuera de GitHub por el .gitignore).
CARPETAS_CORPUS = ["publico", "propio", "restringido", "interno"]

# --- Ollama --------------------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
if not OLLAMA_URL.startswith("http"):
    OLLAMA_URL = "http://" + OLLAMA_URL
MODELO_EMBED = os.getenv("RAG_EMBED", "bge-m3")        # embeddings multilingües
MODELO_LLM = os.getenv("RAG_LLM", "qwen2.5:7b")         # modelo que responde
MODELO_JUEZ = os.getenv("RAG_JUEZ", "qwen2.5:7b")       # juez de RAGAS
CONTEXTO_LLM = int(os.getenv("RAG_NUM_CTX", "8192"))    # ventana de contexto en Ollama
TIMEOUT_OLLAMA = int(os.getenv("RAG_TIMEOUT", "600"))   # segundos

# --- Base vectorial ------------------------------------------------------
COLECCION = os.getenv("RAG_COLECCION", "dama_icesi")

# --- Fragmentación -------------------------------------------------------
TAM_FRAGMENTO = int(os.getenv("RAG_TAM_FRAGMENTO", "1000"))   # caracteres
SOLAPE = int(os.getenv("RAG_SOLAPE", "150"))                  # caracteres
MIN_FRAGMENTO = 80                                            # descarta trozos casi vacíos

# --- Recuperación --------------------------------------------------------
K = int(os.getenv("RAG_K", "8"))                 # fragmentos que recibe el LLM
MIN_DAMA = int(os.getenv("RAG_MIN_DAMA", "2"))   # mínimo de fragmentos de la capa A (DAMA)

# Frase exacta con la que el sistema se abstiene (la evaluación la busca).
FRASE_ABSTENCION = "No encuentro esa información en el corpus documental."
