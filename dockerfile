# Dockerfile (for Flask UI)
FROM python:3.11-slim AS base
WORKDIR /app

# Copy only UI files (adjust if needed)
COPY UI/ /app/

FROM base AS build
RUN pip install --no-cache-dir flask redis psycopg2-binary python-dotenv

FROM base AS final
COPY --from=build /usr/local /usr/local
CMD ["python", "app.py"]
