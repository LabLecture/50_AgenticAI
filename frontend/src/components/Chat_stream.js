import styles from "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";
import { useState } from "react";

const Chat = () => {
  const [messages, setMessages] = useState([]);

  const sendMessage = async (textContent) => {
    const userMessage = {
      role: "user",
      content: textContent,
    };

    // 사용자 메시지 추가
    setMessages((prev) => [
      ...prev,
      {
        direction: "outgoing",
        content: textContent,
        sentTime: new Date(),
        sender: "user",
      },
    ]);

    const controller = new AbortController();
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        messages: [userMessage],
        debug: false,
        deep_thinking_mode: true,
        search_before_planning: false,
      }),
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";
    let aiContent = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop(); // 남은 데이터 보존

      for (const line of lines) {
        if (line.startsWith("data:")) {
          const payload = JSON.parse(line.replace(/^data:\s*/, ""));
          const delta = payload?.delta?.content || "";

          aiContent += delta;

          // 메시지를 실시간으로 추가하거나 마지막 메시지에 덧붙이기
          setMessages((prevMessages) => {
            const last = prevMessages[prevMessages.length - 1];
            if (last?.sender === "ai") {
              // 기존 ai 메시지 덧붙이기
              return [
                ...prevMessages.slice(0, -1),
                {
                  ...last,
                  content: last.content + delta,
                },
              ];
            } else {
              // 새로운 ai 메시지 시작
              return [
                ...prevMessages,
                {
                  direction: "incoming",
                  content: delta,
                  sentTime: new Date(),
                  sender: "ai",
                },
              ];
            }
          });
        }
      }
    }
  };

  return (
    <div style={{ position: "relative", height: "100vh" }}>
      <MainContainer>
        <ChatContainer>
          <MessageList>
            {messages.map((message, idx) => (
              <Message
                key={idx}
                style={{ padding: "1rem 0" }}
                model={{
                  direction: message.direction,
                  message: message.content,
                  sentTime: message.sentTime,
                  sender: message.sender,
                  position: "single",
                }}
              />
            ))}
          </MessageList>
          <MessageInput
            placeholder="Type message here"
            onSend={(innerHtml, textContent, innerText) =>
              sendMessage(textContent)
            }
          />
        </ChatContainer>
      </MainContainer>
    </div>
  );
};

export default Chat;
