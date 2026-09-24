# Simulador de Entrevistas

Prototipo educativo para entrenar a estudiantes en entrevistas de levantamiento de información.

## Estado actual

Rama de desarrollo: **v0.5 · Usuarios, login e historial**.

Esta versión incorpora autenticación local y persistencia de resultados.

## Primera ejecución

Si la base de datos todavía no contiene usuarios, la aplicación muestra automáticamente:

**Crear cuenta profesora**

Debes definir:

- nombre;
- usuario;
- contraseña de al menos 8 caracteres.

No existen credenciales predeterminadas en el repositorio.

Después de crear la primera cuenta, la aplicación inicia sesión automáticamente como profesora.

## Rol profesora

La profesora puede:

- crear simulaciones;
- seleccionar entrevistado y objetivos pedagógicos;
- agregar objetivos personalizados;
- crear cuentas de estudiantes;
- revisar los estudiantes registrados;
- revisar intentos y evaluaciones de todos los estudiantes;
- consultar la transcripción asociada a un resultado.

## Rol estudiante

El estudiante puede:

- iniciar sesión con la cuenta creada por la profesora;
- ver las simulaciones disponibles;
- realizar entrevistas;
- recibir retroalimentación;
- consultar sus propios intentos y resultados.

El estudiante no puede acceder al panel docente ni consultar intentos de otros estudiantes.

## Persistencia

La base local SQLite se encuentra en:

`data/simulador.db`

Contiene:

- usuarios;
- sesiones;
- simulaciones;
- intentos;
- transcripciones;
- evaluaciones.

La base está excluida de GitHub mediante `.gitignore`.

## Seguridad del prototipo

- Las contraseñas no se almacenan en texto plano.
- Se utiliza PBKDF2-HMAC-SHA256 con una sal aleatoria por usuario.
- Las sesiones utilizan tokens aleatorios guardados en SQLite.
- El navegador recibe una cookie HTTPOnly.
- Las claves de OpenAI siguen almacenándose exclusivamente en `.env`.
- No existe ninguna contraseña o API key en el repositorio.

Este mecanismo está pensado para el prototipo local. Antes de una publicación institucional o acceso desde Internet se deberá revisar la arquitectura de autenticación y despliegue.

## Arquitectura

- Backend: Python + FastAPI.
- Entrevistado IA: `app/interviewer.py`.
- Evaluador IA: `app/evaluator.py`.
- Autenticación: `app/auth.py`.
- Persistencia: `app/storage.py` + SQLite.
- Catálogo pedagógico: `config/pedagogia.json`.
- Casos y personajes: JSON.
- Frontend: HTML, CSS y JavaScript.

## Configuración de IA

El archivo local `.env` debe contener:

```text
OPENAI_API_KEY=tu_clave
OPENAI_MODEL=gpt-5.6-luna
OPENAI_EVALUATOR_MODEL=gpt-5.6-luna
```

Después ejecutar:

```text
run.bat
```

y abrir:

`http://127.0.0.1:8000`

## Flujo del Hito 5

```text
Profesora
   ↓
login
   ↓
crea estudiante + simulación
   ↓
cierra sesión

Estudiante
   ↓
login
   ↓
realiza entrevista
   ↓
evaluación IA
   ↓
intento guardado

Profesora
   ↓
login
   ↓
revisa resultado + transcripción
```

## Alcance

Esta versión no incorpora todavía:

- recuperación de contraseña;
- inscripción masiva de estudiantes;
- integración con cuentas UCN;
- asignación selectiva de simulaciones por curso o sección;
- despliegue web institucional;
- voz;
- realidad virtual.

Esas capacidades se agregarán solo cuando el flujo básico de usuarios e intentos esté validado.
