// [2교시] 비스트리밍 — axios 로 day13 /chat 호출.
// 답이 다 완성된 뒤 {"reply": "..."} 가 한 번에 온다.
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";
import { useState } from "react";
import axios from "axios";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function Chat() {
  const [messages, setMessages] = useState([]);

  const handleSend = async (innerHtml, textContent) => {
    const text = textContent.trim();
    if (!text) return;

    // (A) 내 메시지 즉시 표시 (불변 갱신)
    setMessages((p) => [
      ...p,
      { direction: "outgoing", content: text, sender: "user" },
    ]);

    try {
      // (B) 백엔드 호출 (비스트리밍)
      const res = await axios.post(`${API}/chat`, { message: text });
      // (C) AI 응답 표시
      setMessages((p) => [
        ...p,
        { direction: "incoming", content: res.data.reply, sender: "ai" },
      ]);
    } catch (e) {
      setMessages((p) => [
        ...p,
        { direction: "incoming", content: "에러: " + e.message, sender: "ai" },
      ]);
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
                  message: m.content,
                  sender: m.sender,
                  position: "single",
                }}
              />
            ))}
          </MessageList>
          <MessageInput
            placeholder="메시지를 입력하세요"
            onSend={handleSend}
            attachButton={false}
          />
        </ChatContainer>
      </MainContainer>
    </div>
  );
}
