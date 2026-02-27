FROM node:20-slim AS frontend

WORKDIR /build
COPY package.json package-lock.json* ./
RUN npm ci
COPY index.html vite.config.* ./
COPY src/ src/
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend
COPY backend/ backend/
COPY fixtures/ fixtures/
COPY sdk/ sdk/

# Copy frontend build from previous stage
COPY --from=frontend /build/dist dist/

# Copy supporting files
COPY .env.example .env.example

ENV DATABASE_URL=sqlite:///data/truss.db
ENV HMAC_SECRET=change-me-in-production
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "mkdir -p /app/data && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}"]
