document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatBox = document.getElementById("chat-box");
    const queryInput = document.getElementById("query");

    let loadingIndicator = null;
    let eventSource = null; // EventSource 객체 추가

    // 1) 환영 메시지
    addMessage("bot", "안녕하세요! SmartStore FaQ 봇입니다.\n무엇을 도와드릴까요?");

    // 폼 제출 시
    chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query || loadingIndicator) return;

        addMessage("user", query);
        queryInput.value = "";
        scrollToBottom();

        // 로딩 표시
        showLoadingIndicator();

        // 서버로 쿼리 전송
        sendQuery(query);
    });

    /**
     * 서버로 쿼리를 전송하는 함수
     */
    async function sendQuery(query) {
        try {
            // EventSource를 사용하여 스트림을 수신
            const url = `/chat?query=${encodeURIComponent(query)}`;
            eventSource = new EventSource(url);

            // 아직 완성되지 않은 bot 메시지 노드
            let botMsgDiv = null
            let botResponse = "";

            eventSource.onmessage = function (event) {
                try {
                    const parsed = JSON.parse(event.data);
                    const status = parsed.status;
                    const data = parsed.data;

                    if (status === "processing") {
                        // 첫 chunk가 도착했을 때만 봇 메시지 노드를 생성
                        if (!botMsgDiv) {
                            hideLoadingIndicator();
                            botMsgDiv = addMessage("bot", "");
                        }

                        // 실시간으로 메시지를 갱신
                        botMsgDiv.querySelector(".text").textContent += data;
                        botResponse += data
                        hideLoadingIndicator();
                        scrollToBottom();
                    } else if (status === "complete") {
                        // 스트림 종료
                        finalizeBotResponse(botMsgDiv, botResponse);
                        hideLoadingIndicator();
                        eventSource.close();
                    } else if (status === "error") {
                        botMsgDiv.querySelector(".text").textContent = `Error: ${data}`;
                        hideLoadingIndicator();
                        eventSource.close();
                        console.error("서버에서 오류가 발생했습니다:", data);
                    }
                } catch (err) {
                    console.error("JSON parse error:", err, event.data);
                }
            };

            eventSource.onerror = function (err) {
                console.error("EventSource failed:", err);
                hideLoadingIndicator();
                addMessage("bot", "죄송합니다. 현재 응답을 생성할 수 없습니다.");
                eventSource.close();
            };

        } catch (error) {
            console.error("Error:", error);
            hideLoadingIndicator();
            addMessage("bot", "죄송합니다. 현재 응답을 생성할 수 없습니다.");
            scrollToBottom();
        }
    }

    /**
     * 스트리밍 완료 후 최종 botResponse를 분석하여
     * "추천 질문:" 구간을 파싱, 별도 링크로 렌더링
     */
    function finalizeBotResponse(botMsgDiv, fullText) {
        // 기존 파싱 로직과 유사하게, "추천 질문:" 기준으로 split
        const textDiv = botMsgDiv.querySelector(".text");
        // 안전 장치
        if (!fullText || !textDiv) return;

        const parts = fullText.split("추천 질문:");
        if (parts.length > 1) {
            const mainAnswer = parts[0].trim();
            const recPart = parts[1] || "";
            let htmlContent = `<div>${escapeHTML(mainAnswer)}</div>`;

            htmlContent += `<div class="recommended-title">\n 추천 질문:</div>`;
            // 줄 단위 split 후, 공백 제거 & 빈 줄 제외
            const lines = recPart
                .split("\n")
                .map(line => line.trim())
                .filter(line => line.length > 0);

            lines.forEach(line => {
                if (line.startsWith("-") && line.length > 1) {
                    const questionText = line.replace("-", "").trim();
                    htmlContent += `<a class="recommended-question" href="#" data-question="${escapeHTML(questionText)}">${escapeHTML(questionText)}</a>`;
                }
            });

            textDiv.innerHTML = htmlContent;
            // 추천 질문 클릭 이벤트 다시 등록
            setTimeout(() => {
                const recQuestions = textDiv.querySelectorAll(".recommended-question");
                recQuestions.forEach(item => {
                    item.addEventListener("click", () => {
                        const q = item.dataset.question;
                        submitQuery(q);
                    });
                });
            }, 0);
        } else {
            // 추천 질문 구간이 없다면 그대로 텍스트만
            textDiv.textContent = fullText;
        }
    }

    // 이미 있는 로직 재사용 → 추천 질문 클릭 시 다시 submitQuery
    async function submitQuery(query) {
        if (loadingIndicator) {
            return;
        }
        addMessage("user", query);
        queryInput.value = "";
        scrollToBottom();

        // 로딩 표시
        showLoadingIndicator();

        // 서버로 쿼리 전송
        await sendQuery(query);
    }

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

        const textDiv = document.createElement("div");
        textDiv.classList.add("text");
        textDiv.textContent = text;

        if (sender === "user") {
            messageDiv.appendChild(textDiv);
            messageDiv.appendChild(avatarDiv);
        } else {
            messageDiv.appendChild(avatarDiv);
            messageDiv.appendChild(textDiv);
        }

        if (loadingIndicator && chatBox.contains(loadingIndicator)) {
            chatBox.insertBefore(messageDiv, loadingIndicator);
        } else {
            chatBox.appendChild(messageDiv);
        }
        scrollToBottom();
        return messageDiv;
    }

    function showLoadingIndicator() {
        if (loadingIndicator) return;
        loadingIndicator = document.createElement("div");
        loadingIndicator.classList.add("message", "bot", "loading-indicator");

        const avatarDiv = document.createElement("div");
        avatarDiv.classList.add("avatar");
        avatarDiv.innerHTML = '<img src="/static/bot.png" alt="Bot">';

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

    // XSS 대비용 단순 Escape 함수
    function escapeHTML(str) {
        return str.replace(/[&<>"']/g, function (m) {
            switch (m) {
                case '&':
                    return '&amp;';
                case '<':
                    return '&lt;';
                case '>':
                    return '&gt;';
                case '"':
                    return '&quot;';
                case "'":
                    return '&#39;';
                default:
                    return m;
            }
        });
    }
});