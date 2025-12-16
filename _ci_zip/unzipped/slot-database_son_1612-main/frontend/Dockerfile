# Node 18 Alpine
FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package.json .
# Note: In a real repo we would copy yarn.lock too
RUN yarn install

# Copy Code
COPY . .

# Expose Port
EXPOSE 3000

# Start (Development Mode)
CMD ["yarn", "start"]
