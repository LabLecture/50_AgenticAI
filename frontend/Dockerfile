FROM node:14
  
WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .
COPY .env.* ./

ARG REACT_APP_URL
ENV REACT_APP_URL $REACT_APP_URL

EXPOSE 3000

CMD ["npm", "start"]
