# Simulador de Entrevistas

Prototipo educativo para entrenar a estudiantes en entrevistas de levantamiento de información.

## Estado actual

Versión base: **v0.1.1**.

Esta versión:
- presenta el caso RetailNova;
- incluye a Carolina Morales, Encargada de Bodega;
- permite realizar la entrevista por texto;
- utiliza reglas controladas para responder;
- genera una retroalimentación básica al finalizar;
- todavía no utiliza IA generativa, voz ni realidad virtual.

## Arquitectura

- Backend: Python + FastAPI.
- Frontend: HTML, CSS y JavaScript.
- Casos y personajes: JSON.
- Entorno local: `.venv`.

## Ejecución en Windows

1. Tener Python instalado.
2. Ejecutar `run.bat`.
3. Abrir `http://127.0.0.1:8000`.

`run.bat` crea un entorno virtual `.venv` para mantener aisladas las dependencias del proyecto.

## Próximo hito técnico

Reemplazar progresivamente el motor de respuestas por reglas por un entrevistado basado en IA, manteniendo separadas las funciones de entrevistado y evaluador.