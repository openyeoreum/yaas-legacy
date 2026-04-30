FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_BASE=http://127.0.0.1:18000
ENV VITE_API_BASE=$VITE_API_BASE

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 5175

CMD ["nginx", "-g", "daemon off;"]
