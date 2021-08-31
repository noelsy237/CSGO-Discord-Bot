FROM python:slim
WORKDIR /usr/src/app
COPY . .

RUN apt-get update && apt-get install -y libopus0
RUN pip install -r requirements.txt

CMD ["bot.py"]
ENTRYPOINT ["python3"]