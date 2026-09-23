from pathlib import Path
import json
import re
import unicodedata

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
CASE_DIR = ROOT / "casos" / "retailnova"

with open(CASE_DIR / "bodega.json", encoding="utf-8") as f:
    CHARACTER = json.load(f)

app = FastAPI(title="Simulador de Entrevistas RetailNova v0.1.1")

STATE = {"messages": [], "discovered": set(), "question_count": 0}

class MessageIn(BaseModel):
    text: str

def reset_state():
    STATE["messages"] = []
    STATE["discovered"] = set()
    STATE["question_count"] = 0

def normalize(text: str) -> str:
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", text)

def contains_any(q, phrases):
    return any(p in q for p in phrases)

def carolina_answer(question: str) -> str:
    q = normalize(question)

    if contains_any(q, ["que haces", "cual es tu funcion", "cual es tu cargo", "responsabilidades", "tu funcion", "tu trabajo"]):
        STATE["discovered"].add("responsable")
        return "Estoy a cargo de coordinar la recepción y almacenamiento de la mercadería, mantener el inventario lo más actualizado posible y preparar la salida de productos cuando Ventas o despacho lo solicita."

    if contains_any(q, ["dia de trabajo", "dia normal", "jornada normal", "rutina", "como es un dia", "que haces normalmente", "trabajo normal"]):
        STATE["discovered"].add("recepcion")
        return "Normalmente empiezo revisando si quedaron movimientos pendientes del día anterior. Después recibimos mercadería, comprobamos cantidades, ubicamos los productos y vamos registrando los movimientos. Durante el día también preparamos productos que deben salir de bodega y atendemos diferencias o devoluciones cuando aparecen."

    if contains_any(q, ["despachas", "despacho", "salida de un producto", "salida del producto", "sacar un producto", "sale un producto", "productos salen", "entrega de producto", "preparar pedido", "preparacion de pedido"]):
        return "Cuando hay una solicitud de salida, primero revisamos qué producto y cantidad se necesita. Buscamos el producto en bodega, comprobamos físicamente la cantidad y preparamos la entrega. Después corresponde registrar esa salida para que el stock quede actualizado."

    if contains_any(q, ["como reciben", "recepcion", "cuando llega mercaderia", "cuando llegan productos", "llega mercaderia", "entrada de producto", "entrada de mercaderia"]):
        STATE["discovered"].add("recepcion")
        return "Cuando llega la mercadería revisamos las cantidades y el estado de los productos. Si todo está correcto, dejamos registrado lo recibido y después ubicamos los productos en la bodega."

    if contains_any(q, ["excel", "planilla", "como registran", "donde registran", "anotan", "registro de entrada", "registro de salida", "registran los movimientos"]):
        STATE["discovered"].add("excel")
        return "No siempre lo ingresamos inmediatamente al sistema. En algunos momentos usamos primero una planilla Excel para registrar movimientos y luego esa información se pasa al sistema."

    if contains_any(q, ["cuando actualizan", "en que momento actualizan", "cada cuanto actualizan", "final del dia", "actualizan el sistema", "cuando se actualiza"]):
        STATE["discovered"].add("fin_dia")
        return "Depende de la carga de trabajo. Cuando estamos con muchas recepciones o despachos, algunos movimientos pueden quedar pendientes y el sistema termina actualizándose al final del día."

    if contains_any(q, ["quien actualiza", "quien registra", "quien anota", "responsable de registrar", "responsable de actualizar"]):
        STATE["discovered"].add("responsable")
        return "Lo hacemos desde Bodega. No siempre es una sola persona; depende del turno y de quién esté atendiendo la recepción o la salida."

    if contains_any(q, ["stock", "inventario", "diferencias", "diferencia", "cantidad disponible", "stock fisico", "stock del sistema"]):
        STATE["discovered"].add("ventas_stock")
        return "Sí, a veces aparecen diferencias entre lo que tenemos físicamente y lo que muestra el sistema. Puede ocurrir cuando todavía quedan movimientos pendientes de registrar."

    if contains_any(q, ["ventas", "area de ventas", "vendedores", "cuando ventas consulta"]):
        STATE["discovered"].add("ventas_stock")
        return "Ventas consulta el stock en el sistema para saber qué puede ofrecer. El problema es que, si nosotros aún no hemos terminado de registrar los movimientos, ellos pueden ver una cantidad que todavía no refleja exactamente lo que hay físicamente."

    if contains_any(q, ["devolucion", "devoluciones", "devuelven", "producto devuelto", "cliente devuelve"]):
        STATE["discovered"].add("devoluciones")
        return "Las devoluciones son más variables. Primero hay que revisar el motivo y el estado del producto. Dependiendo de eso, no siempre se sigue exactamente el mismo procedimiento."

    if contains_any(q, ["problema", "problemas", "dificultad", "dificultades", "que falla", "que les complica", "principal inconveniente"]):
        return "Lo que más nos complica es mantener todos los movimientos actualizados cuando hay mucha actividad. Si una entrada o salida queda pendiente de registrar, después pueden aparecer diferencias de stock."

    if contains_any(q, ["necesitan automatizar", "deberian automatizar", "deberian cambiar", "seria mejor", "el problema es que necesitan", "la solucion seria"]):
        return "Podría ser, pero no estoy segura. Prefiero explicarte cómo trabajamos actualmente y qué dificultades tenemos; después ustedes pueden analizar qué solución tendría sentido."

    if contains_any(q, ["por que", "por que pasa", "a que te refieres", "me puedes explicar", "puedes profundizar", "como asi", "que ocurre entonces"]):
        return "Principalmente porque durante los momentos de mayor carga priorizamos recibir o despachar los productos físicamente, y algunos registros quedan para después. Ahí es donde se pueden generar diferencias."

    return "No estoy segura de haber entendido exactamente qué quieres saber. ¿Podrías preguntarme por una actividad concreta, por ejemplo recepción, almacenamiento, salida de productos, inventario o devoluciones?"

