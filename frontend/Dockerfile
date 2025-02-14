# frontend/Dockerfile
# Use an official Node.js runtime as a parent image
FROM node:16-alpine as builder

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy app files
COPY . .

# Build the app for production
RUN npm run build

# --- Production Stage ---
FROM nginx:alpine 

COPY --from=builder /app/build /usr/share/nginx/html 
COPY nginx.conf /etc/nginx/conf.d/default.conf 

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]