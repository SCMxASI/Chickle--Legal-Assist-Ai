const container = document.querySelector(".container");
const chatsContainer = document.querySelector(".chats-container");
const promptForm = document.querySelector(".prompt-form");
const promptInput = promptForm.querySelector(".prompt-input");
const fileInput = promptForm.querySelector("#file-input");
const fileUploadWrapper = promptForm.querySelector(".file-upload-wrapper");
const themeToggleBtn = document.querySelector("#theme-toggle-btn");
let hasShrunk = false;
const navbar = document.querySelector(".navbar");
let userScrolled = false;
let stopTyping = false;

// API Setup
let controller, typingInterval;
const chatHistory = [];
const userData = { message: "", file: {} };
function cleanLLMResponse(text) {
  return text
    .replace(/^(AI|Bot):\s*/i, '')
    .replace(/^(Sure,|Certainly,|Okay,|Here(?:’|')s|Let me explain).*?:\s*/i, '')
    .replace(/As an AI language model.*?(\.|\n)/i, '')
    .replace(/\s{2,}/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function markdownToPlainText(mdText) {
  // Create a temp element and set rendered HTML as its innerHTML
  const html = window.markdownit().render(mdText);
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  // Use textContent to extract plain text
  return tempDiv.textContent || tempDiv.innerText || "";
}

// Set initial theme from local storage
const isLightTheme = localStorage.getItem("themeColor") === "light_mode";
document.body.classList.toggle("light-theme", isLightTheme);
themeToggleBtn.textContent = isLightTheme ? "dark_mode" : "light_mode";

// Function to create message elements
const createMessageElement = (content, ...classes) => {
  const div = document.createElement("div");
  div.classList.add("message", ...classes);
  div.innerHTML = content;
  return div;
};

let scrollLocked = true;
chatsContainer.addEventListener("scroll", () => {
  const nearBottom = chatsContainer.scrollHeight - chatsContainer.scrollTop <= chatsContainer.clientHeight + 40;
  scrollLocked = nearBottom;
});

function scrollToBottom(force = false) {
  if (scrollLocked || force) {
    chatsContainer.scrollTop = chatsContainer.scrollHeight;
  }
}

// Simulate typing effect for bot responses
// Update typingEffect function for proper Markdown rendering
const typingEffect = (markdownText, textElement, botMsgDiv) => {
  return new Promise((resolve) => {
    let charIndex = 0;
    let currentRaw = "";
    const md = window.markdownit({
      html: false,       // Disable HTML tags
      breaks: true,
      linkify: true,
      typographer: true
    });

    const typeChar = () => {
      if (charIndex < markdownText.length && !stopTyping) {
        currentRaw += markdownText[charIndex++];
        try {
          textElement.innerHTML = md.render(currentRaw);
        } catch (e) {
          console.error("Markdown rendering error:", e);
          textElement.textContent = currentRaw;  // Fallback to plain text
        }
        scrollToBottom();
        setTimeout(typeChar, 0.5);
      } else {
        botMsgDiv.classList.remove("loading");
        document.body.classList.remove("bot-responding");
        resolve();
      }
    };

    typeChar();
  });
};




const generateResponse = async (botMsgDiv) => {
  const textElement = botMsgDiv.querySelector(".message-text");
  if (controller) controller.abort();
  controller = new AbortController();

  chatHistory.push({
    role: "user",
    parts: [
      { text: userData.message },
      ...(userData.file.data
        ? [
            {
              inline_data: (({ fileName, isImage, ...rest }) => rest)(userData.file),
            },
          ]
        : []),
    ],
  });

  try {
    let response;

    if (userData.file.data) {
      const formData = new FormData();
      formData.append("query", userData.message);

      const byteString = atob(userData.file.data);
      const byteArray = new Uint8Array(byteString.length);
      for (let i = 0; i < byteString.length; i++) {
        byteArray[i] = byteString.charCodeAt(i);
      }

      const blob = new Blob([byteArray], { type: userData.file.mime_type });
      formData.append("file", blob, userData.file.fileName);

      response = await fetch("http://192.168.127.190:5000/ask", {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
    } else {
      response = await fetch("http://192.168.127.190:5000/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userData.message }),
        signal: controller.signal,
      });
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.error.message);

    const responseText = cleanLLMResponse(data.response.trim());
    await typingEffect(responseText, textElement, botMsgDiv);
    chatsContainer.scrollTo(0, chatsContainer.scrollHeight);
    chatHistory.push({ role: "model", parts: [{ text: responseText }] });
  } catch (error) {
    textElement.innerHTML = `<p class="error">${error.name === "AbortError" ? "❌ Response generation stopped." : error.message}</p>`;
    textElement.style.color = "#d62939";
    botMsgDiv.classList.remove("loading");
    scrollToBottom();
    document.body.classList.remove("bot-responding");
  } finally {
    userData.file = {};
  }
};

const handleFormSubmit = async (e) => {
  e.preventDefault();
  stopTyping = false;
  if (!hasShrunk) {
    navbar.classList.add("shrink");
    hasShrunk = true;
  }
  const userMessage = promptInput.value.trim();
  if (!userMessage || document.body.classList.contains("bot-responding")) return;
  userData.message = userMessage;
  promptInput.value = "";
  document.body.classList.add("chats-active", "bot-responding");
  fileUploadWrapper.classList.remove("file-attached", "img-attached", "active");

  const userMsgHTML = `
    <p class="message-text"></p>
    ${userData.file.data ? (userData.file.isImage ? `<img src="data:${userData.file.mime_type};base64,${userData.file.data}" class="img-attachment" />` : `<p class="file-attachment"><span class="material-symbols-rounded">description</span>${userData.file.fileName}</p>`) : ""}
  `;
  const userMsgDiv = createMessageElement(userMsgHTML, "user-message");
  userMsgDiv.querySelector(".message-text").textContent = userData.message;
  chatsContainer.appendChild(userMsgDiv);
  scrollToBottom();

  setTimeout(async () => {
    const botMsgHTML = `<img class="avatar" src="img/Main image ai.png" /> <p class="message-text md-root">Just a sec...</p>`;
    const botMsgDiv = createMessageElement(botMsgHTML, "bot-message", "loading");
    chatsContainer.appendChild(botMsgDiv);
    scrollToBottom();

    try {
      await generateResponse(botMsgDiv);
    } catch (error) {
      const loadingBotMsg = chatsContainer.querySelector(".bot-message.loading");
      if (loadingBotMsg) loadingBotMsg.classList.remove("loading");

      const errorMsgDiv = createMessageElement(
        `<p class="message-text error">Oops! Something went wrong while fetching the response. Please try again.</p>`,
        "bot-message"
      );
      chatsContainer.appendChild(errorMsgDiv);
      chatsContainer.scrollTo(0, chatsContainer.scrollHeight);
    }
  }, 60);
};

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (!file) return;
  const isImage = file.type.startsWith("image/");
  const reader = new FileReader();
  reader.readAsDataURL(file);
  reader.onload = (e) => {
    fileInput.value = "";
    const base64String = e.target.result.split(",")[1];
    fileUploadWrapper.querySelector(".file-preview").src = e.target.result;
    fileUploadWrapper.classList.add("active", isImage ? "img-attached" : "file-attached");

    userData.file = { fileName: file.name, data: base64String, mime_type: file.type, isImage };
  };
});

document.querySelector("#cancel-file-btn").addEventListener("click", () => {
  userData.file = {};
  fileUploadWrapper.classList.remove("file-attached", "img-attached", "active");
});

document.querySelector("#stop-response-btn").addEventListener("click", () => {
  if (controller) {
    controller.abort();
    controller = null;
  }
  stopTyping = true;
  clearInterval(typingInterval);

  const loadingBotMsg = chatsContainer.querySelector(".bot-message.loading");
  if (loadingBotMsg) {
    loadingBotMsg.classList.remove("loading");
    const textElement = loadingBotMsg.querySelector(".message-text");
    textElement.textContent = "❌ Response stopped by user.";
    textElement.style.color = "#d62939";
  }

  document.body.classList.remove("bot-responding");
});

themeToggleBtn.addEventListener("click", () => {
  const isLightTheme = document.body.classList.toggle("light-theme");
  localStorage.setItem("themeColor", isLightTheme ? "light_mode" : "dark_mode");
  themeToggleBtn.textContent = isLightTheme ? "dark_mode" : "light_mode";

  // Trigger fade-in animation
  document.body.classList.remove("fade-in-bottom");
  void document.body.offsetWidth;
  document.body.classList.add("fade-in-bottom");
});

document.querySelector("#delete-chats-btn").addEventListener("click", () => {
  chatHistory.length = 0;
  chatsContainer.innerHTML = "";
  document.body.classList.remove("chats-active", "bot-responding");
  navbar.classList.remove("shrink");
  hasShrunk = false;
});

document.querySelectorAll(".suggestions-item").forEach((suggestion) => {
  suggestion.addEventListener("click", () => {
    promptInput.value = suggestion.querySelector(".text").textContent;
    promptForm.dispatchEvent(new Event("submit"));
  });
});

document.addEventListener("click", ({ target }) => {
  const wrapper = document.querySelector(".prompt-wrapper");
  const shouldHide = target.classList.contains("prompt-input") || (wrapper.classList.contains("hide-controls") && (target.id === "add-file-btn" || target.id === "stop-response-btn"));
  wrapper.classList.toggle("hide-controls", shouldHide);
});

const wrapper = document.getElementById("main-wrapper");
const themeToggle = document.getElementById("theme-toggle-btn");

window.addEventListener("DOMContentLoaded", () => {
  wrapper.classList.add("animate-slide");
  setTimeout(() => wrapper.classList.remove("animate-slide"), 600);
});

themeToggle.addEventListener("click", () => {
  wrapper.classList.add("animate-slide");
  setTimeout(() => wrapper.classList.remove("animate-slide"), 600);
});

window.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("fade-in-bottom");
});

promptForm.addEventListener("submit", handleFormSubmit);
promptForm.querySelector("#add-file-btn").addEventListener("click", () => fileInput.click());
