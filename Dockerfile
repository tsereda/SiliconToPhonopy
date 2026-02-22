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

# Install frontend dependencies and build
WORKDIR /app/frontend
RUN npm install && npm run build

# Move back to /app
WORKDIR /app

# Expose backend and frontend ports
EXPOSE 8000 5173

# Start backend and frontend
CMD ["bash", "-c", "uvicorn backend.si_api:app --host 0.0.0.0 --port 8000 & npx serve frontend/dist --listen 5173"]
