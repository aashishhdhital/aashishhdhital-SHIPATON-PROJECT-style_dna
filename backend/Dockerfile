# Use a lightweight Python image.
FROM python:3.13-slim

# Put all backend code inside /app.
WORKDIR /app

# Copy dependency list first so Docker can cache installs.
COPY requirements.txt .

# Install Python packages.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend source code.
COPY . .

# FastAPI/Uvicorn listens on 8000.
EXPOSE 8000

# Start the FastAPI application.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]