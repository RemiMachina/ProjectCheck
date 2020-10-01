#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from common.pylint import Linter
from common.git import Git

# Executors
linter = Linter()

git = Git(
    before = os.environ.get("SHA_BEFORE"), 
    after = os.environ.get("SHA_AFTER"), 
    repo = os.environ.get("REPO_NAME"), 
    org = os.environ.get("ORG_NAME"), 
    token = os.environ.get("REPO_TOKEN")
)

report = linter.lint(git = git)

linter.terminal(report = report)

git.sync_issues(report = report)