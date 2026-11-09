FROM php:8.2-apache
# Let Apache execute alternate PHP extensions (makes the upload blocklist bypassable)
RUN printf '<FilesMatch "\\.(phtml|php5|php7|phar)$">\n  SetHandler application/x-httpd-php\n</FilesMatch>\n' \
      > /etc/apache2/conf-enabled/extra-php.conf
COPY *.php /var/www/html/
RUN mkdir -p /var/www/html/uploads && chown www-data:www-data /var/www/html/uploads
# Flag for the upload -> RCE challenge: only readable by executing code on the box
ARG FLAG_FS_RCE=FLAG{placeholder}
ARG FLAG_FS_LFI=FLAG{placeholder}
RUN sed -i "s/__FLAG_FS_LFI__/$FLAG_FS_LFI/" /var/www/html/config.php
RUN echo "$FLAG_FS_RCE" > /flag_rce.txt && chmod 444 /flag_rce.txt
EXPOSE 80
