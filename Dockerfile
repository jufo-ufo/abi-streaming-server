FROM ubuntu:22.04

# Update and install util stuff
RUN apt update -y && apt upgrade -y
RUN apt install -y lsb-release
RUN apt install -y net-tools htop vim curl wget tar zip gettext-base tree

# Downloading, Compiling, Installing nginx
WORKDIR /
RUN apt install -y build-essential libpcre3 libpcre3-dev libssl-dev zlib1g zlib1g-dev
RUN wget http://nginx.org/download/nginx-1.20.2.tar.gz
RUN wget https://github.com/sergey-dryabzhinsky/nginx-rtmp-module/archive/dev.zip

RUN tar -zxvf nginx-1.20.2.tar.gz
RUN unzip dev.zip
WORKDIR /nginx-1.20.2

RUN ./configure --with-http_ssl_module --add-module=../nginx-rtmp-module-dev --conf-path=/etc/nginx/nginx.conf
RUN make
RUN make install

# Copying config and setting up files
#COPY nginx.conf /etc/nginx/
RUN mkdir /var/log/nginx
RUN mkdir /video
RUN /usr/local/nginx/sbin/nginx -t

# Finish up
WORKDIR /
STOPSIGNAL SIGQUIT
CMD ["/usr/local/nginx/sbin/nginx", "-g", "daemon off;"]