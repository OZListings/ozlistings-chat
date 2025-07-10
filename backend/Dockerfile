# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the backend source code into the container
COPY . .

# Expose port (will be overridden by Cloud Run)
EXPOSE 8080

# Run the FastAPI app using the PORT environment variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}