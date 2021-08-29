if docker inspect --format="{{.State.Running}}" csgo-bot; then
    echo "Container is running"
    docker stop csgo-bot
    docker rm csgo-bot
else
    echo "Container is not running"
fi
docker build -t csgo-bot .
docker run -d --name=csgo-bot --restart unless-stopped csgo-bot