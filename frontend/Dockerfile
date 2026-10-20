# [참고] 기존: FROM node:14 + react-scripts(CRA) → CRA 지원 종료로 Vite 로 이전
FROM node:22

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

# Vite 개발 서버 (vite.config.js 에서 host: true, port: 3000)
CMD ["npm", "run", "dev"]
