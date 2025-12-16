# Node 18 Alpine
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json .
RUN yarn install

# Copy Code
COPY . .

# Expose Port
EXPOSE 3001

# Start (Vite Dev)
CMD ["yarn", "dev", "--host", "0.0.0.0", "--port", "3001"]
