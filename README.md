# Simulador de Entrevistas

Prototipo educativo para entrenar a estudiantes en entrevistas de levantamiento de información.

## Estado actual

Rama de desarrollo: **v0.7 · Entrevista por voz (7A)**.

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


## Eliminar actividades

La profesora puede eliminar una actividad desde **Actividades creadas**.

La eliminación es segura: la actividad deja de aparecer como disponible para los estudiantes, pero se conserva internamente si existen intentos anteriores. De esta forma no se pierden transcripciones ni evaluaciones históricas.


## Hito 7A · Entrevista por voz

La entrevista puede realizarse oralmente sin perder la modalidad escrita.

Flujo:

```text
Estudiante habla
      ↓
audio del navegador
      ↓
gpt-4o-mini-transcribe
      ↓
pregunta textual
      ↓
motor de Carolina
      ↓
respuesta textual
      ↓
gpt-4o-mini-tts
      ↓
voz de Carolina
```

La pregunta y la respuesta textual quedan en la misma transcripción que utiliza el evaluador pedagógico.

### Uso

Durante una entrevista:

1. Pulsar **Hablar**.
2. Autorizar el micrófono la primera vez que el navegador lo solicite.
3. Formular la pregunta.
4. Pulsar **Detener**.
5. El sistema transcribe la pregunta y la envía a Carolina.
6. Si está activada **Escuchar respuestas de Carolina**, la respuesta se reproduce automáticamente.

El teclado sigue disponible como alternativa.

La interfaz informa que la voz del personaje es generada mediante inteligencia artificial.

### Configuración opcional

Los siguientes valores tienen valores predeterminados, por lo que no es obligatorio agregarlos al `.env` existente:

```text
OPENAI_TRANSCRIBE_MODEL=gpt-4o-mini-transcribe
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=marin
```

El modelo de transcripción admite archivos WebM, que es el formato utilizado habitualmente por MediaRecorder en Chrome/Edge.

## Hito 7B posterior

Después de validar esta modalidad por turnos, la evolución prevista es utilizar Realtime/WebRTC para disminuir la latencia y permitir una conversación oral más natural, manteniendo la evaluación y el control pedagógico ya desarrollados.


## Consumo de tokens y costo

Cada intento completado guarda un resumen de consumo para que la profesora pueda estimar el costo real de operación del simulador.

Se registran:

- tokens reales de entrada y salida utilizados por Carolina;
- tokens reales de entrada y salida utilizados por el evaluador pedagógico;
- tokens de entrada en caché cuando la API los reporta;
- segundos de audio enviados a transcripción;
- uso estimado de la voz sintetizada;
- costo total estimado en USD.

Los precios de referencia incorporados al prototipo corresponden al **24-09-2026**:

| Modelo | Precio usado |
| --- | --- |
| gpt-5.6-luna | USD 0.20 / 1M entrada; USD 0.02 / 1M entrada en caché; USD 1.20 / 1M salida |
| gpt-5.6-terra | USD 2.00 / 1M entrada; USD 0.20 / 1M entrada en caché; USD 12.00 / 1M salida |
| gpt-5.6-sol | USD 4.00 / 1M entrada; USD 0.40 / 1M entrada en caché; USD 20.00 / 1M salida |
| gpt-transcribe | USD 0.0045 / minuto |
| gpt-4o-mini-tts | USD 0.60 / 1M tokens de texto de entrada; USD 12 / 1M tokens de audio de salida |

El costo mostrado es una **estimación**, no una factura. Los tokens de los modelos Responses se obtienen del uso reportado por la API. La transcripción se estima usando la duración grabada y la voz TTS usa una aproximación de duración/tokens de audio.

Los costos se muestran en el historial y en el detalle del intento solo para la profesora.
