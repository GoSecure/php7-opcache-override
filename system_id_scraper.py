#!/usr/bin/env python

# Copyright (c) 2016 GoSecure Inc.

import sys
import re
import requests
from md5 import md5

if len(sys.argv) != 2:
    print sys.argv[0] + " [file|URL]"
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
    print "No PHP version found, is this a phpinfo file?"
    exit(0)

php_version = php_version.group(1)

# Zend Extension Build ID
zend_extension_id = re.search('<tr><td class="e">Zend Extension Build </td><td class="v">(.*) </td></tr>', text)
if zend_extension_id == None:
    print "No Zend Extension Build found."
    exit(0)
zend_extension_id = zend_extension_id.group(1)

# Architecture
architecture = re.search('<tr><td class="e">System </td><td class="v">(.*) </td></tr>', text)
if architecture == None:
    print "No System info found."
    exit(0)
architecture = architecture.group(1).split()[-1]

# Zend Bin ID suffix
if architecture == "x86_64":
    bin_id_suffix = "48888"
else:
    bin_id_suffix = "44444"

zend_bin_id = "BIN_SIZEOF_CHAR" + bin_id_suffix

# Logging
print "PHP version : " + php_version
print "Zend Extension ID : " + zend_extension_id
print "Zend Bin ID : " + zend_bin_id
print "Assuming " + architecture + " architecture"

digest = md5(php_version + zend_extension_id + zend_bin_id).hexdigest()
print "------------"
print "System ID : " + digest

