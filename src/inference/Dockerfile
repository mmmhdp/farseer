FROM ultralytics/ultralytics:latest-python

WORKDIR /usr/src/inference_app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install libgl1 -y 

CMD ["python3","./src/main.py"]
