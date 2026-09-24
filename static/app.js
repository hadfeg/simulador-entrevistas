const screens = [
  document.getElementById("auth-screen"),
  document.getElementById("teacher-screen"),
  document.getElementById("student-screen"),
  document.getElementById("interview-screen"),
  document.getElementById("result-screen")
];

const chat = document.getElementById("chat");
const question = document.getElementById("question");
const submitButton = document.querySelector("#question-form button[type='submit']");
const endButton = document.getElementById("end-btn");

let currentUser = null;
let catalog = null;
let simulations = [];
let students = [];
let attempts = [];
let currentSimulation = null;
let customObjectiveCounter = 0;

const levelNames = {
  no_evidenciado: "No evidenciado",
  en_desarrollo: "En desarrollo",
  logrado: "Logrado",
  destacado: "Destacado"
};

function show(screen) {
  screens.forEach(item => item.classList.add("hidden"));
  screen.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = value ?? "";
  return div.innerHTML;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();

  if (response.status === 401) {
    currentUser = null;
    showLogin();
    throw new Error(data.detail || "La sesión terminó. Inicia sesión nuevamente.");
  }

  if (!response.ok) {
    throw new Error(data.detail || "Ocurrió un error.");
  }

  return data;
}

function showStatus(id, message, type = "success") {
  const target = document.getElementById(id);
  target.textContent = message;
  target.className = "status-message status-" + type;
}

function clearStatus(id) {
  const target = document.getElementById(id);
  target.textContent = "";
  target.className = "status-message hidden";
}

function showSetup() {
  show(document.getElementById("auth-screen"));
  document.getElementById("setup-panel").classList.remove("hidden");
  document.getElementById("login-panel").classList.add("hidden");
}

function showLogin() {
  show(document.getElementById("auth-screen"));
  document.getElementById("setup-panel").classList.add("hidden");
  document.getElementById("login-panel").classList.remove("hidden");
}

async function routeUser() {
  if (!currentUser) {
    showLogin();
    return;
  }

  if (currentUser.role === "teacher") {
    await loadTeacherDashboard();
    show(document.getElementById("teacher-screen"));
  } else {
    await loadStudentDashboard();
    show(document.getElementById("student-screen"));
  }
}

document.getElementById("setup-form").addEventListener("submit", async event => {
  event.preventDefault();
  clearStatus("setup-message");

  try {
    const data = await fetchJson("/api/auth/setup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        display_name: document.getElementById("setup-display-name").value.trim(),
        username: document.getElementById("setup-username").value.trim(),
        password: document.getElementById("setup-password").value
      })
    });

    currentUser = data.user;
    await routeUser();
  } catch (error) {
    showStatus("setup-message", error.message, "error");
  }
});

document.getElementById("login-form").addEventListener("submit", async event => {
  event.preventDefault();
  clearStatus("login-message");

  try {
    const data = await fetchJson("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: document.getElementById("login-username").value.trim(),
        password: document.getElementById("login-password").value
      })
    });

    currentUser = data.user;
    document.getElementById("login-form").reset();
    await routeUser();
  } catch (error) {
    showStatus("login-message", error.message, "error");
  }
});

document.querySelectorAll(".logout-button").forEach(button => {
  button.addEventListener("click", async () => {
    try {
      await fetchJson("/api/auth/logout", { method: "POST" });
    } catch (error) {
      console.error(error);
    }

    currentUser = null;
    catalog = null;
    simulations = [];
    students = [];
    attempts = [];
    showLogin();
  });
});

async function loadTeacherDashboard() {
  document.getElementById("teacher-welcome").textContent =
    "Hola, " + currentUser.display_name;

  await Promise.all([
    loadCatalog(),
    loadSimulations(),
    loadStudents(),
    loadAttempts()
  ]);

  renderTeacherSimulations();
  renderStudents();
  renderTeacherAttempts();
}

async function loadStudentDashboard() {
  document.getElementById("student-welcome").textContent =
    "Hola, " + currentUser.display_name;

  await Promise.all([
    loadSimulations(),
    loadAttempts()
  ]);

  renderStudentSimulations();
  renderStudentAttempts();
}

