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
- Autenticación local: `app/auth.py`.
- Persistencia: SQLite mediante `app/storage.py`.
- Casos y personajes: JSON.
- Objetivos pedagógicos: `config/pedagogia.json`.
- Desarrollo local mediante `.venv`.
- Existen dos roles: `teacher` y `student`.

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
- Los objetivos pedagógicos no se definen en AGENTS.md; deben mantenerse en la configuración pedagógica.
- Una simulación debe indicar explícitamente qué objetivos serán evaluados.
- Los objetivos personalizados deben incluir una conducta observable y evidencia suficiente.
- La evaluación debe basarse en evidencia de la transcripción y en los objetivos seleccionados.
- No evaluar como logro una conducta que proviene principalmente de información entregada espontáneamente por el entrevistado.

## Usuarios y permisos

- La primera cuenta creada en una instalación vacía debe ser profesora.
- Solo la profesora puede crear simulaciones y cuentas de estudiantes.
- Solo el estudiante puede iniciar y realizar una entrevista.
- Un estudiante solo puede consultar sus propios intentos.
- La profesora puede consultar los intentos de todos los estudiantes.
- No agregar credenciales predeterminadas ni contraseñas en el repositorio.

## Seguridad

- Nunca guardar claves de API en el código.
- Nunca subir claves de API a GitHub.
- Utilizar variables de entorno para secretos.
- El archivo `.env` debe permanecer excluido mediante `.gitignore`.
- Las contraseñas nunca deben almacenarse en texto plano.
- El prototipo utiliza PBKDF2-HMAC-SHA256 con sal aleatoria para almacenar contraseñas.
- La autenticación usa una cookie HTTPOnly con sesión almacenada en SQLite.
- No exponer hashes, sales ni tokens de sesión mediante endpoints.
- Mantener este mecanismo simple mientras el sistema siga siendo un prototipo local.

## Persistencia

- SQLite se usa mientras sea suficiente para el prototipo.
- No agregar PostgreSQL, ORM ni servicios externos sin una necesidad concreta.
- Los archivos de base de datos local no se suben a GitHub.
- Cada intento debe quedar asociado al estudiante y a la simulación.
- Guardar transcripción y evaluación final del intento.
- No eliminar físicamente una simulación que pueda tener historial; al quitarla del uso docente, marcarla como inactiva para preservar intentos, transcripciones y evaluaciones.
- La interrupción del servidor puede impedir reanudar una entrevista en curso; no implementar reanudación hasta que sea un requisito explícito.

## Verificación

Antes de considerar terminada una modificación:

1. Iniciar la aplicación.
2. Si no existen usuarios, crear la cuenta profesora inicial.
3. Iniciar sesión como profesora.
4. Crear un estudiante.
5. Crear o verificar una simulación.
6. Cerrar sesión.
7. Iniciar sesión como estudiante.
8. Verificar que aparecen las simulaciones disponibles.
9. Realizar y finalizar una entrevista.
10. Confirmar que el intento aparece en el historial del estudiante.
11. Cerrar sesión e iniciar como profesora.
12. Confirmar que el resultado del estudiante puede revisarse.
13. Confirmar que un estudiante no accede al panel docente.
