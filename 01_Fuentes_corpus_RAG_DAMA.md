# Corpus documental del RAG de Gobierno de Datos (DAMA-DMBOK)
**Universidad Icesi · Oficina de Estrategia de Datos Institucionales**
Recomendación de fuentes · versión 0.2 · 16 de noviembre de 2026 (incluye las decisiones de la sección 8)

---

## 1. Criterios de selección

1. **Autoridad.** DAMA-DMBOK2 es la referencia primaria. Todo lo demás se ordena según lo cerca que esté de DAMA: adaptaciones oficiales del marco, normativa obligatoria, referentes de otras universidades y marcos complementarios.
2. **Pertinencia.** Se escogieron documentos útiles para una universidad privada colombiana: datos académicos y administrativos, datos personales de estudiantes y registros institucionales.
3. **Licencia.** Cada documento indica si puede ir al repositorio de GitHub o si solo se indexa de forma local.
4. **Idioma.** Se prefieren documentos en español. Los documentos en inglés se aceptan porque los embeddings multilingües (por ejemplo bge-m3) recuperan bien entre idiomas.

> DMBOK2 (edición revisada de 2024) sigue siendo el estándar vigente. DAMA trabaja en DMBOK 3.0, cuya publicación está prevista para 2027. El corpus debe poder actualizarse cuando salga esa versión.

---

## 2. Estructura en capas

Cada documento lleva un metadato `capa`. Con él se pueden filtrar o ponderar los resultados en Chroma; por ejemplo, para responder "¿qué dice DAMA sobre…?" solo con las capas A y B.

| Capa | Contenido | Papel en el RAG |
|---|---|---|
| **A** | Núcleo DAMA-DMBOK | Fuente primaria de la metodología |
| **B** | Adaptación colombiana de DAMA (MinTIC, DANE) | Traduce DAMA al contexto y vocabulario colombianos |
| **C** | Normativa de datos personales | Obligaciones legales del área de Seguridad y de Ética |
| **D** | Referentes de otras universidades | Ejemplos de políticas y modelos de gobierno en educación superior |
| **E** | Marcos complementarios | Profundizan procesos y evaluación. Se citan como "complementarios", no como DAMA |
| **F** | Documentos de Icesi | La "información de la organización" que exige la tarea |

Prioridad: **E** = esencial · **R** = recomendado · **O** = opcional

---

### Capa A · Núcleo DAMA-DMBOK

