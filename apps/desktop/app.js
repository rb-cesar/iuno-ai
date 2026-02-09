const backendUrl = "http://localhost:8000";

const healthStatus = document.getElementById("health-status");
const backendVersion = document.getElementById("backend-version");
const refreshHealth = document.getElementById("refresh-health");

const toolsList = document.getElementById("tools-list");
const refreshTools = document.getElementById("refresh-tools");

const chatWindow = document.getElementById("chat-window");
const chatInput = document.getElementById("chat-input");
const chatSend = document.getElementById("chat-send");
const chatStatus = document.getElementById("chat-status");

const toolNameInput = document.getElementById("tool-name");
const toolArgsInput = document.getElementById("tool-args");
const runToolButton = document.getElementById("run-tool");
const toolResult = document.getElementById("tool-result");

const addChatBubble = (text, role) => {
  const bubble = document.createElement("div");
  const base =
    "max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed shadow-sm";
  const roleClass =
    role === "user"
      ? "self-end bg-blue-500/20 text-slate-100"
      : "self-start bg-slate-800/70 text-slate-100";
  bubble.className = `${base} ${roleClass}`;
  bubble.textContent = text;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
};

const setChatStatus = (state) => {
  chatStatus.textContent = state;
  chatStatus.classList.toggle("bg-emerald-500/20", state === "Conectado");
  chatStatus.classList.toggle("text-emerald-300", state === "Conectado");
  chatStatus.classList.toggle("bg-amber-500/20", state === "Reconectando");
  chatStatus.classList.toggle("text-amber-300", state === "Reconectando");
};

const fetchHealth = async () => {
  try {
    healthStatus.textContent = "Carregando...";
    const response = await fetch(`${backendUrl}/health`);
    const data = await response.json();
    healthStatus.textContent = data.status === "ok" ? "Online" : "Indisponível";
    backendVersion.textContent = `Versão: ${data.version ?? "-"}`;
  } catch (error) {
    healthStatus.textContent = "Offline";
    backendVersion.textContent = "Versão: —";
  }
};

const fetchTools = async () => {
  toolsList.innerHTML = "";
  try {
    const response = await fetch(`${backendUrl}/tools`);
    const data = await response.json();
    const tools = data.tools ?? [];
    if (tools.length === 0) {
      toolsList.innerHTML =
        "<li class='rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-400'>Nenhuma ferramenta encontrada.</li>";
      return;
    }
    tools.forEach((tool) => {
      const item = document.createElement("li");
      item.className = "rounded-xl border border-slate-800 bg-slate-950/60 p-3";
      item.innerHTML = `
        <h3 class="text-sm font-semibold text-slate-100">${tool.name}</h3>
        <p class="mt-1 text-xs text-slate-400">${tool.description}</p>
        <p class="mt-2 text-xs text-slate-500"><strong>Args:</strong> ${JSON.stringify(
          tool.args_schema,
        )}</p>
      `;
      toolsList.appendChild(item);
    });
  } catch (error) {
    toolsList.innerHTML =
      "<li class='rounded-xl border border-slate-800 bg-slate-950/60 p-3 text-sm text-slate-400'>Backend indisponível.</li>";
  }
};

const executeTool = async () => {
  toolResult.textContent = "Resultado: executando...";
  try {
    const name = toolNameInput.value.trim();
    if (!name) {
      toolResult.textContent = "Resultado: informe o nome da ferramenta.";
      return;
    }
    const args = toolArgsInput.value ? JSON.parse(toolArgsInput.value) : {};
    const response = await fetch(`${backendUrl}/tools/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, args }),
    });
    const data = await response.json();
    toolResult.textContent = `Resultado: ${JSON.stringify(data, null, 2)}`;
  } catch (error) {
    toolResult.textContent = "Resultado: erro ao executar ferramenta.";
  }
};

let socket;
let reconnectTimer;

const connectChat = () => {
  if (socket) {
    socket.close();
  }
  setChatStatus("Conectando...");
  socket = new WebSocket(`ws://localhost:8000/chat`);

  socket.addEventListener("open", () => {
    setChatStatus("Conectado");
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "assistant_chunk") {
      const lastBubble = chatWindow.lastElementChild;
      if (!lastBubble || !lastBubble.classList.contains("assistant")) {
        addChatBubble(data.content, "assistant");
      } else {
        lastBubble.textContent += data.content;
      }
    }
    if (data.type === "assistant_done") {
      addChatBubble(data.content, "assistant");
    }
    if (data.type === "error") {
      addChatBubble(`Erro: ${data.message}`, "assistant");
    }
  });

  socket.addEventListener("close", () => {
    setChatStatus("Reconectando");
    reconnectTimer = setTimeout(connectChat, 3000);
  });
};

const sendChatMessage = () => {
  const message = chatInput.value.trim();
  if (!message) return;
  addChatBubble(message, "user");
  socket?.send(JSON.stringify({ type: "user_message", content: message }));
  chatInput.value = "";
};

refreshHealth.addEventListener("click", fetchHealth);
refreshTools.addEventListener("click", fetchTools);
runToolButton.addEventListener("click", executeTool);
chatSend.addEventListener("click", sendChatMessage);
chatInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    sendChatMessage();
  }
});

fetchHealth();
fetchTools();
connectChat();

window.addEventListener("beforeunload", () => {
  clearTimeout(reconnectTimer);
  socket?.close();
});
