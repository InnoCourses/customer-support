FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry==1.7.1

# Copy poetry configuration files
COPY app/pyproject.toml app/poetry.lock* /app/

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy application code
COPY app/ /app/

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