@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")

@app.post("/api/start")
def start():
    reset_state()
    opening = "Hola, soy Carolina Morales, encargada de Bodega de RetailNova. ¿En qué te puedo ayudar?"
    STATE["messages"].append({"role": "assistant", "text": opening})
    return {"character": {"name": CHARACTER["nombre"], "role": CHARACTER["cargo"], "company": CHARACTER["empresa"]}, "message": opening}

@app.post("/api/message")
def message(data: MessageIn):
    text = data.text.strip()
    if not text:
        return {"error": "La pregunta no puede estar vacía."}
    STATE["question_count"] += 1
    STATE["messages"].append({"role": "user", "text": text})
    answer = carolina_answer(text)
    STATE["messages"].append({"role": "assistant", "text": answer})
    return {"message": answer}

@app.post("/api/end")
def end():
    total = len(CHARACTER["hallazgos_ocultos"])
    discovered_ids = STATE["discovered"]
    items = [{"id": item["id"], "description": item["descripcion"], "discovered": item["id"] in discovered_ids} for item in CHARACTER["hallazgos_ocultos"]]
    q_count = STATE["question_count"]
    coverage = round((len(discovered_ids) / total) * 100) if total else 0
    feedback = []
    if coverage >= 80:
        feedback.append("Lograste una cobertura alta de los aspectos relevantes del proceso.")
    elif coverage >= 50:
        feedback.append("Lograste una cobertura parcial. Conviene profundizar en los aspectos que quedaron abiertos.")
    else:
        feedback.append("La entrevista quedó superficial. Necesitas explorar con mayor detalle el proceso y sus excepciones.")
    if q_count < 5:
        feedback.append("Realizaste pocas preguntas; prueba utilizar repreguntas antes de cerrar un tema.")
    else:
        feedback.append("La cantidad de preguntas permitió desarrollar una entrevista con cierto nivel de profundidad.")
    return {"questions": q_count, "coverage": coverage, "discovered_count": len(discovered_ids), "total": total, "items": items, "feedback": feedback, "transcript": STATE["messages"]}

app.mount("/static", StaticFiles(directory=STATIC), name="static")