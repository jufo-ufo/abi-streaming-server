#!/bin/bash
if ! command -v docker ps &> /dev/null; then
    sudo apt update
    sudo apt install docker.io
fi

if docker build -t streaming_server:latest .; then
    echo ""
    echo "Runnning Container!"
    echo ""
    if $1 == "detached"; then
        docker run --rm --network host \
            -v "$(pwd)"/frontend:/usr/share/nginx/html \
            -v "$(pwd)"/logs:/var/log/nginx/ \
            --detach streaming_server:latest    
    else
        docker run --rm --network host \
            -v "$(pwd)"/frontend:/usr/share/nginx/html \
            -v "$(pwd)"/logs:/var/log/nginx/ \
            -it streaming_server:latest
    fi
fi