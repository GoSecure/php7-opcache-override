FROM php:%%PHP_VERSION%%-cli-alpine

# Override with custom opcache settings
RUN docker-php-ext-install opcache
COPY opcache.ini $PHP_INI_DIR/conf.d/

COPY test.php /usr/src/myapp/
WORKDIR /usr/src/myapp
CMD [ "php", "./test.php" ]
