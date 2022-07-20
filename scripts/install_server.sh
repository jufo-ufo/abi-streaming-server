#!/bin/bash

# Install Shit
apt update && apt -y upgrade
apt install docker.io
apt install htop
apt install lm-sensors jq

# Creating portainer volume
docker volume create portainer_data
docker run -d -p 8000:8000 -p 9443:9443 --name portainer \
    --restart=always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v portainer_data:/data \
    portainer/portainer-ce:2.9.3

# Setting up nginx
docker build -t streaming_server:latest .
docker run --rm --network host \
    -v "$(pwd)"/frontend:/usr/share/nginx/html \
    -v "$(pwd)"/logs:/var/log/nginx/ \
    --detach streaming_server:latest
