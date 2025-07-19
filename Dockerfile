FROM python:3.12-slim

# Set working directory
WORKDIR /app

# System deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# Add a non-root user
RUN adduser --disabled-password appuser

# Copy project files
COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY README.md ./

# Now install your package (and its requirements)
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir .

# Remove build tools for smaller final image
RUN apt-get purge -y build-essential gcc && apt-get autoremove -y

# Change ownership of the app directory to the non-root user
RUN chown -R appuser /app

# Switch to non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Healthcheck to ensure the app is running
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Use uvicorn to run the FastAPI app
CMD ["uvicorn", "twitter_interest.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]