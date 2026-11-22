# Asistente RAG de gobierno de datos (DAMA-DMBOK) · Universidad Icesi

Sistema RAG (*Retrieval-Augmented Generation*) para que el equipo de gobierno de datos de la
Universidad Icesi haga preguntas sobre la metodología DAMA-DMBOK y reciba respuestas acotadas
al corpus documental, con citas a las fuentes.

Tarea 2 del curso Tendencias de IA Generativa (MCD): RAG con información de la organización,
**Chroma DB** como base vectorial y **métricas de calidad de las respuestas** (RAGAS y métricas propias).

Todo corre localmente con **Ollama**: los documentos no salen del equipo y no hay costo por consulta.

## Arquitectura

```
corpus/ (PDF, OCR, Markdown)          corpus_manifest.csv (metadatos)
          │                                     │
          └──────────► src/ingesta.py ◄─────────┘
                        extracción → limpieza → fragmentos (~1.000 caracteres)
                        → embeddings bge-m3 (Ollama) → Chroma (chroma_db/)
                                     │
pregunta ──► src/rag.py: embedding de la pregunta → búsqueda en Chroma (k=8,
             mínimo 2 fragmentos DAMA) → prompt con fragmentos → LLM local
             (qwen2.5:7b) → respuesta con citas [A2_12], [C1, p. 3]
                                     │
             src/app.py (chat Streamlit)   eval/evaluar.py (métricas)
```

| Componente | Tecnología |
|---|---|
| Extracción de texto | PyMuPDF; OCR con Tesseract para PDF escaneados (ya incluido en `corpus/`) |
| Embeddings | `bge-m3` en Ollama (multilingüe: preguntas en español, diagramas DAMA en inglés) |
| Base vectorial | Chroma persistente, distancia coseno |
| LLM | `qwen2.5:7b` en Ollama (configurable) |
| Interfaz | Streamlit |
| Evaluación | hit rate, MRR, abstención, citas válidas y RAGAS 0.4 con juez local |

## Corpus

El corpus está organizado en capas, y cada fragmento lleva la capa en sus metadatos:

| Capa | Contenido |
|---|---|
| A | DAMA-DMBOK2: 14 diagramas de contexto oficiales y la Rueda DAMA (transcripción literal, CC BY-ND 4.0) |
| B | Guías colombianas que adaptan DAMA: MinTIC (gobierno de datos, datos maestros, calidad…) y DANE (metadatos) |
| C | Normativa de datos personales: Ley 1581, Decretos 1377 y 1389, guías de la SIC |
| D | Referentes de otras instituciones: UNAL, CUC, EDUCAUSE, UPME |
| F | Documentos de la Universidad Icesi: política de datos personales, seguridad de la información, lineamientos de IA |

El detalle de cada documento (fuente, licencia, URL) está en `corpus_manifest.csv` y en
`01_Fuentes_corpus_RAG_DAMA.md`.

> Limitación: la oficina no tiene el libro DAMA-DMBOK2. La capa A se basa en los diagramas de
> contexto oficiales; el sistema responde "según el marco DAMA tal como lo resumen sus diagramas
> y adaptaciones", no según el texto completo del libro.

## Instalación (Windows, PowerShell)

### 1. Ollama y modelos

Instala Ollama desde https://ollama.com y descarga los modelos:

```powershell
ollama pull bge-m3
ollama pull qwen2.5:7b
```

Recomendado: ampliar la ventana de contexto del servidor para el juez de RAGAS y reiniciar Ollama:

```powershell
setx OLLAMA_CONTEXT_LENGTH 8192
```

### 2. Entorno de Python

Como la carpeta del proyecto está en Google Drive, conviene crear el entorno virtual **fuera** de
Drive (miles de archivos que no deben sincronizarse):

```powershell
cd "G:\Mi unidad\2-FORMACIÓN\MCD\Tendencias de IA\Tarea 2"
python -m venv $HOME\venvs\rag-dama
& $HOME\venvs\rag-dama\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONUTF8 = "1"          # tildes correctas en la consola
```

