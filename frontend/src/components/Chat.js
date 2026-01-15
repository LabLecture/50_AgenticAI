import styles from "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
  MainContainer,
  ChatContainer,
  MessageList,
  Message,
  MessageInput,
} from "@chatscope/chat-ui-kit-react";    // 챗 UI 구성을 위한 컴포넌트들
import { useState } from "react";         // React의 상태 관리를 위한 훅
import axios from "axios";                // 백엔드 API와의 통신을 위한 라이브러리

const Chat = () => {
  // 메시지 내역을 저장하는 상태(State) 변수
  const [messages, setMessages] = useState([]); // {direction, content, sentTime, sender} 객체들의 배열

  return (
    // 3. 전체 화면을 꽉 채우는 컨테이너 설정 (높이 100vh)
    <div style={{ position: "relative", height: "100vh" }}>
      <MainContainer>
        <ChatContainer>
          {/* 4. 대화 내용이 표시되는 리스트 영역 */}
          <MessageList>
            {/* messages 배열을 순회(map)하며 각각의 Message 컴포넌트를 생성 */}
            {messages.map((message) => (
              <Message
                style={{ padding: "1rem 0" }}
                model={{
                  direction: message.direction, // "incoming" 또는 "outgoing"
                  message: message.content,
                  sentTime: String(message.sentTime),
                  sender: message.sender,       // "user" 또는 "ai"
                  position: "single",
                }}
              />
            ))}
          </MessageList>
          {/* 5. 사용자가 메시지를 입력하는 창 */}
          <MessageInput
            placeholder="Type message here"
            onSend={async (innerHtml, textContent, innerText) => {
              // [A] 사용자가 보낸 메시지를 즉시 화면(상태)에 반영
              setMessages((prev) => [
                ...prev,      // 기존 메시지 유지
                {
                  direction: "outgoing",  // 사용자가 보낸 메시지(오른쪽 정렬)
                  content: innerText,
                  sentTime: new Date(),
                  sender: "user",
                },
              ]);

              // [B] 백엔드 서버(Localhost 8000번 포트)로 메시지 전송
              // 사용자의 질문을 'question'이라는 키에 담아 POST 요청을 전송
              const response = await axios.post("http://localhost:8000/chat", {
                question: textContent,
              });

              // [C] 서버로부터 받은 응답(AI 답변)을 화면(상태)에 추가
              setMessages((prev) => [
                ...prev,
                {
                  direction: "incoming",          // AI가 보낸 메시지(왼쪽 정렬)
                  content: response.data.answer,  // 서버에서 보내준 응답 데이터
                  sentTime: new Date().toLocaleTimeString(),
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
