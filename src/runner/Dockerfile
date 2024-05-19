FROM python:3.11

WORKDIR /usr/src/runner_app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3","./src/main.py"]
