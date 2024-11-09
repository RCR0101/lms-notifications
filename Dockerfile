FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8000 8501

CMD uvicorn selenium_monitor:app --host 0.0.0.0 --port 8000 & \
    streamlit run frontend.py --server.port=8501 --server.enableCORS=false