La base vectorial no se guarda en la carpeta del proyecto: Chroma no puede abrir su índice en rutas
con tildes (como `2-FORMACIÓN`) ni en carpetas de Google Drive. En Windows se guarda automáticamente en
`%LOCALAPPDATA%\rag-dama-icesi\chroma_db`. Para usar otra ubicación: `$env:RAG_CHROMA_DIR = "C:\rag\chroma_db"`.

### 3. Cargar el corpus en Chroma

```powershell
python src/ingesta.py
```

La carga es incremental: si vuelves a ejecutarla, solo procesa los documentos nuevos o modificados
y retira del índice los que ya no estén en `corpus/`. Para reconstruir todo: `python src/ingesta.py --reconstruir`.
Para revisar la fragmentación sin usar Ollama: `python src/ingesta.py --solo-extraer`
(genera `chroma_db/vista_previa_fragmentos.jsonl`).

## Uso

Pregunta desde la terminal:

```powershell
python src/rag.py "¿Cuáles son las actividades de la gestión de calidad de datos según DAMA?"
```

Chat en el navegador:

```powershell
streamlit run src/app.py
```

En la barra lateral se puede cambiar `k`, el mínimo de fragmentos DAMA y filtrar por capa.

## Evaluación

El conjunto de prueba está en `eval/preguntas.csv`: 53 preguntas (24 DAMA, 8 guías colombianas,
11 normativa, 5 Icesi y 5 fuera de alcance), cada una con respuesta de referencia y documento esperado.
**Es un borrador: conviene que el equipo revise las respuestas de referencia.**

Antes de evaluar, permite que Ollama atienda varias peticiones a la vez y reinícialo:

```powershell
setx OLLAMA_NUM_PARALLEL 4
```

```powershell
# prueba rápida: 5 preguntas, solo métricas sin juez
python eval/evaluar.py --etiqueta prueba --limite 5 --sin-ragas

# corrida completa: métricas sin juez sobre las 53 preguntas y RAGAS sobre una muestra de 20
python eval/evaluar.py --etiqueta base

# comparar una configuración alternativa, por ejemplo sin el mínimo de fragmentos DAMA
python eval/evaluar.py --etiqueta sin_dama --min-dama 0

# recalcular métricas y RAGAS sobre respuestas ya generadas
python eval/evaluar.py --solo-ragas eval/resultados/base_AAAAMMDD-HHMM_respuestas.jsonl
```

### Cómo se acelera la evaluación

Cada pregunta requiere unas 9 llamadas al modelo juez. Para que la corrida sea corta:

| Opción | Por defecto | Efecto |
|---|---|---|
| `--paralelo` | `4` | Preguntas que se procesan al mismo tiempo, tanto al generar respuestas como en RAGAS. Las cuatro métricas de cada pregunta también se piden en paralelo. Si la GPU tiene poca memoria (6 GB o menos), usa `--paralelo 2`. |
| `--muestra-ragas` | `20` | RAGAS se calcula sobre una muestra estratificada por categoría (siempre la misma, semilla fija). Las métricas sin juez usan todas las preguntas. `0` = todas. |
| `--k-precision` | `5` | Context precision juzga solo los 5 primeros fragmentos (hace una llamada por fragmento). |
| Caché del juez | activa | Las respuestas del juez se guardan en `eval/.cache_ragas/`; repetir una evaluación sobre las mismas respuestas no vuelve a llamar al modelo. |
| Telemetría de RAGAS | desactivada | Además de no enviar datos de uso, evita que cada llamada espere el envío de la telemetría, que anulaba el paralelismo. |

Verifica con `ollama ps` que el modelo corre en GPU ("100% GPU"); en CPU todo será mucho más lento.

### Métricas