async function loadCatalog() {
  catalog = await fetchJson("/api/catalog");

  document.getElementById("general-objective").textContent =
    catalog.objetivo_general;

  const characterSelect = document.getElementById("character-select");
  characterSelect.innerHTML = "";

  catalog.personajes.forEach(character => {
    const option = document.createElement("option");
    option.value = character.id;
    option.textContent =
      character.name + " · " + character.role + " · " + character.company;
    characterSelect.appendChild(option);
  });

  const objectiveCatalog = document.getElementById("objective-catalog");
  objectiveCatalog.innerHTML = "";

  catalog.objetivos.forEach(objective => {
    const label = document.createElement("label");
    label.className = "objective-option";
    label.innerHTML =
      '<input type="checkbox" name="pedagogical-objective" value="' +
      escapeHtml(objective.id) +
      '">' +
      '<span><strong>' +
      escapeHtml(objective.nombre) +
      '</strong><small>' +
      escapeHtml(objective.descripcion) +
      "</small></span>";

    objectiveCatalog.appendChild(label);
  });
}

async function loadSimulations() {
  simulations = await fetchJson("/api/simulations");
}

async function loadStudents() {
  students = await fetchJson("/api/students");
}

async function loadAttempts() {
  attempts = await fetchJson("/api/attempts");
}

function renderTeacherSimulations() {
  const target = document.getElementById("teacher-simulations");
  target.innerHTML = "";

  if (!simulations.length) {
    target.innerHTML = '<p class="muted">Todavía no hay simulaciones creadas.</p>';
    return;
  }

  simulations.forEach(simulation => {
    const article = document.createElement("article");
    article.className = "simulation-card";

    const objectives = (simulation.objetivos || [])
      .map(item => '<span class="chip">' + escapeHtml(item.nombre) + "</span>")
      .join("");

    article.innerHTML =
      '<div class="simulation-card-head">' +
        "<div>" +
          '<span class="small-label">ENTREVISTADO</span>' +
          "<h3>" + escapeHtml(simulation.nombre) + "</h3>" +
          '<p class="muted">' +
            escapeHtml(simulation.character.name) +
            " · " +
            escapeHtml(simulation.character.role) +
          "</p>" +
        "</div>" +
        '<span class="count-badge">' +
          simulation.cantidad_objetivos +
          " objetivos</span>" +
      "</div>" +
      '<p><strong>Objetivo:</strong> ' +
        escapeHtml(simulation.objetivo_actividad) +
      "</p>" +
      '<div class="chips">' + objectives + "</div>" +
      '<div class="simulation-actions">' +
        '<button class="danger delete-simulation" type="button" data-id="' +
          simulation.id +
        '">Eliminar actividad</button>' +
      "</div>";

    target.appendChild(article);
  });

  target.querySelectorAll(".delete-simulation").forEach(button => {
    button.addEventListener("click", async () => {
      const simulationId = Number(button.dataset.id);
      const simulation = simulations.find(item => item.id === simulationId);
      const confirmed = window.confirm(
        '¿Eliminar la actividad "' +
          (simulation ? simulation.nombre : "") +
          '"?\n\nDejará de aparecer a los estudiantes. Los resultados históricos se conservarán.'
      );

      if (!confirmed) return;

      button.disabled = true;

      try {
        const result = await fetchJson(
          "/api/simulations/" + simulationId,
          { method: "DELETE" }
        );

        await loadSimulations();
        renderTeacherSimulations();
        showStatus("teacher-message", result.message);
      } catch (error) {
        button.disabled = false;
        showStatus("teacher-message", error.message, "error");
      }
    });
  });
}

