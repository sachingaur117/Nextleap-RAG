# Use a more robust Debian-based Python runtime
FROM python:3.9-bookworm

# Set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Note: In a production environment, you should run the Backend and Frontend in separate containers.
# We will use docker-compose to orchestrate this.
