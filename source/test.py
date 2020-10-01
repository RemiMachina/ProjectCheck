#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

print(os.environ.get("RUN_SCRIPT"))
print(os.environ.get("SHA_BEFORE"))
print(os.environ.get("SHA_AFTER"))
print(os.environ.get("ORG_NAME"))
print(os.environ.get("REPO_NAME"))
print(os.environ.get("REPO_TOKEN"))