FROM node:22-alpine AS ui
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/data/samples ./data/samples
COPY --from=ui /web/dist ./frontend/dist

ENV RAG_SAMPLE_DIR=/app/data/samples
ENV RAG_INDEX_PATH=/var/lib/rag/index.json
ENV RAG_FRONTEND_DIST=/app/frontend/dist
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
