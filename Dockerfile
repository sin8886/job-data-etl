# Use the official Python 3.11 base image.
FROM python:3.11-slim

# Set the container working directory.
WORKDIR /app

# Copy the dependency manifest first.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project into the image.
COPY . .

# Keep the default image command lightweight; Compose provides the app command.
CMD ["python", "--version"]