function renderStudentSimulations() {
  const target = document.getElementById("student-simulations");
  target.innerHTML = "";

  if (!simulations.length) {
    target.innerHTML =
      '<div class="card"><p class="muted">No hay simulaciones disponibles.</p></div>';
    return;
  }

  simulations.forEach(simulation => {
    const article = document.createElement("article");
    article.className = "card simulation-card";

    article.innerHTML =
      '<div class="simulation-card-head">' +
        "<div>" +
          '<p class="eyebrow">SIMULACIÓN</p>' +
          "<h2>" + escapeHtml(simulation.nombre) + "</h2>" +
          '<p class="muted">' +
            escapeHtml(simulation.character.name) +
            " · " +
            escapeHtml(simulation.character.role) +
          "</p>" +
        "</div>" +
      "</div>" +
      '<div class="learning-box compact">' +
        "<strong>Objetivo de la actividad</strong>" +
        "<p>" + escapeHtml(simulation.objetivo_actividad) + "</p>" +
      "</div>" +
      '<p class="instruction">' +
        escapeHtml(simulation.instrucciones_estudiante) +
      "</p>" +
      '<button class="primary start-simulation" type="button" data-id="' +
        simulation.id +
      '">Comenzar entrevista</button>';

    target.appendChild(article);
  });

  target.querySelectorAll(".start-simulation").forEach(button => {
    button.addEventListener("click", () =>
      startSimulation(Number(button.dataset.id))
    );
  });
}

function addCustomObjectiveCard() {
  customObjectiveCounter += 1;
  const target = document.getElementById("custom-objectives");

  const card = document.createElement("article");
  card.className = "custom-objective-card";
  card.dataset.customId = String(customObjectiveCounter);

  card.innerHTML =
    '<div class="custom-objective-head">' +
      "<strong>Objetivo personalizado</strong>" +
      '<button type="button" class="text-button remove-custom">Eliminar</button>' +
    "</div>" +
    '<label>Nombre del objetivo' +
      '<input class="custom-name" maxlength="160" placeholder="Ej.: Detectar inconsistencias entre versiones">' +
    "</label>" +
    '<label>Qué quieres observar' +
      '<textarea class="custom-description" rows="2" placeholder="Describe la conducta o aprendizaje que quieres observar."></textarea>' +
    "</label>" +
    '<label>Qué evidencia considerarías suficiente' +
      '<textarea class="custom-evidence" rows="2" placeholder="Ej.: El estudiante identifica una contradicción y la aclara mediante una repregunta."></textarea>' +
    "</label>";

  card.querySelector(".remove-custom").addEventListener("click", () => card.remove());
  target.appendChild(card);
}

function collectCustomObjectives() {
  return [...document.querySelectorAll(".custom-objective-card")].map(card => {
    const nombre = card.querySelector(".custom-name").value.trim();
    const descripcion = card.querySelector(".custom-description").value.trim();
    const evidencia_suficiente =
      card.querySelector(".custom-evidence").value.trim();

    if (!nombre || !descripcion || !evidencia_suficiente) {
      throw new Error(
        "Completa todos los campos de cada objetivo personalizado o elimínalo."
      );
    }

    return { nombre, descripcion, evidencia_suficiente };
  });
}

document.getElementById("add-custom-objective").addEventListener(
  "click",
  addCustomObjectiveCard
);

document.getElementById("simulation-form").addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearStatus("teacher-message");

    try {
      const selectedObjectives = [
        ...document.querySelectorAll(
          'input[name="pedagogical-objective"]:checked'
        )
      ].map(input => input.value);

      const customObjectives = collectCustomObjectives();

      if (!selectedObjectives.length && !customObjectives.length) {
        throw new Error("Selecciona o agrega al menos un objetivo.");
      }

      const created = await fetchJson("/api/simulations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: document.getElementById("simulation-title").value.trim(),
          personaje: document.getElementById("character-select").value,
          objetivo_actividad:
            document.getElementById("activity-objective-input").value.trim(),
          instrucciones_estudiante:
            document.getElementById("student-instructions-input").value.trim(),
          objetivos_evaluados: selectedObjectives,
          objetivos_personalizados: customObjectives
        })
      });

      showStatus(
        "teacher-message",
        'Simulación "' + created.nombre + '" guardada correctamente.'
      );

      document.getElementById("simulation-form").reset();
      document.getElementById("custom-objectives").innerHTML = "";
      await loadSimulations();
      renderTeacherSimulations();
    } catch (error) {
      showStatus("teacher-message", error.message, "error");
    }
  }
);

