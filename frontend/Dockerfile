# Development stage
FROM node:20-alpine AS development

WORKDIR /app

COPY package.json .
RUN npm install

EXPOSE 5173

CMD ["npx", "vite", "--host", "0.0.0.0"]
