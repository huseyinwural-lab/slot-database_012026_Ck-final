# Node 20 (Alpine not recommended for some native deps, using slim)
FROM node:20-slim as build

WORKDIR /app

# Install dependencies
COPY package.json yarn.lock ./
# Remove frozen-lockfile constraint to auto-fix lockfile issues during build if needed
RUN yarn install --non-interactive

# Copy Code
COPY . .

# Expose Port
EXPOSE 3001

# Start (Vite Dev)
CMD ["yarn", "dev", "--host", "0.0.0.0", "--port", "3001"]
