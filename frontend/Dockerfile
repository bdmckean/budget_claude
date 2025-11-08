# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/src ./src
COPY frontend/public ./public

# Build arguments and environment variables
ARG REACT_APP_API_URL=http://localhost:5001/api
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

# Build the app
RUN npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Install serve to run the app
RUN npm install -g serve

# Copy built app from build stage
COPY --from=build /app/build ./build

# Expose port
EXPOSE 3000

# Run the app
CMD ["serve", "-s", "build", "-l", "3000"]
