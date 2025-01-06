document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatBox = document.getElementById("chat-box");
    const queryInput = document.getElementById("query");

    // 로딩 표시(typing indicator)용 변수
    let loadingIndicator = null;

    // 1) 페이지 로드 후, 환영 메시지 출력
    addMessage("bot", "안녕하세요! SmartStore FaQ 봇입니다.\n무엇을 도와드릴까요?");

    // 사용자가 폼 제출 시(메시지 전송)
    chatForm.addEventListener("submit", async function (e) {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query || loadingIndicator) return;

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
                body: JSON.stringify({query: query})
            });

            if (!response.ok) {
                throw new Error("챗봇 응답에 실패했습니다.");
            }

            const data = await response.json();
            const botResponse = data.response;

            // 로딩 표시 제거
            hideLoadingIndicator();

            // 봇 메시지
            addMessage("bot", botResponse);
            scrollToBottom();
        } catch (error) {
            console.error("Error:", error);
            hideLoadingIndicator();
            addMessage("bot", "죄송합니다. 현재 응답을 생성할 수 없습니다.");
            scrollToBottom();
        }
    });

    /**
     * 메시지를 채팅창에 추가
     * sender: "user" or "bot"
     * text: 메시지 텍스트
     */
    function addMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);

        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("avatar");
        if (sender === "user") {
            avatarDiv.innerHTML = '<img src="/static/ebi.png" alt="User">';
        } else {
            avatarDiv.innerHTML = '<img src="/static/bot.png" alt="Bot">';
        }

        // 말풍선 영역
        const textDiv = document.createElement("div");
        textDiv.classList.add("text");

        if (sender === "bot") {
            // "추천 질문:" 기준으로 나누기
            const parts = text.split("추천 질문:");
            if (parts.length > 1) {
                const mainAnswer = parts[0].trim();
                const recPart = parts[1];

                let htmlContent = `<div>${mainAnswer}</div>`;
                htmlContent += `<div class="recommended-title">\n 추천 질문:</div>`;

                // 줄 단위 split 후, 공백 제거 & 빈 줄은 제외
                const lines = recPart
                    .split("\n")
                    .map(line => line.trim())
                    .filter(line => line.length > 0);

                // 실제 추천 질문 목록(a 태그) 생성
                lines.forEach(line => {
                    if (line.startsWith("-") && line.length > 1) {
                        const questionText = line.replace("-", "").trim();
                        // 멀티라인 텍스트 내 들여쓰기 X, 불필요한 줄바꿈 X
                        htmlContent += `<a class="recommended-question" href="#" data-question="${questionText}">${questionText}</a>`;
                    }
                });

                textDiv.innerHTML = htmlContent;
            } else {
                textDiv.textContent = text;
            }
        } else {
            // 유저 메시지는 그대로 텍스트로
            textDiv.textContent = text;
        }

        if (sender === "user") {
            messageDiv.appendChild(textDiv);
            messageDiv.appendChild(avatarDiv);
        } else {
            messageDiv.appendChild(avatarDiv);
            messageDiv.appendChild(textDiv);
        }

        // 로딩 표시가 존재하면 그 위에 삽입, 아니면 맨 뒤에 추가
        if (loadingIndicator && chatBox.contains(loadingIndicator)) {
            chatBox.insertBefore(messageDiv, loadingIndicator);
        } else {
            chatBox.appendChild(messageDiv);
        }

        scrollToBottom();

        // 추천 질문 클릭 이벤트 등록
        if (sender === "bot") {
            setTimeout(() => {
                const recQuestions = textDiv.querySelectorAll(".recommended-question");
                recQuestions.forEach(item => {
                    item.addEventListener("click", () => {
                        const q = item.dataset.question; // data-question 속성 사용
                        handleRecommendedQuestion(q);
                    });
                });
            }, 0);
        }
    }

    // 추천 질문 클릭 시 자동 전송
    function handleRecommendedQuestion(question) {
        submitQuery(question);
    }

    // 서버로 질문을 전송하는 공통 함수
    async function submitQuery(query) {
        if (loadingIndicator) {
            return
        }
        // 사용자 메시지
        addMessage("user", query);
        queryInput.value = "";
        scrollToBottom();

        // 로딩표시
        showLoadingIndicator();

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({query: query})
            });

            if (!response.ok) {
                throw new Error("챗봇 응답에 실패했습니다.");
            }

            const data = await response.json();
            const botResponse = data.response;

            // 로딩 제거
            hideLoadingIndicator();

            // 봇 메시지
            addMessage("bot", botResponse);
            scrollToBottom();
        } catch (error) {
            console.error("Error:", error);
            hideLoadingIndicator();
            addMessage("bot", "죄송합니다. 현재 응답을 생성할 수 없습니다.");
            scrollToBottom();
        }
    }

    // 로딩 표시 (typing indicator)
    function showLoadingIndicator() {
        if (loadingIndicator) return;
        loadingIndicator = document.createElement("div");
        loadingIndicator.classList.add("message", "bot", "loading-indicator");

        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("avatar");
        avatarDiv.innerHTML = '<img src="https://via.placeholder.com/40/eaeaea/333333?text=B" alt="Bot">';

        // 스피너
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