FROM python:3.10-slim

WORKDIR /app

COPY frontend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ ./frontend/
COPY frontend/templates/ ./templates/
COPY main.py ./
COPY outline_hierarchy.py ./

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "frontend.frontend:app", "--host", "0.0.0.0", "--port", "8000"] 