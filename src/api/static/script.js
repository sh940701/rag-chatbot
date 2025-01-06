document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.getElementById("chat-form");
    const chatBox = document.getElementById("chat-box");
    const queryInput = document.getElementById("query");

    // 로딩 표시(typing indicator)용 변수
    let loadingIndicator = null;

    chatForm.addEventListener("submit", async function(e) {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;

        // 사용자 메시지
        addMessage("user", query);
        queryInput.value = "";
        scrollToBottom();

        // 로딩 표시 시작
        showLoadingIndicator();

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ query: query })
            });

            if (!response.ok) {
                throw new Error("챗봇 응답에 실패했습니다.");
            }

            const data = await response.json();
            const botResponse = data.response;

            // 로딩 표시 제거
            hideLoadingIndicator();

            // 챗봇 메시지
            addMessage("bot", botResponse);
            scrollToBottom();
        } catch (error) {
            console.error("Error:", error);
            hideLoadingIndicator();
            addMessage("bot", "죄송합니다. 현재 응답을 생성할 수 없습니다.");
            scrollToBottom();
        }
    });

    function addMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);

        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("avatar");
        if (sender === "user") {
            avatarDiv.innerHTML = '<img src="https://via.placeholder.com/40/007bff/ffffff?text=U" alt="User">';
        } else {
            avatarDiv.innerHTML = '<img src="https://via.placeholder.com/40/eaeaea/333333?text=B" alt="Bot">';
        }

        // 텍스트
        const textDiv = document.createElement("div");
        textDiv.classList.add("text");
        textDiv.textContent = text;

        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(textDiv);
        chatBox.appendChild(messageDiv);
        scrollToBottom();

        // 로딩 표시가 존재한다면 그 위에 삽입
        if (loadingIndicator && chatBox.contains(loadingIndicator)) {
            chatBox.insertBefore(messageDiv, loadingIndicator);
        } else {
            chatBox.appendChild(messageDiv);
        }
    }

    function showLoadingIndicator() {
        if (loadingIndicator) return;
        loadingIndicator = document.createElement("div");
        // 로딩도 bot 메시지 형태로
        loadingIndicator.classList.add("message", "bot", "loading-indicator");

        // 아바타
        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("avatar");
        avatarDiv.innerHTML = '<img src="https://via.placeholder.com/40/eaeaea/333333?text=B" alt="Bot">';

        // 로딩 스피너 (3점만, 텍스트 없음)
        const textDiv = document.createElement("div");
        textDiv.classList.add("text");
        textDiv.innerHTML = `
            <div class="spinner">
                <div class="bounce1"></div>
                <div class="bounce2"></div>
                <div class="bounce3"></div>
            </div>
        `;

        loadingIndicator.appendChild(avatarDiv);
        loadingIndicator.appendChild(textDiv);
        chatBox.appendChild(loadingIndicator);
        scrollToBottom();
    }

    function hideLoadingIndicator() {
        if (loadingIndicator && chatBox.contains(loadingIndicator)) {
            chatBox.removeChild(loadingIndicator);
        }
        loadingIndicator = null;
    }

    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});