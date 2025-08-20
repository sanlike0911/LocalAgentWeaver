FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start with a simple command that keeps the container running
CMD ["sh", "-c", "while true; do npm run dev --hostname 0.0.0.0 || sleep 5; done"]