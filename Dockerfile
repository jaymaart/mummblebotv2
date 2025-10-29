FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user
RUN useradd -m botuser
RUN chown -R botuser:botuser /app

# Copy the rest of the application
COPY --chown=botuser:botuser . .

# Switch to non-root user
USER botuser

# Command to run the bot
CMD ["python", "main.py"] 