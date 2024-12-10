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

  return (
    <div style={{ position: "relative", height: "100vh" }}>
      <MainContainer>
        <ChatContainer>
          <MessageList>
            {messages.map((message) => (
              <Message
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
            onSend={async (innerHtml, textContent, innerText) => {
              setMessages((prev) => [
                ...prev,
                {
                  direction: "outgoing",
                  content: innerText,
                  sentTime: new Date(),
                  sender: "user",
                },
              ]);

              const response = await axios.post("http://61.108.166.16:8000/chat", {
                question: textContent,
              });

              setMessages((prev) => [
                ...prev,
                {
                  direction: "incoming",
                  content: response.data.answer,
                  sentTime: new Date(),
                  sender: "ai",
                },
              ]);
            }}
          />
        </ChatContainer>
      </MainContainer>
    </div>
  );
};

export default Chat;
