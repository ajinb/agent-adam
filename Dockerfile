FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    AGENT_ADAM_TOKEN_STORE=file \
    STREAMLIT_SERVER_HEADLESS=true STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
RUN useradd --uid 1000 --no-create-home adam && mkdir -p /app/data && chown adam /app/data
USER 1000

EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health').status==200 else 1)"
# Mount credentials.json read-only and keep token.json on a volume:
#   docker run -p 8501:8501 --env-file .env -v $PWD/credentials.json:/app/credentials.json:ro agent-adam
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
