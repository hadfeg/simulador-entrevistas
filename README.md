# Simulador de Entrevistas

Prototipo educativo para entrenar a estudiantes en entrevistas de levantamiento de información.

## Estado actual

Rama de desarrollo: **v0.2 · entrevistado con IA**.

Esta versión:
- presenta el caso RetailNova;
- incluye a Carolina Morales, Encargada de Bodega;
- permite realizar la entrevista por texto;
- usa IA para comprender lenguaje natural y mantener contexto;
- controla el comportamiento mediante la ficha JSON del personaje;
- conserva una detección de hallazgos provisional;
- todavía no incorpora el evaluador con IA, voz ni realidad virtual.

## Arquitectura

- Backend: Python + FastAPI.
- Entrevistado IA: OpenAI Responses API.
- Frontend: HTML, CSS y JavaScript.
- Casos y personajes: JSON.
- Entorno local: `.venv`.

## Configuración local

1. Tener Python instalado.
2. Copiar `.env.example` como `.env`.
3. Completar en `.env`:

```text
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-5.6-luna
```

4. Ejecutar `run.bat`.
5. Abrir `http://127.0.0.1:8000`.

`run.bat` crea un entorno virtual `.venv` para mantener aisladas las dependencias.

## Seguridad

El archivo `.env` está excluido por `.gitignore`. Nunca se debe subir una clave de API al repositorio.

## Alcance del Hito 2

El objetivo de esta versión es validar que Carolina:
- mantenga el contexto de la conversación;
- entienda repreguntas como “¿dónde lo registran?”, “¿quién hace eso?” o “¿por qué?”;
- responda de forma natural;
- no revele todos los hallazgos de inmediato;
- no actúe como tutora ni evaluadora.

La evaluación automática inteligente corresponde al siguiente hito.