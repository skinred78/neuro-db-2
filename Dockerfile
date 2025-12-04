FROM python:3.11-slim
WORKDIR /app
COPY poc_api_first/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY poc_api_first/ ./poc_api_first/
COPY data/neuro_terms.json ./data/neuro_terms.json
ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 poc_api_first.webapp.app:app
