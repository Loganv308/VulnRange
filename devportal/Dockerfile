FROM node:20-slim
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json .
RUN npm install --omit=dev
COPY server.js .
COPY docs ./docs
# Flag for the path traversal / command injection challenges lives outside the web root
ARG FLAG_DEV_FILE=FLAG{placeholder}
RUN echo "$FLAG_DEV_FILE" > /opt/flag.txt && chmod 644 /opt/flag.txt
USER node
EXPOSE 3000
CMD ["node", "server.js"]
