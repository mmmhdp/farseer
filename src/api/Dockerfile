FROM python:3.11

WORKDIR /usr/src/api_app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn","src.main:farseer_app","--host", "0.0.0.0", "--port", "8000"]
