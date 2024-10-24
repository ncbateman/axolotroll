FROM python:3.11-slim

WORKDIR /app

# Accept BUILD_PORT as a build argument
ARG BUILD_PORT

# Set BUILD_PORT as an environment variable so it's available at runtime
ENV BUILD_PORT=${BUILD_PORT}

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY ./docker/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the correct port
EXPOSE ${BUILD_PORT}

# Use the environment variable for the port at runtime
CMD ["sh", "-c", "uvicorn --host 0.0.0.0 --port $BUILD_PORT asgi:factory --factory"]
