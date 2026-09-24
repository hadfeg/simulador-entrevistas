# Simulador de Entrevistas

Prototipo educativo para entrenar a estudiantes en entrevistas de levantamiento de información.

## Estado actual

Rama de desarrollo: **v0.4 · Panel Docente**.

Esta versión incorpora un flujo de prueba con dos vistas:

- **Profesora:** crea simulaciones, selecciona entrevistado y objetivos pedagógicos.
- **Estudiante:** ve las simulaciones disponibles, realiza la entrevista y recibe retroalimentación.

Todavía no existe autenticación real. La selección Profesora / Estudiante sirve para validar el flujo antes de implementar usuarios y contraseñas.

## Panel docente

La profesora puede:

- definir el nombre de una simulación;
- escoger entre los entrevistados IA ya implementados;
- escribir el objetivo particular de la entrevista;
- escribir las instrucciones que verá el estudiante;
- seleccionar objetivos desde el catálogo pedagógico;
- agregar objetivos personalizados;
- guardar la simulación;
- revisar las actividades creadas.

Los objetivos personalizados solicitan:

1. nombre del objetivo;
2. qué conducta se quiere observar;
3. qué evidencia se considerará suficiente.

## Vista estudiante

El estudiante puede:

- ver las simulaciones disponibles;
- conocer el objetivo general de la actividad, sin acceder a los hallazgos ocultos del personaje;
- comenzar la entrevista;
- conversar con el entrevistado IA;
- finalizar y recibir la evaluación correspondiente a los objetivos seleccionados por la profesora.

## Persistencia

Las simulaciones creadas desde el panel se guardan localmente en SQLite:

`data/simulador.db`

La carpeta se crea automáticamente. La base de datos está excluida de GitHub.

Al iniciar por primera vez se carga como actividad inicial la entrevista de Bodega configurada en:

`casos/retailnova/simulacion_bodega.json`

## Arquitectura

- Backend: Python + FastAPI.
- Entrevistado IA: `app/interviewer.py`.
- Evaluador IA: `app/evaluator.py`.
- Persistencia: `app/storage.py` + SQLite.
- Catálogo pedagógico: `config/pedagogia.json`.
- Casos y personajes: JSON.
- Frontend: HTML, CSS y JavaScript.
- Entorno local: `.venv`.

## Configuración local

El archivo `.env` debe contener:

```text
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-5.6-luna
OPENAI_EVALUATOR_MODEL=gpt-5.6-luna
```

Luego:

```text
run.bat
```

y abrir:

`http://127.0.0.1:8000`

## Evaluación

El Hito 4 conserva el evaluador separado del entrevistado y endurece los criterios:

- una pregunta aislada normalmente no basta para un nivel logrado;
- escuchar activamente exige retomar una pista concreta;
- identificar que existe una herramienta no basta para comprender datos y sistemas;
- una secuencia entregada espontáneamente por el entrevistado no demuestra por sí sola que el estudiante levantó el proceso;
- el nivel destacado exige evidencia consistente en más de un momento.

## Alcance del Hito 4

El objetivo de esta versión es validar que el docente pueda configurar una actividad sin editar JSON ni código.

El siguiente hito incorporará usuarios reales, login y persistencia de intentos/resultados por estudiante.
