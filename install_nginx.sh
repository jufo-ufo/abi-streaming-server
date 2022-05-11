#!/bin/bash

apt update -y && apt upgrade -y
apt install -y lsb-release
apt install -y net-tools htop vim curl wget tar zip gettext-base tree

# Downloading, Compiling, Installing nginx
apt install -y build-essential libpcre3 libpcre3-dev libssl-dev zlib1g zlib1g-dev
wget http://nginx.org/download/nginx-1.20.2.tar.gz
wget https://github.com/sergey-dryabzhinsky/nginx-rtmp-module/archive/dev.zip

tar -zxvf nginx-1.20.2.tar.gz
unzip dev.zip
cd /nginx-1.20.2

./configure --with-http_ssl_module --add-module=../nginx-rtmp-module-dev --conf-path=/etc/nginx/nginx.conf
make
make install

# Copying config and setting up files
cp etc/nginx/* /etc/nginx/
mkdir /var/log/nginx

/usr/local/nginx/sbin/nginx -t

# Finish up
echo "To start run: /usr/local/nginx/sbin/nginx start"
echo "To stop run: /usr/local/nginx/sbin/nginx stop"
echo "To stop run: /usr/local/nginx/sbin/nginx restart"