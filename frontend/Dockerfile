# Use an official Node.js runtime as a parent image
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package.json (and package-lock.json if available)
COPY package.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Bind the React development server to 0.0.0.0 so it is accessible externally
ENV HOST=0.0.0.0

# Expose port 3000 for the React app
EXPOSE 3000

# Start the React development server
CMD ["npm", "start"]