# AGENTS.md

## Objetivo del proyecto

Construir un simulador educativo de entrevistas para entrenar a estudiantes en levantamiento de información.

El estudiante debe entrevistar personajes simulados, descubrir información relevante mediante preguntas y repreguntas y, posteriormente, recibir retroalimentación sobre su desempeño.

## Principios de desarrollo

- Mantener la solución lo más simple posible.
- Crear solo los archivos estrictamente necesarios.
- No agregar frameworks o dependencias sin una necesidad concreta.
- Hacer cambios pequeños y verificables.
- Mantener el código fácil de comprender.
- Mantener los textos claros y concretos.
- No modificar componentes que no estén relacionados con la tarea solicitada.
- Reutilizar la estructura existente antes de crear componentes nuevos.

## Arquitectura actual

- Backend: Python + FastAPI.
- Frontend: HTML, CSS y JavaScript.
- Casos y personajes: JSON.
- Objetivos pedagógicos: `config/pedagogia.json`.
- Configuración de cada simulación: archivo de simulación del caso.
- Desarrollo local mediante `.venv`.

## Reglas pedagógicas

- El entrevistado debe interpretar su personaje durante toda la entrevista.
- El entrevistado no debe enseñar al estudiante durante la entrevista.
- El entrevistado no debe evaluar al estudiante durante la entrevista.
- El personaje no debe entregar espontáneamente toda la información.
- La información debe revelarse progresivamente según las preguntas del estudiante.
- El personaje solo debe responder utilizando información que pertenece a su rol.
- El personaje no debe inventar hechos que no formen parte del caso.
- El estudiante debe descubrir información mediante preguntas y repreguntas.
- El evaluador debe estar separado del entrevistado.
- La evaluación se realiza después de finalizar la entrevista.
- Los objetivos pedagógicos no se definen en AGENTS.md; deben mantenerse en la configuración pedagógica para que puedan ser seleccionados por el docente.
- La evaluación debe basarse en evidencia de la transcripción y en los objetivos seleccionados para esa simulación.

## Seguridad

- Nunca guardar claves de API en el código.
- Nunca subir claves de API a GitHub.
- Utilizar variables de entorno para secretos.
- El archivo `.env` debe permanecer excluido mediante `.gitignore`.

## Verificación

Antes de considerar terminada una modificación:

1. Iniciar la aplicación.
2. Verificar que la página principal carga correctamente.
3. Comenzar una entrevista.
4. Realizar varias preguntas.
5. Finalizar la entrevista.
6. Verificar que aparece la evaluación por objetivos.
7. Confirmar que no hay errores visibles.
