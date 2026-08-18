FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY phase6_backend_api/requirements.txt /app/phase6_backend_api/requirements.txt
RUN pip install --no-cache-dir -r /app/phase6_backend_api/requirements.txt

# Copy necessary phases for backend engine and data
COPY phase1_data_ingestion /app/phase1_data_ingestion
COPY phase2_user_input /app/phase2_user_input
COPY phase3_integration_layer /app/phase3_integration_layer
COPY phase4_recommendation_engine /app/phase4_recommendation_engine
COPY phase6_backend_api /app/phase6_backend_api

# Expose port
ENV PORT=8000
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["sh", "-c", "uvicorn phase6_backend_api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
