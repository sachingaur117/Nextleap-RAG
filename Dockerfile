# Use a more robust Debian-based Python runtime
FROM python:3.11-bookworm

# Set working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Ensure the orchestrator script is executable
RUN chmod +x start.sh

# Start the application!
CMD ["./start.sh"]
