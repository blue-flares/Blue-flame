# Use a lightweight Python base image
FROM python:3.12-slim

# Install uv (ultrafast dependency manager)
RUN pip install --no-cache-dir uv

# Set the working directory inside the container
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies using uv
RUN uv pip install -r requirements.txt --system

# Copy the rest of the application code
COPY . .

# Run the main.py file
CMD ["python", "main.py"]
