# Build the React application with Node.js. This is a separate stage so the final
# image contains the compiled website, not the larger Node.js toolchain.
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency manifests first so Docker can cache npm install between source
# changes. npm ci uses the committed lockfile for a reproducible installation.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# The final image uses an Nginx image designed to run without root privileges.
# Nginx serves the static files produced by Vite.
FROM nginxinc/nginx-unprivileged:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

# The unprivileged Nginx image listens on 8080 instead of privileged port 80.
EXPOSE 8080
