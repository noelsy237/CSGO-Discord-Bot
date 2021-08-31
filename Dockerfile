FROM python:slim
WORKDIR /usr/src/app
COPY . .

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopus0 \
&& rm -rf /var/lib/apt/lists/*```

RUN pip install -r requirements.txt --no-cache-dir

CMD ["bot.py"]
ENTRYPOINT ["python3"]