if docker inspect --format="{{.State.Running}}" csgo-discord-bot; then
    echo "Container is running"
    docker stop csgo-discord-bot
    docker rm csgo-discord-bot
else
    echo "Container is not running"
fi
docker build -t csgo-discord-bot .
docker run -d --name=csgo-discord-bot --restart unless-stopped csgo-discord-bot