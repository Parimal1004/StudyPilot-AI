FROM python:3.11-slim

# Hugging Face runs Docker Spaces as user id 1000
RUN useradd -m -u 1000 user
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data && chown -R user:user /app

USER user

# Frontend talks to the backend running inside the same container
ENV BACKEND_URL=http://localhost:8000

# Hugging Face expects the public app on port 7860
EXPOSE 7860

# Start the API in the background, then Streamlit in the foreground.
# XSRF/CORS are turned off so file uploads work inside the Hugging Face iframe.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 & sleep 6 && exec streamlit run frontend/app.py --server.port 7860 --server.address 0.0.0.0 --server.headless true --server.enableXsrfProtection false --server.enableCORS false"]