# Use an official Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy backend files
COPY backend/ ./backend/

# Copy frontend files
COPY frontend/ ./frontend/

# Install backend dependencies
RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt

# Install Node.js 20.x and npm for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    npm --version && node --version

# Install frontend dependencies, add the node adapter, and build
WORKDIR /app/frontend
RUN npm install && \
    npm install -D @sveltejs/adapter-node && \
    npm run build && ls -la

# Move back to /app
WORKDIR /app

# Expose backend and frontend ports
EXPOSE 8000 5173

# Start backend and frontend
# HOST=0.0.0.0 is crucial so SvelteKit listens externally, not just on localhost
CMD ["bash", "-c", "uvicorn backend.si_api:app --host 0.0.0.0 --port 8000 & HOST=0.0.0.0 PORT=5173 node frontend/build/index.js"]