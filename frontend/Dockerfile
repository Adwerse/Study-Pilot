FROM node:20-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 4173

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s CMD wget -qO- "http://127.0.0.1:${PORT:-4173}/health" >/dev/null || exit 1

CMD ["sh", "-c", "export PORT=${PORT:-4173}; envsubst '$PORT' < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf && nginx -g 'daemon off;'"]
