#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from common.pylint import Linter
from common.git import Git

from slack import slack

# Executors
linter = Linter()

print(f"Branch: {os.environ['REPO_BRANCH']}")

git = Git(
    before = os.environ.get("SHA_BEFORE"), 
    after = os.environ.get("SHA_AFTER"), 
    repo = os.environ.get("REPO_NAME"),
    token = os.environ.get("REPO_TOKEN"),
    branch = os.environ.get("REPO_BRANCH")
)

report = linter.lint(git = git)

# linter.terminal(report = report)

count = git.sync_issues(report = report)

if count > 0:
    
    print(f"reports: {count}")
    
    sender = slack.lookup_bot(oauth = os.environ.get("SLACK_OAUTH"))
    receiver = slack.lookup_channel(name = "github-actions")

    if report.counts.errors.total == 1:
        pluralised = "is 1 unresolved issue"
    else:
        pluralised = f"are {count} unresolved autolint issues"

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": f"The Github Actions autobuild has halted because there {pluralised}. Please fix these problems and try again.",
                "emoji": True
            }
        }, {
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🚀  View Action",
                    "emoji": True
                },
                "url": f"https://github.com/{os.environ.get('REPO_NAME')}/actions/runs/{os.environ.get('GIT_RUN')}",
                "style": "primary"
            }, {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "🐞  View Errors",
                    "emoji": True
                },
                "url": f"https://github.com/{os.environ.get('REPO_NAME')}/issues?q=is%3Aopen+is%3Aissue+label%3Aautolint",
                "style": "danger"
            }]
        }
    ]

    # slack.send_blocks(blocks = blocks, sender = sender, receiver = receiver)
    
    sys.exit(1)

else:
    
    print(f"hellow: {count}")