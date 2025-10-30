FROM docker.io/ubuntu:jammy-20230126

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt -y full-upgrade

# Web server
RUN apt install -y lighttpd openssl
RUN mkdir /etc/lighttpd/ssl/
RUN	openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -subj '/CN=localhost' -nodes -sha256 && \
	cat /tmp/key.pem /tmp/cert.pem > /etc/lighttpd/ssl/localhost.pem && \
	rm /tmp/key.pem /tmp/cert.pem && \
	chmod 400 /etc/lighttpd/ssl/localhost.pem
COPY docker-data/config/lighttpd/*.conf /etc/lighttpd/
RUN groupadd lighttpd
RUN useradd -g lighttpd lighttpd

# PHP
RUN apt install -y php8.1 php8.1-curl php8.1-xml php8.1-mysql php8.1-mbstring php8.1-zip php8.1-imagick php8.1-cgi php8.1-fpm php8.1-cli php-json php8.1-zip php8.1-gd php8.1-intl
COPY docker-data/config/php/fpm/pool.d/*.conf /etc/php/8.1/fpm/pool.d/

# WordPress
RUN mkdir -p /usr/share/webapps/
COPY wordpress.tar.gz /opt/
RUN tar -xzvf /opt/wordpress.tar.gz -C /usr/share/webapps/
RUN rm /opt/wordpress.tar.gz
RUN chown -R www-data /usr/share/webapps/
RUN mkdir -p /var/www/localhost/htdocs
RUN ln -s /usr/share/webapps/wordpress/ /var/www/localhost/htdocs/wordpress

# phpinfo
RUN bash -c " echo '<?php phpinfo(); ?>' > /var/www/localhost/htdocs/phpinfo.php"

# Expose http(s) ports
EXPOSE 80 443

RUN chown -R www-data:www-data /var/log/lighttpd

CMD [ "/bin/bash", "-c", "php-fpm8.1 && lighttpd -D -f /etc/lighttpd/lighttpd.conf" ]