#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests

from typing import List, Dict
from functools import reduce

from .util import util
from .pylint import LintReport, LintIssue

# Data Structures

class GitIssue:

    def __init__(self, number: int, title: str, body: str, labels: List[str], assignees: List[str], local: bool):

        self.number = number
        self.title = title
        self.body = body
        self.labels = labels
        self.assignees = assignees
        self.local = local
        
    @staticmethod
    def from_json(data: Dict[str, any]):
        
        if "pull_request" in data: return None
        if data["state"] == "closed": return None
        
        labels = list(map(lambda a: a["name"], data["labels"]))
        assignees = list(map(lambda a: a["login"], data["assignees"]))
        
        if "autolint" not in labels: return None

        return GitIssue(
            number = data["number"],
            title = data["title"],
            body = data["body"],
            labels = labels,
            assignees = assignees,
            local = False
        )

    @staticmethod
    def from_lint(lints: List[LintIssue], repo: str, after: str):
        
        first = lints[0]
        empty = "{}"
        base = f"{empty}\r\nhttps://github.com/{repo}/blob/{after}/{first.path}#L{empty}\r\n"
        
        try:
        
            return GitIssue(
                number = None,
                title = f"[{first.message_id}] " + first.symbol.replace("-", " ").capitalize() + " " + first.type + " in " + first.path,
                body = "".join(list(map(lambda a: base.format(b.message, b.line), lints))),
                labels = ["autolint", first.type],
                assignees = list(set(list(map(lambda a: a.blame.author, lints)))),
                local = True
            )
            
        except:
            
            print(lints)
            print(lints[0])
            for a in lints:
                print(a.blame.author)
            return 1/0
        
    def prepare_create(self) -> Dict[str, any]:
        
        return {
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
            "assignees": self.assignees
        }
        
    def prepare_close(self) -> Dict[str, any]:
        
        return {
            "state": "closed"
        }
        
    def prepare_update(self) -> Dict[str, any]:
        
        return {
            "title": self.title,
            "body": self.body,
            "labels": self.labels,
            "assignees": self.assignees,
            "state": "open"
        }
    
    def __eq__(self, other):
        return self.title == other.title and self.body == other.body and set(self.labels) == set(other.labels) and set(self.assignees) == set(other.assignees)
        
    
class GitBlame:

    def __init__(self, porcelain, focus):

        if porcelain[0].count(" ") == 2:
            self.sha, self.line_before, self.line_after = porcelain.pop(0).split(" ")
            self.line_group = None
        else:
            self.sha, self.line_before, self.line_after, self.line_group = porcelain.pop(0).split(" ")

        self.new = self.sha in focus
        self.code = porcelain.pop(-1)

        safe_split = lambda a: tuple(a) if len(a) == 2 else tuple(a + [""])

        lookup = dict(map(lambda a: safe_split(a.split(" ", 1)), porcelain))
        
        self.author = lookup["author"]
        self.committer = lookup["committer"]
        self.summary = lookup["summary"]
        

                
# Executors
            
class Git:

    def __init__(self, before: str, after: str, repo: str, token: str):

        self.before = before
        self.after = after
        self.repo = repo
        self.auth = {"Authorization": f"Bearer {token}"}

        # Produce a list of the git hashes that are included in the commit
        shas = util.exec("git log --format=format:%H").split("\n")
        self.focus = shas[shas.index(self.after):shas.index(self.before)]

    def blame(self, path: str) -> List[GitBlame]:

        # Produce a git blame for each line in the file
        path = path.replace(" ", "\ ")
        porcelain = util.exec(f"git blame --line-porcelain {path}").split("\n")
        endpoints = [index + 2 for index, line in enumerate(porcelain) if line[0:9] == "filename "]
        startpoints = [0] + endpoints[:-1]

        return list(map(
            lambda a: 
            GitBlame(porcelain = porcelain[a[0]:a[1]], focus = self.focus), 
            zip(startpoints, endpoints)
        ))

    def local_issues(self, report: LintReport) -> List[GitIssue]:
        
        issues = []
        
        for path, file_report in report.reports.items():
            
            issues += list(map(
                lambda a: 
                GitIssue.from_lint(lints = a, repo = self.repo, after = self.after), 
                file_report.lints.values()
            ))
            
        return issues
        
    def remote_issues(self) -> List[GitIssue]:
        
        response = requests.get(f"https://api.github.com/repos/{self.repo}/issues", headers=self.auth)
        
        return list(filter(
            lambda a: 
            a is not None, 
            map(
                lambda b: 
                GitIssue.from_json(b), 
                response.json()
            )
        ))
        
    def sync_issues(self, report: LintReport):

        updates = {}
        
        for local in self.local_issues(report = report):
            updates[local.title] = {"local": local, "remote": None}
            
        for remote in self.remote_issues():
            if remote.title in updates:
                updates[remote.title]["remote"] = remote
            else:
                updates[remote.title] = {"local": None, "remote": remote}

        for title, update in updates.items():
            
            if update["remote"] is None:
                self.create_issue(issue = update["local"])
            elif update["local"] is None:
                self.close_issue(issue = update["remote"])
            elif update["local"] is not None and update["remote"] is not None:
                self.update_issue(new = update["local"], old = update["remote"])

    def create_issue(self, issue: GitIssue): 

        response = requests.post(
            f"https://api.github.com/repos/{self.repo}/issues", 
            headers = self.auth, 
            json = issue.prepare_create()
        )

    def close_issue(self, issue: GitIssue):

        response = requests.patch(
            f"https://api.github.com/repos/{self.repo}/issues/{issue.number}", 
            headers = self.auth, 
            json = issue.prepare_close()
        )

    def update_issue(self, new: GitIssue, old: GitIssue):

        if new == old: return

        response = requests.patch(
            f"https://api.github.com/repos/{self.repo}/issues/{old.number}", 
            headers = self.auth, 
            json = new.prepare_update()
        )