| ID | Documento | Por qué incluirlo | Licencia y manejo en el repositorio | Prioridad |
|---|---|---|---|---|
| A1 | **DAMA-DMBOK2, edición revisada** (DAMA International y Technics Publications, 2024). Hay traducciones, incluida una al español. | Es la metodología misma: 11 áreas de conocimiento, más ética, big data y ciencia de datos, y evaluación de madurez. | Tiene derechos de autor. **La oficina no tiene ejemplar (16 nov 2026): queda fuera de la versión 1.** Si se adquiere, se indexa en `corpus/restringido/` y se validan las fichas A3 contra el libro. | E (pendiente) |
| A2 | **Diagramas de contexto de DMBOK2 (14) y la Rueda DAMA** ([dama.org/dmbok](https://dama.org/dmbok)) | Cada diagrama resume un área: definición, metas, entradas, actividades, entregables, roles, técnicas, herramientas y métricas. Es la versión de DAMA más fiel que se puede usar libremente. | Licencia **CC BY-ND 4.0**. Se pueden compartir con atribución y sin modificar la imagen. Propuesta: transcribir cada diagrama a texto (un documento corto por área) con la atribución a DAMA International y conservar las imágenes originales. | E |
| A3 | **Fichas propias por área de conocimiento** (11 áreas, más ética y madurez), redactadas por el equipo | Ofrecen fragmentos limpios y homogéneos con las palabras de Icesi. Cada ficha incluye la referencia al capítulo y la página de DMBOK2. Resuelven el problema de licencia del libro y sirven además como respuestas de referencia para la evaluación. | Contenido propio: **se puede subir al repositorio.** | E |
| A4 | **Glosario DAMA del equipo** (data owner, data steward, custodio, metadatos, dato maestro, linaje…) | Las preguntas de vocabulario son las más frecuentes en un equipo de gobierno de datos. | Contenido propio: se puede subir al repositorio. Puede alinearse con el *DAMA Dictionary of Data Management*. | R |
| A5 | *DAMA Dictionary of Data Management*, 2.ª ed. (más de 2.000 términos) | Glosario oficial asociado al DMBOK. | Es de pago. No se sube al repositorio. | O |

### Capa B · Adaptación colombiana de DAMA

| ID | Documento | Por qué incluirlo | Áreas DAMA | Prioridad |
|---|---|---|---|---|
| B1 | **MinTIC MGGTI.GE.GI.04, Guía específica de Gobierno de Datos**, v3.0, noviembre de 2024 ([PDF](https://www.mintic.gov.co/arquitecturaempresarial/630/articles-398776_recurso_1.pdf)) | Adopta los principios de DAMA, los tipos de custodios de datos, el CDO, los comités, la oficina de gobierno y el modelo operativo. Es la mejor "traducción" oficial de DAMA al español. | Gobierno | E |
| B2 | **MinTIC MGGTI.G.GI, Guía de dominio de gestión de información**, v1.0, mayo de 2023 ([PDF](https://www.mintic.gov.co/arquitecturaempresarial/630/articles-237660_recurso_1.pdf)) | Cubre ciclo de vida, calidad, datos maestros, metadatos, explotación y apertura de datos, con sus roles. Cita DAMA-DMBOK como estándar. | Varias | E |
| B3 | MinTIC MGGTI.GE.GI.05, Guía específica para la gestión de datos maestros ([ZIP](https://www.mintic.gov.co/arquitecturaempresarial/630/articles-440525_recurso_1.zip)) | Datos maestros: estudiante, programa, docente, dependencia. | Datos maestros y de referencia | R |
| B4 | MinTIC MGGTI.GE.GI.08, Guía de aprovechamiento de datos, v1, diciembre de 2025 ([PDF](https://www.mintic.gov.co/arquitecturaempresarial/630/articles-440526_recurso_1.pdf)), CC BY 4.0 | Uso analítico de los datos. | Bodega de datos e inteligencia de negocios, big data | R |
| B5 | MinTIC MAE.GE.AI.04, Guía para elaborar modelos de datos y mapas de información ([PDF](https://www.mintic.gov.co/arquitecturaempresarial/630/articles-440520_recurso_1.pdf)), CC BY 4.0 | Se apoya explícitamente en DAMA-DMBOK y en la norma ISO/IEC 11179. | Arquitectura, modelado, metadatos | R |
| B6 | MinTIC, Guía de estándares de calidad e interoperabilidad de los datos abiertos, julio de 2022 ([PDF](https://gobiernodigital.mintic.gov.co/692/articles-179118_recurso_5.pdf)), CC BY 4.0 | Dimensiones y criterios de calidad de datos aplicables. | Calidad, integración | R |
| B7 | DANE, Lineamientos para la documentación de metadatos con los estándares DDI y Dublin Core, 2014 ([PDF](https://www.dane.gov.co/files/sen/lineamientos/DSO_050_LIN_01.pdf)), y Recomendaciones para la documentación de metadatos de registros administrativos, 2023 ([PDF](https://www.dane.gov.co/files/sen/lineamientos/Recomendaciones-documentacion-metadatos-registroAdmi.pdf)) | Metadatos de registros administrativos, el tipo de dato con el que más trabaja la oficina. | Metadatos | R |

> Nota de licencia: MinTIC suele publicar sus guías con licencia CC BY 4.0, y así consta en B4, B5 y B6. Para B1, B2 y B3 hay que confirmar la licencia en cada documento antes de subirlos al repositorio.

### Capa C · Normativa de datos personales

| ID | Documento | Por qué incluirlo | Prioridad |
|---|---|---|---|
| C1 | **Ley 1581 de 2012**, protección de datos personales ([Gestor Normativo](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=49981)) | Marco legal obligatorio para el área de Seguridad y para la de Ética. | E |
| C2 | **Decreto 1377 de 2013**, compilado en el Decreto 1074 de 2015 | Reglamenta la autorización del titular, las políticas de tratamiento y las transferencias de datos. | E |
| C3 | **SIC, Guía sobre el tratamiento de datos personales en el contexto universitario**, julio de 2026 ([copia en PDF](https://www.universidad.edu.co/wp-content/uploads/2026/08/Guia_Datos_personalesenIES.pdf); conviene buscar la versión original en la sede electrónica de la SIC) | Es muy reciente y está escrita para universidades. Trata la clasificación de la información académica, el consentimiento diferenciado, la privacidad desde el diseño, el oficial de protección de datos, la responsabilidad demostrada y los trabajos de los estudiantes. | E |
| C4 | SIC, Guía para la implementación del principio de responsabilidad demostrada ([PDF](http://www.sic.gov.co/sites/default/files/files/Publicaciones/Guia-Accountability.pdf); verificar que el enlace siga vigente) | Explica cómo demostrar el cumplimiento de la ley, lo cual se conecta con las métricas de gobierno. | R |
| C5 | Decreto 1389 de 2022, Modelo de Gobernanza de la Infraestructura de Datos ([PDF](https://normograma.icfes.gov.co/docs/pdf/decreto_1389_2022.pdf)) | Da contexto nacional, pero se dirige sobre todo al sector público. | O |

### Capa D · Referentes de otras universidades y de la educación superior

| ID | Documento | Por qué incluirlo | Prioridad |
|---|---|---|---|
| D1 | **Universidad del Rosario, Política de gestión de datos e información institucional**, v1.0, mayo de 2021, Decreto Rectoral 1694 ([PDF](https://repository.urosario.edu.co/bitstreams/1a92135c-4e4f-406f-870d-62a59d59e90f/download)) | Política universitaria colombiana que cita DMBOK2 de forma explícita. | R |
| D2 | Universidad Nacional de Colombia, Modelo de gestión de la información, U.MD.17.001.001 ([PDF](https://gestiondeinformacion.unal.edu.co/media/documentos/UMD17001001_-_Modelo_de_Gesti%C3%B3n_de_la_Informaci%C3%B3n_1.pdf)) | Modelo completo de 195 páginas: ética, gobierno, comité y política. Por su extensión requiere una fragmentación cuidadosa. | R |
| D3 | Universidad de la Costa (CUC), Política de gobierno de datos, Acuerdo CD 712, noviembre de 2025 ([PDF](https://www.cuc.edu.co/wp-content/uploads/2025/12/AC-No.-CD-712-POLITICA-DE-GOBIERNO-DE-DATOS-UNIVERSIDAD-DE-LA-COSTA-CUC-24112025.pdf)) | Es la política universitaria más reciente encontrada. | R |
| D4 | EDUCAUSE, *2023 Horizon Action Plan: Data Governance*, 11 páginas, en inglés ([página](https://library.educause.edu/resources/2023/3/2023-educause-horizon-action-plan-data-governance)), CC BY-NC-ND 4.0 | Visión de la educación superior internacional sobre gobierno de datos. | R |
| D5 | EDUCAUSE, *Establishing Data Stewardship Models*, 2015 ([página](https://library.educause.edu/resources/2015/12/establishing-data-stewardship-models)) | Modelos de custodia (stewardship) para datos administrativos universitarios. Hay que verificar si su acceso es libre. | O |
| D6 | UPME, Políticas de gobierno de datos del sector minero-energético, abril de 2025 ([PDF](https://docs.upme.gov.co/CIO-Sectorial/Politicas_de_gobierno_de_datos_CIO_2024%2025-02-2025_VFD.pdf)) | Ejemplo colombiano reciente de roles y políticas basados en DMBOK. | O |

### Capa E · Marcos complementarios (se etiquetan como "no DAMA")

| ID | Documento | Por qué incluirlo | Manejo | Prioridad |
|---|---|---|---|---|
| E1 | **Especificaciones UNE 0077:2023 (Gobierno del dato), UNE 0078:2023 (Gestión del dato) y UNE 0079:2023 (Gestión de la calidad del dato)**, más las guías de evaluación UNE 0080 y 0081 ([información](https://datos.gob.es/en/node/129089)) | Están en español y describen procesos de forma operativa, compatibles con DAMA. La descarga es gratuita en AENOR gracias al patrocinio de la Oficina del Dato de España. | La descarga gratuita no autoriza a redistribuirlas: **solo se indexan de forma local, no se suben al repositorio.** | R |
| E2 | DGI Data Governance Framework, del Data Governance Institute ([página](https://datagovernance.com/the-dgi-data-governance-framework/)) | Marco clásico de componentes de gobierno: por qué, qué, quién y cómo. | Se etiqueta `capa=E`. | O |
| E3 | Abraham, Schneider y vom Brocke (2019), "Data governance: A conceptual framework, structured review, and research agenda", *IJIM* ([DOI](https://doi.org/10.1016/j.ijinfomgt.2019.07.008)) | Síntesis académica del gobierno de datos. | La versión de la revista es de pago; los autores publicaron un manuscrito propio. | O |

### Capa F · Documentos de la Universidad Icesi (requisito de la tarea)

| ID | Documento | Disponibilidad | Prioridad |
|---|---|---|---|
| F1 | **Política de tratamiento de datos personales de la Universidad Icesi** | Pública (sitio web y Secretaría General). | E |
| F2 | **Lineamientos para el uso responsable de herramientas de IA generativa**, Icesi, 2026 ([PDF](https://www.icesi.edu.co/servicios/wp-content/uploads/2026/03/Lineamientos-Para-El-Uso-Responsable-De-Herramientas-De-Inteligencia-Artificial-Generativa-vf.pdf)) | Pública. Es pertinente porque el mismo RAG es una herramienta de IA generativa. | R |
| F3 | **Lineamientos de clasificación y recomendaciones para el tratamiento de la información de la Universidad Icesi** | Los cita F2. Hay que confirmar si son públicos o internos. | E |
| F4 | Política de seguridad de la información de Icesi | Hay que confirmar si es pública o interna. | R |
| F5 | **Documentos de la oficina**: marco o política de gobierno de datos, roles y matriz RACI (dueños y custodios), glosario de negocio, diccionario de datos o catálogo de indicadores, decisiones del comité | Internos. **No se suben a un repositorio público.** Antes de indexarlos hay que revisar si contienen datos personales. | E, si existen |

---

## 3. Lo que recomiendo no incluir

- **PDFs del DMBOK descargados de sitios no autorizados** (Scribd y similares). Además del problema de licencia, muchos corresponden al *DAMA-DMBOK Functional Framework v3* de 2008, de la época de DMBOK1, que organiza el contenido en 10 funciones. Mezclar esa versión con DMBOK2 confunde la terminología.
- **Blogs de proveedores** de herramientas de catálogo o de nube. Sus resúmenes de DAMA tienen sesgo comercial, a veces son imprecisos y quitan peso a las fuentes autorizadas en la recuperación.
- **Tesis de grado genéricas sobre "gobierno de datos con DAMA".** Su calidad es muy variable.
- **Exceso de normativa del sector público** (todos los CONPES, el MRAE completo). Inclinaría las respuestas hacia el sector público y alejaría el corpus de DAMA.

---

## 4. Tamaño sugerido

- **Núcleo mínimo viable para la tarea (unos 10 documentos):** A2, A3, A4, B1, B2, C1, C3, D1, F1 y F2, más A1 si hay un ejemplar licenciado.
- **Versión ampliada (unos 25 a 30 documentos):** se suman las fuentes marcadas como R.
- **Balance:** la capa A debería aportar al menos el 40 % de los fragmentos. Si las capas B a D la superan, el sistema contestará "según MinTIC" o "según el Rosario" en lugar de "según DAMA". El metadato `capa` permite corregir ese desbalance en la recuperación.

## 5. Metadatos por fragmento (para Chroma)

`id_doc`, `titulo`, `emisor`, `anio`, `capa` (A–F), `autoridad` (primaria / adaptacion / normativa / referente / complementaria / institucional), `area_dama` (una de las 11 áreas, o ética, big data, madurez), `idioma`, `licencia`, `publicable_repo` (sí/no), `url`, `seccion_pagina`.

Con estos campos, Chroma puede filtrar por capa y por área con `where`, y cada respuesta puede citar el documento y la sección de donde sale.

## 6. Manejo en GitHub

Repositorio **privado** (decisión del 16 de noviembre de 2026):

```
corpus/
  publico/        -> documentos públicos de las capas A, B, C, D y F (se suben al repo privado)
  propio/         -> fichas A3 y glosario A4 escritos por el equipo (se suben)
  restringido/    -> UNE y, si se adquiere, DMBOK2 (en .gitignore)
  interno/        -> documentos internos de la oficina, cuando existan (en .gitignore hasta revisarlos)
corpus_manifest.csv   -> inventario con URL y licencia de cada documento
```

Aunque el repositorio sea privado, se mantiene fuera el material cuya licencia no permite compartirlo con terceros (el profesor y los compañeros que revisen la tarea tendrán acceso). Lo anterior es una recomendación práctica, no una asesoría legal. Ante una duda, conviene consultar a la Secretaría General.

## 7. Conexión con la presentación

- **Diapositiva "Arquitectura técnica", columna Fuentes:** se reemplaza por estas seis capas. Además, la tarea exige **Chroma DB**, así que donde la plantilla dice pgvector debe decir Chroma.
- **Diapositiva "Evaluación":** las fichas A3 permiten construir un conjunto de preguntas con respuesta de referencia por área DAMA (por ejemplo, 5 preguntas × 14 áreas = 70 preguntas). Ese conjunto alimenta RAGAS, en particular las métricas de fidelidad, relevancia, precisión y exhaustividad del contexto y corrección de la respuesta.
- **Diapositiva "Impacto":** las cifras de la plantilla son ilustrativas y deben reemplazarse por mediciones propias de la oficina.

## 8. Decisiones tomadas (16 de noviembre de 2026)

| Decisión | Consecuencia para el corpus |
|---|---|
| **La oficina no tiene ejemplar del DMBOK2.** | El núcleo DAMA de la versión 1 se apoya en los diagramas de contexto oficiales (A2), las fichas por área (A3), el glosario (A4) y la guía MinTIC MGGTI.GE.GI.04 (B1), que adopta los principios y roles de DAMA. Las fichas A3 se marcan como `validada_libro = no` hasta que se puedan contrastar con el libro. En la presentación conviene decirlo como limitación: el sistema responde "según el marco DAMA tal como lo resumen sus diagramas oficiales y sus adaptaciones", no "según el libro". |
| **El repositorio de GitHub será privado.** | Pueden subirse los documentos públicos de las capas B, C, D y F aunque su licencia no sea abierta, porque el uso es interno y académico. Siguen fuera del repositorio las normas UNE (licencia de AENOR para uso del descargador) y cualquier copia del DMBOK2. |
| **Por ahora no hay documentos internos.** | La capa F de la versión 1 queda con F1 y F2, que son públicos. Se deja creada la carpeta `corpus/interno/` y la ingesta se diseña de forma incremental: se agrega un documento al inventario, se vuelve a ejecutar la ingesta y Chroma actualiza solo lo nuevo (con `upsert` por `id_doc` y número de fragmento). Antes de indexar documentos internos se revisa si contienen datos personales. |

### Opciones para conseguir el DMBOK2 más adelante

- Comprar la edición en español o en inglés (Technics Publications).
- La membresía individual de DAMA International incluye acceso gratuito a las traducciones de la edición revisada en su portal de miembros, según anunció DAMA en 2026; hay que confirmar si ya está disponible.
