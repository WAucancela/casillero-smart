# ══════════════════════════════════════════════════════════════
#  Frontend Angular — build de producción servido por nginx
#  Etapa 1: compila la app con Node
#  Etapa 2: imagen final nginx con el dist (la config de nginx
#           se monta desde ./nginx/conf.d en docker-compose)
# ══════════════════════════════════════════════════════════════

FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build -- --configuration production

FROM nginx:1.25-alpine
COPY --from=build /app/dist/frontend-angular/browser /usr/share/nginx/html
