# TrackFlow UIs — Dockerfile
# Sirve website (puerto 3000) y backoffice (puerto 3001) con Node.js

FROM node:20-alpine

WORKDIR /app

# Instalar dependencias de website y backoffice por separado
COPY website/package.json website/
RUN cd website && npm install

COPY backoffice/package.json backoffice/
RUN cd backoffice && npm install

# Copiar código fuente de ambas interfaces
COPY website/ website/
COPY backoffice/ backoffice/

# Script de arranque para ambos servicios
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 3000 3001

CMD ["/start.sh"]