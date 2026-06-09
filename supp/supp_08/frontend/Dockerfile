# [6교시] 프론트 개발 컨테이너 — npm start (개발 서버)
FROM node:18

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000
CMD ["npm", "start"]
