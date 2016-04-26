#!/usr/bin/env sh

echo "Setting opcache location in php.ini"
sed -e "s@;opcache.file_cache=\$@opcache.file_cache=$PWD\/opcache@g" php.ini.sample > php.ini

echo "Setting permissions of opcache folder to 777..."
chmod 777 opcache

echo "Setting permissions of demo folder to 500..."
chmod 500 .
