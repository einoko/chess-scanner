FROM python:3.8
RUN apt-get update && apt-get install -y ffmpeg libsm6 libxext6 && rm -r /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt ./
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]