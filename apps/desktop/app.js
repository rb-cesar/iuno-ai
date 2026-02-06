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
  bubble.className = `chat-bubble ${role}`;
  bubble.textContent = text;
  chatWindow.appendChild(bubble);
  chatWindow.scrollTop = chatWindow.scrollHeight;
};

const setChatStatus = (state) => {
  chatStatus.textContent = state;
  chatStatus.classList.toggle("connected", state === "Conectado");
  chatStatus.classList.toggle("warning", state === "Reconectando");
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
      toolsList.innerHTML = "<li class='tool-item'>Nenhuma ferramenta encontrada.</li>";
      return;
    }
    tools.forEach((tool) => {
      const item = document.createElement("li");
      item.className = "tool-item";
      item.innerHTML = `
        <h3>${tool.name}</h3>
        <p>${tool.description}</p>
        <p><strong>Args:</strong> ${JSON.stringify(tool.args_schema)}</p>
      `;
      toolsList.appendChild(item);
    });
  } catch (error) {
    toolsList.innerHTML = "<li class='tool-item'>Backend indisponível.</li>";
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
