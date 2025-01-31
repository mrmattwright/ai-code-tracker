FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install project dependencies using uv
RUN uv pip install --system .

# Set default command
ENTRYPOINT ["python", "-m", "ai_code_tracker.contribution_tracker"] 