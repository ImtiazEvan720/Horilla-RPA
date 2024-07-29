FROM python:3.10-slim-bullseye

ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY . .

# Ensure the entrypoint script is executable
RUN chmod +x /app/entrypoint.sh

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

EXPOSE 80

# Run the Django development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:80"]