document.getElementById("student-form").addEventListener(
  "submit",
  async event => {
    event.preventDefault();
    clearStatus("student-create-message");

    try {
      const created = await fetchJson("/api/students", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          display_name:
            document.getElementById("student-display-name").value.trim(),
          username:
            document.getElementById("student-username").value.trim(),
          password: document.getElementById("student-password").value
        })
      });

      showStatus(
        "student-create-message",
        'Estudiante "' + created.display_name + '" creado correctamente.'
      );

      document.getElementById("student-form").reset();
      await loadStudents();
      renderStudents();
    } catch (error) {
      showStatus("student-create-message", error.message, "error");
    }
  }
);

function renderStudents() {
  const target = document.getElementById("student-list");
  target.innerHTML = "";

  if (!students.length) {
    target.innerHTML = '<p class="muted">Todavía no hay estudiantes registrados.</p>';
    return;
  }

  students.forEach(student => {
    const row = document.createElement("div");
    row.className = "simple-row";
    row.innerHTML =
      "<strong>" + escapeHtml(student.display_name) + "</strong>" +
      '<span class="muted">@' + escapeHtml(student.username) + "</span>";
    target.appendChild(row);
  });
}

function formatDate(value) {
  if (!value) return "En curso";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function renderTeacherAttempts() {
  renderAttempts("teacher-attempts", attempts, true);
}

function renderStudentAttempts() {
  renderAttempts("student-attempts", attempts, false);
}

function renderAttempts(targetId, rows, showStudent) {
  const target = document.getElementById(targetId);
  target.innerHTML = "";

  if (!rows.length) {
    target.innerHTML = '<p class="muted">Todavía no hay intentos registrados.</p>';
    return;
  }

  rows.forEach(attempt => {
    const article = document.createElement("article");
    article.className = "attempt-card";

    const studentLine = showStudent
      ? '<p class="muted">' + escapeHtml(attempt.display_name || attempt.username) + "</p>"
      : "";

    const level = attempt.completed
      ? escapeHtml(levelNames[attempt.global_level] || attempt.global_level || "Evaluado")
      : "En curso";

    article.innerHTML =
      '<div class="attempt-main">' +
        "<div>" +
          "<strong>" + escapeHtml(attempt.simulation_name) + "</strong>" +
          studentLine +
          '<small class="muted">' + escapeHtml(formatDate(attempt.completed_at || attempt.started_at)) + "</small>" +
        "</div>" +
        '<div class="attempt-actions">' +
          '<span class="level">' + level + "</span>" +
          (attempt.completed
            ? '<button class="secondary view-attempt" type="button" data-id="' + attempt.id + '">Ver resultado</button>'
            : "") +
        "</div>" +
      "</div>";

    target.appendChild(article);
  });

  target.querySelectorAll(".view-attempt").forEach(button => {
    button.addEventListener("click", () =>
      viewAttempt(Number(button.dataset.id))
    );
  });
}

async function startSimulation(simulationId) {
  try {
    const data = await fetchJson(
      "/api/simulations/" + simulationId + "/start",
      { method: "POST" }
    );

    currentSimulation = data.simulation;
    document.getElementById("interview-title").textContent =
      currentSimulation.nombre;
    document.getElementById("interview-character").textContent =
      data.character.name + " · " + data.character.role;
    document.getElementById("interview-objective").textContent =
      currentSimulation.objetivo_actividad;

    chat.innerHTML = "";
    addMessage("assistant", data.message);
    show(document.getElementById("interview-screen"));
    question.focus();
  } catch (error) {
    alert(error.message);
  }
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "message " + role;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

document.getElementById("question-form").addEventListener(
  "submit",
  async event => {
    event.preventDefault();

    const text = question.value.trim();
    if (!text) return;

    addMessage("user", text);
    question.value = "";
    question.disabled = true;
    submitButton.disabled = true;
    submitButton.textContent = "Pensando...";

    try {
      const data = await fetchJson("/api/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });

      addMessage("assistant", data.message);
    } catch (error) {
      addMessage("system", error.message);
    } finally {
      question.disabled = false;
      submitButton.disabled = false;
      submitButton.textContent = "Enviar";
      question.focus();
    }
  }
);

document.getElementById("end-btn").addEventListener("click", async () => {
  endButton.disabled = true;
  endButton.textContent = "Evaluando...";

  try {
    const data = await fetchJson("/api/end", { method: "POST" });
    renderEvaluation(
      data.evaluation,
      data.questions,
      data.transcript
    );
    show(document.getElementById("result-screen"));
  } catch (error) {
    addMessage("system", error.message);
  } finally {
    endButton.disabled = false;
    endButton.textContent = "Finalizar entrevista";
  }
});

async function viewAttempt(attemptId) {
  try {
    const attempt = await fetchJson("/api/attempts/" + attemptId);

    if (!attempt.evaluation) {
      alert("Este intento todavía no tiene una evaluación final.");
      return;
    }

    renderEvaluation(
      attempt.evaluation,
      attempt.question_count,
      attempt.transcript
    );
    show(document.getElementById("result-screen"));
  } catch (error) {
    alert(error.message);
  }
}

function renderEvaluation(evaluation, questionCount, transcript) {
  document.getElementById("global-level").textContent =
    levelNames[evaluation.nivel_global] || evaluation.nivel_global;
  document.getElementById("questions").textContent = questionCount;
  document.getElementById("objectives-count").textContent =
    evaluation.resultados.length;
  document.getElementById("summary").textContent = evaluation.sintesis;

  const objectiveResults = document.getElementById("objective-results");
  objectiveResults.innerHTML = "";

  evaluation.resultados.forEach(item => {
    const card = document.createElement("article");
    card.className = "objective-card";

    const evidence = item.evidencia.length
      ? "<ul>" +
        item.evidencia
          .map(value => "<li>" + escapeHtml(value) + "</li>")
          .join("") +
        "</ul>"
      : '<p class="muted">No se identificó evidencia suficiente.</p>';

    card.innerHTML =
      '<div class="objective-head">' +
        "<h4>" + escapeHtml(item.nombre) + "</h4>" +
        '<span class="level level-' + item.nivel + '">' +
          escapeHtml(levelNames[item.nivel] || item.nivel) +
        "</span>" +
      "</div>" +
      "<p>" + escapeHtml(item.justificacion) + "</p>" +
      "<strong>Evidencia observada</strong>" +
      evidence +
      "<strong>Para mejorar</strong>" +
      "<p>" + escapeHtml(item.mejora_sugerida) + "</p>";

    objectiveResults.appendChild(card);
  });

  renderSimpleList("strengths", evaluation.fortalezas);
  renderSimpleList("next-steps", evaluation.proximos_pasos);
  renderTranscript(transcript || []);
}

function renderSimpleList(id, items) {
  const target = document.getElementById(id);
  target.innerHTML = "";

  items.forEach(text => {
    const li = document.createElement("li");
    li.textContent = text;
    target.appendChild(li);
  });
}

function renderTranscript(transcript) {
  const target = document.getElementById("saved-transcript");
  target.innerHTML = "";

  transcript.forEach(item => {
    const row = document.createElement("div");
    row.className = "transcript-row";
    const who = item.role === "user" ? "Estudiante" : "Entrevistada";
    row.innerHTML =
      "<strong>" + who + ":</strong> " + escapeHtml(item.text);
    target.appendChild(row);
  });
}

document.getElementById("result-back-btn").addEventListener("click", async () => {
  currentSimulation = null;

  if (currentUser.role === "teacher") {
    await loadTeacherDashboard();
    show(document.getElementById("teacher-screen"));
  } else {
    await loadStudentDashboard();
    show(document.getElementById("student-screen"));
  }
});

async function initialize() {
  try {
    const status = await fetchJson("/api/auth/status");

    if (status.needs_setup) {
      showSetup();
      return;
    }

    if (!status.user) {
      showLogin();
      return;
    }

    currentUser = status.user;
    await routeUser();
  } catch (error) {
    console.error(error);
    showLogin();
  }
}

initialize();
