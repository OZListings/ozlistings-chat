# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Upgrade pip and install a specific version of Poetry (we choose 1.5.1 here)
RUN pip install --upgrade pip && \
    pip install poetry==1.5.1

# Copy the dependency descriptor from the repo root
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to install dependencies into the system environment (avoiding a virtual environment)
RUN poetry config virtualenvs.create false && \
    poetry install --only main

# Copy the backend source code into the container
COPY backend/ .
COPY data/ .

# Expose port 8000 for the FastAPI app
EXPOSE 8000

# Run the FastAPI app with auto-reload enabled
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]