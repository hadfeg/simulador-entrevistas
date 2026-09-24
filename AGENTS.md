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
- Entrevistado IA: `app/interviewer.py`.
- Evaluador IA: `app/evaluator.py`.
- Persistencia local de simulaciones: SQLite mediante `app/storage.py`.
- Casos y personajes: JSON.
- Objetivos pedagógicos: `config/pedagogia.json`.
- Desarrollo local mediante `.venv`.
- El panel docente y la vista estudiante comparten la misma aplicación.
- El login real todavía no forma parte de esta versión.

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
- Una simulación debe indicar explícitamente qué objetivos serán evaluados.
- Los objetivos personalizados deben incluir una conducta observable y evidencia suficiente.
- La evaluación debe basarse en evidencia de la transcripción y en los objetivos seleccionados para esa simulación.
- No evaluar como logro una conducta que proviene principalmente de información entregada espontáneamente por el entrevistado.

## Persistencia

- SQLite se usa solo para mantener el prototipo simple.
- No agregar PostgreSQL, ORM ni servicios externos mientras SQLite sea suficiente.
- Los archivos de base de datos local no se suben a GitHub.
- El catálogo pedagógico permanece en JSON; las simulaciones creadas por el docente se guardan en SQLite.

## Seguridad

- Nunca guardar claves de API en el código.
- Nunca subir claves de API a GitHub.
- Utilizar variables de entorno para secretos.
- El archivo `.env` debe permanecer excluido mediante `.gitignore`.

## Verificación

Antes de considerar terminada una modificación:

1. Iniciar la aplicación.
2. Entrar a la vista Profesora.
3. Crear una simulación con al menos un objetivo.
4. Confirmar que aparece en Actividades creadas.
5. Entrar a la vista Estudiante.
6. Confirmar que la simulación está disponible.
7. Comenzar una entrevista.
8. Realizar varias preguntas.
9. Finalizar la entrevista.
10. Verificar que la evaluación usa los objetivos seleccionados.
11. Confirmar que no hay errores visibles.
