# ── Stage 1: Build the Vue app ──
FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Build arg so the API URL is baked into the bundle
ARG VITE_API_URL=/api
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ── Stage 2: Serve with Nginx ──
FROM nginx:alpine

# Remove default nginx page
RUN rm -rf /usr/share/nginx/html/*

# Copy the built Vue app
COPY --from=build /app/dist /usr/share/nginx/html

# Nginx config will be mounted via docker-compose volume
EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
