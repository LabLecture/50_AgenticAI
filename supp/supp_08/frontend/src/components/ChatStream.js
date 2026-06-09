// [4교시] 스트리밍 — fetch + response.body.getReader() 로 토큰을 받아 타이핑 효과.
// 백엔드 /chat/stream 은 text/plain 으로 토큰을 흘리고 끝에 \n[DONE] 마커를 붙인다(day14).
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";
import { useState } from "react";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function ChatStream() {
  const [messages, setMessages] = useState([]);

  const handleSend = async (innerHtml, textContent) => {
    // (A) 입력값 정리 — 앞뒤 공백을 제거하고, 빈 문자열이면 아무것도 보내지 않는다.
    const text = textContent.trim();
    if (!text) return;

    // (B) 내 메시지 + "빈 AI 메시지 칸" 2개를 한 번에 추가한다.
    //     스트리밍은 토큰이 조금씩 도착하므로, 먼저 빈 칸을 만들어 두고
    //     이후 토큰이 올 때마다 "배열의 마지막 칸(=이 AI 칸)"만 갱신한다.
    setMessages((p) => [
      ...p,
      { direction: "outgoing", content: text, sender: "user" },
      { direction: "incoming", content: "", sender: "ai" }, // ← 토큰을 채워 넣을 자리
    ]);

    try {
      // (C) 백엔드 /chat/stream 호출. axios 가 아니라 fetch 를 쓰는 이유는
      //     응답 "본문 스트림"(response.body)을 직접 읽기 위해서다.
      //     (axios 는 본문이 다 모일 때까지 기다렸다가 한 번에 돌려줘서 타이핑 효과를 낼 수 없다.)
      const res = await fetch(`${API}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }), // day13/14 와 동일한 {"message": ...} 형태
      });

      // (D) 스트림 리더 준비. read() 로 받는 value 는 바이트(Uint8Array) 라서
      //     TextDecoder 로 사람이 읽는 글자로 바꿔 준다. acc 는 지금까지 받은 토큰 버퍼.
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let acc = "";

      // (E) 서버가 스트림을 닫을 때(done)까지 반복해서 청크를 읽는다.
      while (true) {
        const { value, done } = await reader.read();
        if (done) break; // 더 올 토큰이 없으면 종료

        // (F) 도착한 청크를 디코드해 누적. { stream: true } 옵션은 멀티바이트 글자(한글)가
        //     청크 경계에서 잘려도 다음 청크와 이어서 안전하게 해석하도록 해 준다.
        acc += decoder.decode(value, { stream: true });

        // (G) 백엔드(day14)가 끝에 붙이는 종료 마커 "\n[DONE]" 은 화면에 보이지 않게 잘라낸다.
        const shown = acc.replace(/\n?\[DONE\]\s*$/, "");

        // (H) 마지막 AI 칸만 새 내용으로 교체한다.
        //     React 불변성 규칙 — 배열을 복사([...p])한 뒤 끝 요소만 교체해야 다시 그려진다.
        //     → 글자가 한 글자씩 늘어나 보이는 "타이핑 효과" 가 된다.
        setMessages((p) => {
          const c = [...p];
          c[c.length - 1] = { ...c[c.length - 1], content: shown };
          return c;
        });
      }
    } catch (e) {
      // (I) 네트워크/서버 오류 시, 미리 만들어 둔 마지막 AI 칸에 에러 메시지를 표시한다.
      setMessages((p) => {
        const c = [...p];
        c[c.length - 1] = { ...c[c.length - 1], content: "에러: " + e.message };
        return c;
      });
    }
  };

  return (
    <div style={{ position: "relative", height: "100%" }}>
      <MainContainer>
        <ChatContainer>
          <MessageList>
            {messages.map((m, i) => (
              <Message
                key={i}
                model={{
                  direction: m.direction,
                  message: m.content || "…",
                  sender: m.sender,
                  position: "single",
                }}
              />
            ))}
          </MessageList>
          <MessageInput
            placeholder="메시지를 입력하세요 (스트리밍)"
            onSend={handleSend}
            attachButton={false}
          />
        </ChatContainer>
      </MainContainer>
    </div>
  );
}
