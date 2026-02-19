FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app code
COPY . .

# Cloud Run uses the PORT env var
EXPOSE 8080

# Start Shiny
# CMD ["shiny", "run", "apps/dashboard/app.py", "--host", "0.0.0.0", "--port", "8080"]
CMD python -m shiny run apps/dashboard/app.py --host 0.0.0.0 --port $PORT