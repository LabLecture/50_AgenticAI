import { useState } from "react";
import Chat from "./components/Chat";
import ChatStream from "./components/ChatStream";
import ChatWs from "./components/ChatWs";

// 세 가지 연동 방식을 탭으로 전환하며 비교한다.
//  - 2교시 Chat       : axios 비스트리밍
//  - 4교시 ChatStream : fetch + getReader 스트리밍(타이핑 효과)
//  - 5교시 ChatWs     : WebSocket 양방향
const TABS = {
  basic: { label: "2교시 · 비스트리밍(axios)", Comp: Chat },
  stream: { label: "4교시 · 스트리밍(fetch)", Comp: ChatStream },
  ws: { label: "5교시 · WebSocket", Comp: ChatWs },
};

export default function App() {
  const [tab, setTab] = useState("basic");
  const { Comp } = TABS[tab];

  return (
    <div style={{ height: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: 8, display: "flex", gap: 8, borderBottom: "1px solid #eee" }}>
        {Object.entries(TABS).map(([key, { label }]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            style={{ fontWeight: tab === key ? "bold" : "normal" }}
          >
            {label}
          </button>
        ))}
      </div>
      <div style={{ flex: 1, minHeight: 0 }}>
        {/* key={tab} → 탭 전환 시 컴포넌트를 새로 마운트(상태/소켓 초기화) */}
        <Comp key={tab} />
      </div>
    </div>
  );
}
