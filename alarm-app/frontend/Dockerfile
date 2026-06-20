FROM node:20-alpine AS build

WORKDIR /app

COPY alarm-app/frontend/package.json alarm-app/frontend/package-lock.json* ./
RUN npm ci --ignore-scripts 2>/dev/null || npm install

COPY alarm-app/frontend/ .
RUN npm run build

FROM nginx:1.27-alpine

COPY alarm-app/frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -qO- http://localhost/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
