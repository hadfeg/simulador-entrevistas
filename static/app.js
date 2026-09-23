const startScreen = document.getElementById("start-screen");
const interviewScreen = document.getElementById("interview-screen");
const resultScreen = document.getElementById("result-screen");
const chat = document.getElementById("chat");
const question = document.getElementById("question");
const submitButton = document.querySelector("#question-form button[type='submit']");
const endButton = document.getElementById("end-btn");

const levelNames = {
  no_evidenciado: "No evidenciado",
  en_desarrollo: "En desarrollo",
  logrado: "Logrado",
  destacado: "Destacado"
};

function show(screen) {
  [startScreen, interviewScreen, resultScreen].forEach(s => s.classList.add("hidden"));
  screen.classList.remove("hidden");
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "message " + role;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

async function loadSimulation() {
  try {
    const res = await fetch("/api/simulation");
    const data = await res.json();
    if (!res.ok) return;

    document.getElementById("simulation-name").textContent = data.nombre;
    document.getElementById("activity-objective").textContent = data.objetivo_actividad;
    document.getElementById("student-instructions").textContent = data.instrucciones_estudiante;
  } catch (error) {
    console.error("No fue posible cargar la configuración de la simulación.", error);
  }
}

document.getElementById("start-btn").addEventListener("click", async () => {
  const res = await fetch("/api/start", { method: "POST" });
  const data = await res.json();
  chat.innerHTML = "";
  addMessage("assistant", data.message);
  show(interviewScreen);
  question.focus();
});

document.getElementById("question-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = question.value.trim();
  if (!text) return;

  addMessage("user", text);
  question.value = "";
  question.disabled = true;
  submitButton.disabled = true;
  submitButton.textContent = "Pensando...";

  try {
    const res = await fetch("/api/message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    const data = await res.json();

    if (!res.ok) {
      addMessage("system", data.detail || "No fue posible contactar al entrevistado.");
      return;
    }

    addMessage("assistant", data.message);
  } catch (error) {
    addMessage("system", "No fue posible conectar con el servidor del simulador.");
  } finally {
    question.disabled = false;
    submitButton.disabled = false;
    submitButton.textContent = "Enviar";
    question.focus();
  }
});

document.getElementById("end-btn").addEventListener("click", async () => {
  endButton.disabled = true;
  endButton.textContent = "Evaluando...";

  try {
    const res = await fetch("/api/end", { method: "POST" });
    const data = await res.json();

    if (!res.ok) {
      addMessage("system", data.detail || "No fue posible generar la evaluación.");
      return;
    }

    const evaluation = data.evaluation;
    document.getElementById("global-level").textContent = levelNames[evaluation.nivel_global] || evaluation.nivel_global;
    document.getElementById("questions").textContent = data.questions;
    document.getElementById("objectives-count").textContent = evaluation.resultados.length;
    document.getElementById("summary").textContent = evaluation.sintesis;

    const objectiveResults = document.getElementById("objective-results");
    objectiveResults.innerHTML = "";

    evaluation.resultados.forEach(item => {
      const card = document.createElement("article");
      card.className = "objective-card";

      const evidence = item.evidencia.length
        ? "<ul>" + item.evidencia.map(e => "<li>" + escapeHtml(e) + "</li>").join("") + "</ul>"
        : "<p class=\"muted\">No se identificó evidencia suficiente.</p>";

      card.innerHTML =
        "<div class=\"objective-head\">" +
          "<h4>" + escapeHtml(item.nombre) + "</h4>" +
          "<span class=\"level level-" + item.nivel + "\">" + escapeHtml(levelNames[item.nivel] || item.nivel) + "</span>" +
        "</div>" +
        "<p>" + escapeHtml(item.justificacion) + "</p>" +
        "<strong>Evidencia observada</strong>" + evidence +
        "<strong>Para mejorar</strong>" +
        "<p>" + escapeHtml(item.mejora_sugerida) + "</p>";

      objectiveResults.appendChild(card);
    });

    renderSimpleList("strengths", evaluation.fortalezas);
    renderSimpleList("next-steps", evaluation.proximos_pasos);
    show(resultScreen);
  } catch (error) {
    addMessage("system", "No fue posible conectar con el evaluador.");
  } finally {
    endButton.disabled = false;
    endButton.textContent = "Finalizar entrevista";
  }
});

function renderSimpleList(id, items) {
  const target = document.getElementById(id);
  target.innerHTML = "";
  items.forEach(text => {
    const li = document.createElement("li");
    li.textContent = text;
    target.appendChild(li);
  });
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value;
  return div.innerHTML;
}

document.getElementById("restart-btn").addEventListener("click", () => {
  show(startScreen);
});

loadSimulation();