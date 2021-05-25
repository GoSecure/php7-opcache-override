#!/usr/bin/env python2

# Copyright (c) 2016, 2019 GoSecure Inc.

import sys
from packaging import version
import re
import requests

def md5(data):
    if type(data) is str:
        data = bytes(data, encoding='utf-8')
    return __import__('hashlib').md5(data).hexdigest()

if len(sys.argv) != 2:
    print(sys.argv[0] + " [file|URL]")
    exit(0)

if (sys.argv[1].startswith("http")):
    text = requests.get(sys.argv[1]).text
else:
    with open(sys.argv[1]) as file:
        text = file.read()
        file.close()

# PHP Version
php_version = re.search('<tr><td class="e">PHP Version </td><td class="v">(.*) </td></tr>', text)

if php_version == None:
    php_version = re.search('<h1 class="p">PHP Version (.*)', text)

if php_version == None:
    print("No PHP version found, is this a phpinfo file?")
    exit(0)

php_version = php_version.group(1)
php_greater_74 = (version.parse("7.4.0") < version.parse(php_version.split("-")[0]))
# Zend Extension Build ID
zend_extension_id = re.search('<tr><td class="e">Zend Extension Build </td><td class="v">(.*) </td></tr>', text)
if zend_extension_id == None:
    print("No Zend Extension Build found.")
    exit(0)
zend_extension_id = zend_extension_id.group(1)

# Architecture
architecture = re.search('<tr><td class="e">System </td><td class="v">(.*) </td></tr>', text)
if architecture == None:
    print("No System info found.")
    exit(0)
architecture = architecture.group(1).split()[-1]

# Zend Bin ID suffix
if architecture == "x86_64":
    bin_id_suffix = "48888"
else:
    bin_id_suffix = "44444"

# With PHP 7.4 they fixed the undefined macro that did the weird bin ID
if php_greater_74:
    zend_bin_id = "BIN_" + bin_id_suffix
else:
    zend_bin_id = "BIN_SIZEOF_CHAR" + bin_id_suffix

# Alternate Bin ID, see #5
if not php_greater_74:
    if architecture == "x86_64":
        alt_bin_id_suffix = "148888"
    else:
        alt_bin_id_suffix = "144444"

    alt_zend_bin_id = "BIN_" + alt_bin_id_suffix


# Logging
print("PHP version : " + php_version)
print("Zend Extension ID : " + zend_extension_id)
print("Zend Bin ID : " + zend_bin_id)
print("Assuming " + architecture + " architecture")

digest = md5(php_version + zend_extension_id + zend_bin_id)
print("------------")
print("System ID : " + digest)

if not php_greater_74:
    alt_digest = md5(php_version + zend_extension_id + alt_zend_bin_id)
    print("PHP lower than 7.4 detected, an alternate Bin ID is possible:")
    print("Alternate Zend Bin ID : " + alt_zend_bin_id)
    print("Alternate System ID : " + alt_digest)
