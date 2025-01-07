document.addEventListener("DOMContentLoaded", function () {
    const chatForm = document.getElementById("chat-form");
    const chatBox = document.getElementById("chat-box");
    const queryInput = document.getElementById("query");

    let loadingIndicator = null;

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

        // SSE 방식으로 서버 요청
        fetchSSE(query);
    });

    /**
     * SSE로 서버 호출하는 메서드
     */
    async function fetchSSE(query) {
        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                hideLoadingIndicator();
                throw new Error("챗봇 응답에 실패했습니다.");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            // 아직 완성되지 않은 bot 메시지 노드
            let botMsgDiv = addMessage("bot", ""); // 처음엔 빈 문자열
            let botResponse = ""; // 스트리밍 전체 텍스트 누적

            let firstChunkArrived = false; // 첫 chunk 여부

            async function readStream() {
                let isDone = false;
                while (!isDone) {
                    const { done, value } = await reader.read();
                    if (done) {
                        isDone = true;
                        console.log("Stream done.");

                        // 스트리밍 종료 시점에 최종 파싱 (추천 질문 레이아웃 등)
                        hideLoadingIndicator(); //念

                        // botResponse 최종 파싱 → 추천 질문 렌더링
                        finalizeBotResponse(botMsgDiv, botResponse);

                        break;
                    }

                    // chunk
                    const chunkText = decoder.decode(value, { stream: true });
                    const lines = chunkText.split("\n");

                    for (let line of lines) {
                        let trimmedLine = line.trim();
                        if (!trimmedLine) continue;

                        try {
                            const parsed = JSON.parse(trimmedLine);
                            const status = parsed.status;
                            const data = parsed.data;

                            if (status === "processing") {
                                // 첫 번째 chunk라면 로딩인디케이터 제거
                                if (!firstChunkArrived) {
                                    firstChunkArrived = true;
                                    hideLoadingIndicator();
                                }
                                // 토큰 누적
                                botResponse += data;
                                // 실시간으로 메시지를 갱신
                                botMsgDiv.querySelector(".text").textContent = botResponse;
                                scrollToBottom();

                            } else if (status === "complete") {
                                console.log("SSE complete:", data);
                            } else if (status === "error") {
                                botMsgDiv.querySelector(".text").textContent = `Error: ${data}`;
                                hideLoadingIndicator();
                                isDone = true;
                                break;
                            }
                        } catch (err) {
                            console.error("JSON parse error:", err, line);
                        }
                    }
                }
            }

            await readStream();
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

        showLoadingIndicator();

        try {
            // SSE로 다시
            const response = await fetch("/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream"
                },
                body: JSON.stringify({ query })
            });

            if (!response.ok) {
                hideLoadingIndicator();
                throw new Error("챗봇 응답에 실패했습니다.");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            let botMsgDiv = addMessage("bot", "");
            let botResponse = "";
            let firstChunkArrived = false;

            async function readStream() {
                let isDone = false;
                while (!isDone) {
                    const { done, value } = await reader.read();
                    if (done) {
                        isDone = true;
                        console.log("Stream done.");

                        // 스트리밍 종료 시점에 최종 파싱 (추천 질문 레이아웃 등)
                        hideLoadingIndicator(); //念

                        // botResponse 최종 파싱 → 추천 질문 렌더링
                        finalizeBotResponse(botMsgDiv, botResponse);

                        break;
                    }

                    // chunk
                    const chunkText = decoder.decode(value, { stream: true });
                    const lines = chunkText.split("\n");

                    for (let line of lines) {
                        let trimmedLine = line.trim();
                        if (!trimmedLine) continue;

                        try {
                            const parsed = JSON.parse(trimmedLine);
                            const status = parsed.status;
                            const data = parsed.data;

                            if (status === "processing") {
                                // 첫 번째 chunk라면 로딩인디케이터 제거
                                if (!firstChunkArrived) {
                                    firstChunkArrived = true;
                                    hideLoadingIndicator();
                                }
                                // 토큰 누적
                                botResponse += data;
                                // 실시간으로 메시지를 갱신
                                botMsgDiv.querySelector(".text").textContent = botResponse;
                                scrollToBottom();

                            } else if (status === "complete") {
                                console.log("SSE complete:", data);
                            } else if (status === "error") {
                                botMsgDiv.querySelector(".text").textContent = `Error: ${data}`;
                                hideLoadingIndicator();
                                isDone = true;
                                break;
                            }
                        } catch (err) {
                            console.error("JSON parse error:", err, line);
                        }
                    }
                }
            }
            await readStream();
        } catch (err) {
            console.error("Error:", err);
            hideLoadingIndicator();
            addMessage("bot", "죄송합니다. 현재 응답을 생성할 수 없습니다.");
            scrollToBottom();
        }
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
                case '&': return '&amp;';
                case '<': return '&lt;';
                case '>': return '&gt;';
                case '"': return '&quot;';
                case "'": return '&#39;';
                default: return m;
            }
        });
    }
});