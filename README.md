# Simulador de Entrevistas

Prototipo educativo para entrenar a estudiantes en entrevistas de levantamiento de información.

## Estado actual

Rama de desarrollo: **v0.3 · modelo pedagógico y evaluador IA**.

La aplicación separa tres responsabilidades:

1. El **entrevistado IA** interpreta al personaje y conversa con el estudiante.
2. La **configuración pedagógica** define qué competencias pueden entrenarse y cuáles se evalúan en cada simulación.
3. El **evaluador IA** analiza la transcripción únicamente después de finalizar la entrevista.

## Modelo pedagógico

El objetivo general y el catálogo de objetivos están en:

`config/pedagogia.json`

El catálogo inicial incluye objetivos relacionados con apertura, preguntas abiertas, continuidad de la indagación, escucha activa, repreguntas, actores, procesos, datos y sistemas, reglas de negocio, problemas, excepciones, neutralidad, validación y cierre.

La simulación actual está definida en:

`casos/retailnova/simulacion_bodega.json`

Ese archivo selecciona qué objetivos del catálogo se evaluarán en la entrevista con Carolina. En una etapa posterior, el panel docente permitirá realizar esta selección desde la interfaz.

## Escala de logro

Cada objetivo se evalúa usando cuatro niveles:

- No evidenciado.
- En desarrollo.
- Logrado.
- Destacado.

El evaluador debe justificar el nivel con evidencia de la transcripción y proponer una acción concreta de mejora.

## Arquitectura

- Backend: Python + FastAPI.
- Entrevistado IA: `app/interviewer.py`.
- Evaluador IA: `app/evaluator.py`.
- Catálogo pedagógico: `config/pedagogia.json`.
- Configuración de la entrevista: `casos/retailnova/simulacion_bodega.json`.
- Frontend: HTML, CSS y JavaScript.
- Casos y personajes: JSON.
- Entorno local: `.venv`.

## Configuración local

Copiar `.env.example` como `.env` y completar:

```text
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-5.6-luna
OPENAI_EVALUATOR_MODEL=gpt-5.6-luna
```

Luego ejecutar:

```text
run.bat
```

y abrir:

`http://127.0.0.1:8000`

## Principio de evaluación

El sistema no evalúa solo si el estudiante consiguió una palabra o hallazgo.

Por ejemplo, que Carolina mencione Excel no demuestra por sí mismo que el estudiante haya realizado una buena entrevista. El evaluador analiza la acción del estudiante que produjo, profundizó o validó esa información.

## Alcance del Hito 3

Esta versión permite validar que:

- existe un objetivo general independiente del personaje;
- los objetivos específicos provienen de un catálogo reutilizable;
- una simulación selecciona cuáles objetivos evaluar;
- Carolina sigue siendo únicamente entrevistada;
- el evaluador es un agente separado;
- la evaluación usa evidencia de la transcripción;
- cada objetivo recibe nivel, evidencia, justificación y sugerencia de mejora.

Todavía no incluye login, panel docente, persistencia de estudiantes, voz ni realidad virtual.
