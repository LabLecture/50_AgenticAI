# frontend (React + Vite)

CRA(react-scripts)는 지원이 종료되어 Vite 로 이전했습니다. 포트(3000)와 빌드 폴더(`build/`)는 기존과 같습니다.

```bash
npm install
npm start          # 개발 서버 http://localhost:3000 (npm run dev 와 동일)
npm run build      # build/ 에 배포용 파일 생성
npm run preview    # 빌드 결과 미리보기
```

CRA 와 다른 점
- JSX 가 들어간 파일은 확장자 `.jsx` (`src/index.jsx`, `src/App.jsx`, `src/components/Chat.jsx`)
- `index.html` 은 `public/` 이 아니라 frontend 루트에 있음 (`%PUBLIC_URL%` 없이 `/파일명`)
- 환경변수는 `REACT_APP_` 대신 `VITE_` 접두사, 코드에서는 `import.meta.env.VITE_xxx`
- 백엔드 주소는 `src/components/Chat.jsx` 의 `axios.post(...)` URL (이 브랜치는 localhost:8002)
