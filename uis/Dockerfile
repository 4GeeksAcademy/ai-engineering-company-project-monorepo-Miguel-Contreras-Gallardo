# TrackFlow UIs — Dockerfile
# Sirve website (puerto 3000) y backoffice (puerto 3001) con Node.js

FROM node:20-alpine

WORKDIR /app

# Instalar serve globalmente (no depende de bind mounts)
RUN npm install -g serve@^14.2.0

# Copiar package.json por separado para cache de capas Docker
COPY website/package.json website/
COPY backoffice/package.json backoffice/

# Instalar dependencias de cada UI en su propio directorio
RUN cd website && npm install
RUN cd backoffice && npm install

# Copiar código fuente (será sobrescrito por bind mount en desarrollo)
COPY website/ website/
COPY backoffice/ backoffice/

# Script de arranque
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 3000 3001

CMD ["/start.sh"]