| Métrica | Qué mide | Necesita juez |
|---|---|---|
| Hit rate @k / @3 | % de preguntas en que el documento esperado aparece entre los fragmentos recuperados | No |
| MRR | Qué tan arriba aparece el documento esperado (1 = primer lugar) | No |
| Citas válidas | % de respuestas que citan al menos un fragmento realmente recuperado | No |
| Abstención correcta | % de preguntas fuera de alcance en que el sistema dice que no tiene la información | No |
| Falsa abstención | % de preguntas en alcance que el sistema no respondió | No |
| Faithfulness (RAGAS) | Si las afirmaciones de la respuesta se sustentan en el contexto recuperado | Sí |
| Answer relevancy (RAGAS) | Si la respuesta atiende la pregunta | Sí |
| Context precision (RAGAS) | Si los fragmentos recuperados son pertinentes frente a la referencia | Sí |
| Context recall (RAGAS) | Si los fragmentos recuperados cubren la respuesta de referencia | Sí |

Los resultados quedan en `eval/resultados/`. `resumen.csv` guarda una fila por corrida, para comparar
configuraciones en la presentación.

El juez de RAGAS es un modelo local (por defecto el mismo `qwen2.5:7b`). Un modelo pequeño a veces
no devuelve el JSON que RAGAS espera; esos casos quedan como vacíos y se cuentan en `ragas_fallos`.
Si hay muchos, usa un juez más grande (`$env:RAG_JUEZ = "qwen2.5:14b"`).

## Configuración

Todo se ajusta con variables de entorno (ver `src/config.py`):

| Variable | Por defecto | Uso |
|---|---|---|
| `RAG_LLM` | `qwen2.5:7b` | Modelo que responde |
| `RAG_JUEZ` | `qwen2.5:7b` | Juez de RAGAS |
| `RAG_EMBED` | `bge-m3` | Modelo de embeddings |
| `RAG_K` | `8` | Fragmentos que recibe el LLM |
| `RAG_MIN_DAMA` | `2` | Mínimo de fragmentos de la capa A |
| `RAG_TAM_FRAGMENTO` / `RAG_SOLAPE` | `1000` / `150` | Tamaño y solapamiento de los fragmentos (caracteres) |
| `RAG_CHROMA_DIR` | `chroma_db/` | Ubicación de la base vectorial |
| `OLLAMA_HOST` | `http://localhost:11434` | Servidor de Ollama |

Si cambias el modelo de embeddings o la fragmentación, ejecuta `python src/ingesta.py --reconstruir`.

## Agregar documentos (por ejemplo, documentos internos de la oficina)

1. Guarda el archivo en `corpus/interno/` (o `corpus/publico/`) con un código al inicio del nombre:
   `F5_glosario_de_negocio.pdf`.
2. Agrega una fila con ese código (`F5`) en `corpus_manifest.csv`: título, emisor, capa, área DAMA, licencia.
3. Ejecuta `python src/ingesta.py`. Solo se procesa lo nuevo.

`corpus/interno/` y `corpus/restringido/` están excluidas de Git en `.gitignore`. Antes de indexar
documentos internos, revisa que no contengan datos personales.

## Repositorio en GitHub

El repositorio es **privado**. Para entregar el enlace, agrega al profesor como colaborador
(Settings → Collaborators); si no, el enlace le mostrará un error 404.

```powershell
git init
git add .
git commit -m "RAG de gobierno de datos DAMA-DMBOK con Chroma y RAGAS"
gh repo create rag-dama-icesi --private --source . --push
```

## Estructura

```
├── 01_Fuentes_corpus_RAG_DAMA.md   recomendación y licencias de las fuentes
├── corpus_manifest.csv             inventario del corpus (metadatos)
├── corpus/
│   ├── publico/                    documentos públicos + diagramas DAMA (texto/ para el RAG)
│   ├── propio/                     contenido escrito por el equipo
│   ├── restringido/                material con licencia restringida (fuera de Git)
│   └── interno/                    documentos internos (fuera de Git)
├── src/
│   ├── config.py                   configuración
│   ├── ollama_cliente.py           llamadas a Ollama
│   ├── ingesta.py                  extracción, fragmentación y carga en Chroma
│   ├── rag.py                      recuperación y generación
│   └── app.py                      chat en Streamlit
├── eval/
│   ├── preguntas.csv               conjunto de prueba (borrador)
│   ├── evaluar.py                  métricas y RAGAS
│   └── resultados/                 salidas de cada corrida
└── requirements.txt
```

---
Andrés Ocampo · Oficina de Estrategia de Datos Institucionales · Universidad Icesi
