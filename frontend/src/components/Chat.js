import styles from "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";
import { useState } from "react";
import axios from "axios";

const Chat = () => {
  const [messages, setMessages] = useState([]);

  const convertToApiMessages = () => {
    return messages.map((msg) => ({
      role: msg.sender === "user" ? "user" : "assistant",
      content: msg.content,
    }));
  };

  return (
    <div style={{ position: "relative", height: "100vh" }}>
      <MainContainer>
        <ChatContainer>
          <MessageList>
            {messages.map((message, index) => (
              <Message
                key={index}
                style={{ padding: "1rem 0" }}
                model={{
                  direction: message.direction,
                  message: message.content,
                  sentTime: message.sentTime.toLocaleTimeString(),
                  sender: message.sender,
                  position: "single",
                }}
              />
            ))}
          </MessageList>
          <MessageInput
            placeholder="Type message here"
            onSend={async (innerHtml, textContent, innerText) => {
              const userMessage = {
                direction: "outgoing",
                content: innerText,
                sentTime: new Date(),
                sender: "user",
              };

              const updatedMessages = [...messages, userMessage];
              setMessages(updatedMessages);

              try {
                const response = await axios.post("http://localhost:8000/chat", {
                  messages: [
                    ...convertToApiMessages(),
                    { role: "user", content: innerText },
                  ],
                  debug: false,
                  deep_thinking_mode: false,
                  search_before_planning: false,
                });

                const assistantMessage = {
                  direction: "incoming",
                  content: response.data.response,
                  sentTime: new Date(),
                  sender: "ai",
                };

                setMessages((prev) => [...prev, assistantMessage]);
              } catch (error) {
                console.error("Error during chat request:", error);
                // 에러 처리 개선
                const errorMessage = {
                  direction: "incoming",
                  content: error.response?.data?.detail || "서버와 통신 중 오류가 발생했습니다.",
                  sentTime: new Date(),
                  sender: "ai",
                };
                
                setMessages((prev) => [...prev, errorMessage]);
              }
            }}
          />
        </ChatContainer>
      </MainContainer>
    </div>
  );
};

export default Chat;