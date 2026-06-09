// [5교시] WebSocket 양방향 — 한 번 연결해 두고 여러 질문을 연속 처리.
// 백엔드 /ws/chat 은 받은 질문에 대해 토큰을 send_text 로 흘리고 끝에 "[DONE]" 을 보낸다.
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";
import { useEffect, useRef, useState } from "react";

const WS_URL =
  (process.env.REACT_APP_API_URL || "http://localhost:8000").replace(/^http/, "ws") +
  "/ws/chat"; // http→ws, https→wss

export default function ChatWs() {
  const [messages, setMessages] = useState([]);
  const [ready, setReady] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket(WS_URL);
    ws.onopen = () => setReady(true);
    ws.onmessage = (ev) => {
      if (ev.data === "[DONE]") return;
      // 마지막 AI 메시지 칸에 토큰 누적
      setMessages((p) => {
        const c = [...p];
        c[c.length - 1] = {
          ...c[c.length - 1],
          content: c[c.length - 1].content + ev.data,
        };
        return c;
      });
    };
    ws.onclose = () => setReady(false);
    wsRef.current = ws;
    return () => ws.close(); // 언마운트 시 연결 정리
  }, []); // [] → 마운트 시 한 번만 연결

  const handleSend = (innerHtml, textContent) => {
    // (A) 입력값 정리 + 전송 가능 여부 가드.
    //     빈 문자열이거나 / 소켓이 아직 없거나 / 연결이 OPEN 상태가 아니면 보내지 않는다.
    //     (OPEN 이 아닐 때 send() 하면 예외가 나므로 readyState 를 먼저 확인)
    const text = textContent.trim();
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    // (B) 내 메시지 + "빈 AI 칸" 을 먼저 추가한다.
    //     비스트리밍(Chat.js)과 달리 응답은 이 함수가 아니라 위쪽 ws.onmessage 에서
    //     토큰 단위로 도착해 이 빈 칸을 이어서 채운다.
    setMessages((p) => [
      ...p,
      { direction: "outgoing", content: text, sender: "user" },
      { direction: "incoming", content: "", sender: "ai" }, // ← onmessage 가 토큰을 누적할 자리
    ]);

    // (C) 질문을 소켓으로 흘려보낸다. HTTP(axios/fetch)처럼 매번 새 요청·연결을 여는 게 아니라,
    //     useEffect 에서 한 번 열어 둔 연결(wsRef.current)을 그대로 재사용한다.
    //     → 서버 응답 토큰은 ws.onmessage 콜백이 받아 마지막 AI 칸에 이어 붙인다.
    wsRef.current.send(text);
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
            placeholder={ready ? "메시지를 입력하세요 (WebSocket)" : "연결 중…"}
            onSend={handleSend}
            attachButton={false}
            disabled={!ready}
          />
        </ChatContainer>
      </MainContainer>
    </div>
  );
}
