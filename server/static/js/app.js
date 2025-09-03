// Эффект печати
function typeText(element, text, speed = 50, callback) {
    let i = 0;
    element.textContent = "";
    element.style.borderRight = "2px solid white";
    function type() {
        if (i < text.length) {
            element.textContent += text.charAt(i);
            i++;
            setTimeout(type, speed);
        } else {
            element.style.borderRight = "none";
            if (callback) callback();
        }
    }
    type();
}

// Переход экранов
function switchScreen(hideId, showId, callback) {
    const hide = document.getElementById(hideId);
    const show = document.getElementById(showId);

    hide.classList.add("fade-out");
    
    // Сначала убираем hidden у show
    show.classList.remove("hidden");
    show.classList.add("fade-in");

    setTimeout(() => {
        hide.classList.add("hidden");
        hide.classList.remove("fade-out");
        show.classList.remove("fade-in");
        if (callback) callback();
    }, 1000);
}

// Загрузка JSON
async function uploadHierarchy() {
    const fileInput = document.getElementById("file-input");
    const errorMsg = document.getElementById("error-message");

    if (!fileInput.files.length) {
        errorMsg.textContent = "Выберите JSON файл!";
        return;
    }

    let formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("/upload-hierarchy/", {
            method: "POST",
            body: formData
        });
        const result = await response.json();
        if (result.status === "ok") {
            switchScreen("upload-screen", "query-screen", () => {
                typeText(document.getElementById("typed-text"), "Напиши свой запрос");
            });
        } else {
            errorMsg.textContent = "Ошибка загрузки: неверный формат JSON или структура";
        }
    } catch (e) {
        errorMsg.textContent = "Ошибка загрузки: " + e;
    }
}

// Отправка запроса
async function sendQuery(event) {
    event.preventDefault();

    // Определяем активное поле ввода
    const activeInput = document.getElementById("chat-input") || document.getElementById("query-input");
    if (!activeInput) return;

    const chatBox = document.getElementById("chat-box");

    // Сообщение пользователя
    let userMsg = document.createElement("div");
    userMsg.className = "user-msg";
    userMsg.textContent = activeInput.value;
    if (chatBox) chatBox.appendChild(userMsg);

    let formData = new FormData();
    formData.append("query", activeInput.value);

    const response = await fetch("/process-query/", {
        method: "POST",
        body: formData
    });
    const result = await response.json();

    // Ответ бота
    let botMsg = document.createElement("div");
    botMsg.className = "bot-msg";
    if (result.status === "ok") {
        const phrases = [
            "Да, конечно, вот твой запрос: ",
            "Обработал твой запрос, проверяй: ",
            "А вот и я с ответом: "
        ];
        botMsg.textContent = phrases[Math.floor(Math.random() * phrases.length)] + result.response;
    } else {
        botMsg.textContent = "Ошибка: " + result.message;
    }

    if (chatBox) {
        chatBox.appendChild(botMsg);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Переход на экран чата при первом запросе
    if (document.getElementById("query-screen") && !document.getElementById("chat-screen").classList.contains("fade-in")) {
        switchScreen("query-screen", "chat-screen");
    }

    activeInput.value = "";
}