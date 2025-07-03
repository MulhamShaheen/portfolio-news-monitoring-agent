# Use official Python image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry files if present
COPY poetry.lock pyproject.toml ./

# Install poetry and dependencies
RUN pip install --upgrade pip \
    && pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 8000

# Set environment variables (override in compose if needed)
ENV PYTHONUNBUFFERED=1

# Run the API
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

