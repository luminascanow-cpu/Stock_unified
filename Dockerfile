FROM python:3.11-slim

# Allow statements and log messages to immediately appear in the Knative logs
ENV PYTHONUNBUFFERED True

WORKDIR /app

# Copy requirements
COPY requirements.txt ./

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download FinBERT model weights into the image to avoid HF rate-limiting (429) & long startup times
RUN python -c "import logging; logging.basicConfig(level=logging.INFO); from transformers import AutoTokenizer, AutoModelForSequenceClassification; AutoTokenizer.from_pretrained('ProsusAI/finbert'); AutoModelForSequenceClassification.from_pretrained('ProsusAI/finbert')"

# Force transformers to use the cached models preventing 429 rate limits
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

# Copy the rest of the app code
COPY . ./

# Run the web service on container startup. Here we use the gunicorn
# webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase the number of workers
# to be equal to the cores available.
# Cloud Run injects the PORT environment variable.
CMD exec uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
