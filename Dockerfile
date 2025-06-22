FROM python:3.12-slim

# Set working directory
WORKDIR /app

# System deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy metadata and the source tree _together_
COPY pyproject.toml requirements.txt README.md ./
COPY src ./src

# Now install your package (and its requirements)
RUN pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir .

# Expose and run
EXPOSE 8000
CMD ["uvicorn", "twitter_interest.api:app", "--host", "0.0.0.0", "--port", "8000"]