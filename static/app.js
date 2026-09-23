const startScreen = document.getElementById("start-screen");
const interviewScreen = document.getElementById("interview-screen");
const resultScreen = document.getElementById("result-screen");
const chat = document.getElementById("chat");
const question = document.getElementById("question");

function show(screen) {
  [startScreen, interviewScreen, resultScreen].forEach(s => s.classList.add("hidden"));
  screen.classList.remove("hidden");
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
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
  const res = await fetch("/api/message", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text })
  });
  const data = await res.json();
  addMessage("assistant", data.message || "No pude responder esa pregunta.");
  question.focus();
});

document.getElementById("end-btn").addEventListener("click", async () => {
  const res = await fetch("/api/end", { method: "POST" });
  const data = await res.json();
  document.getElementById("coverage").textContent = `${data.coverage}%`;
  document.getElementById("questions").textContent = data.questions;
  document.getElementById("findings").textContent = `${data.discovered_count}/${data.total}`;
  const discoveries = document.getElementById("discoveries");
  discoveries.innerHTML = "";
  data.items.forEach(item => {
    const row = document.createElement("div");
    row.className = `discovery ${item.discovered ? "ok" : "miss"}`;
    row.innerHTML = `<span>${item.discovered ? "✓" : "○"}</span><span>${item.description}</span>`;
    discoveries.appendChild(row);
  });
  const feedback = document.getElementById("feedback");
  feedback.innerHTML = "";
  data.feedback.forEach(text => { const li = document.createElement("li"); li.textContent = text; feedback.appendChild(li); });
  show(resultScreen);
});

document.getElementById("restart-btn").addEventListener("click", () => show(startScreen));