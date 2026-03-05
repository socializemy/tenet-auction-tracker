# Step 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# We use a relative API base so Nginx can proxy requests properly
ENV VITE_API_URL=""
RUN npm run build

# Step 2: Serve the application using Nginx
FROM nginx:alpine
# Copy built static assets
COPY --from=build /app/dist /usr/share/nginx/html
# Copy custom Nginx configuration to handle React routing and /api proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
