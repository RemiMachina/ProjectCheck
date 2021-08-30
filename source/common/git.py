#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests

from typing import List, Dict, Set
from functools import reduce

from .util import util
from .pylint import LintReport, LintIssue

# Data Structures

class GitIssue:

    def __init__(self, number: int, title: str, body: str, labels: List[str], assignees: List[str], local: bool, branch: str):

        self.number = number
        self.title = title
        self.body = body
        self.labels = labels
        self.assignees = assignees
        self.local = local
        self.branch = branch
        
    @staticmethod
    def from_json(data: Dict[str, any], branch: str):
        
        if "pull_request" in data: return None
        if data["state"] == "closed": return None
        
        labels = list(map(lambda a: a["name"], data["labels"]))
        assignees = list(map(lambda a: a["login"], data["assignees"]))
        
        if "autolint" not in labels: return None

        if branch != data["title"].split(" ")[1][1:-1]: return None

        return GitIssue(
            number = data["number"],
            title = data["title"],
            body = data["body"],
            labels = labels,
            assignees = assignees,
            local = False,
            branch = branch
        )

    @staticmethod
    def from_lint(lints: List[LintIssue], users: Set[str], repo: str, branch: str, after: str):
        
        first = lints[0]
        empty = "{}"
        base = f"{empty}\r\nhttps://github.com/{repo}/blob/{after}/{first.path}#L{empty}\r\n"
        
        common_issues = {
            "E0611": "This issue is often flagged by pylint when an imported pip package and a local python file share the same name. You can disable the check in this file by adding a pylint disable comment to the end of each offending line:\r\n`import blah # pylint: disable=E0611`.",
            "E0402": "This issue is often flagged by pylint because it is unsure of the Python context that the script will be run in. If you are sure that this import is ok, you can disable the error by adding a pylint disable comment to the end of each offending line:\r\n`import .blah # pylint: disable=E0402`."
        }
            
        try:
            common_warning = ">**Note:**\r\n>" + common_issues[first.message_id] + "\r\n\r\n"
        except KeyError:
            common_warning = ""
        
        if branch == "master":
            branch_label = "ᚶ master"
        elif branch == "develop":
            branch_label = "ᚶ develop"
        else:
            branch_label = "ᚶ feature"

        return GitIssue(
            number = None,
            title = f"[{first.message_id}] [{branch}] " + first.symbol.replace("-", " ").capitalize() + " " + first.type + " in " + first.path,
            body = common_warning + "".join(list(map(lambda a: base.format(a.message, a.line), lints))),
            labels = ["autolint", first.type, branch_label],
            assignees = list(set(list(map(lambda a: a.blame.author, lints))).intersection(users)),
            local = True,
            branch = branch
        )
        
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

    def __init__(self, before: str, after: str, repo: str, token: str, branch: str):

        self.before = before
        self.after = after
        self.repo = repo
        self.auth = {"Authorization": f"Bearer {token}"}
        self.branch = branch

        # Produce a list of the git hashes that are included in the commit
        shas = util.exec("git log --format=format:%H").split("\n")
        self.focus = shas[util.safe_index(shas, self.after):util.safe_index(shas, self.before)]

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
        users = self.remote_users()
        
        for path, file_report in report.reports.items():
            for hash, lints in file_report.lints.items():
                issues.append(GitIssue.from_lint(lints = lints, users = users, repo = self.repo, branch = self.branch, after = self.after))
                
        return issues
        
    def remote_issues(self) -> List[GitIssue]:
        
        issues = []
        
        page = 1
        max = 100
        finished = False
        
        empty = "{}"
        url = f"https://api.github.com/repos/{self.repo}/issues?per_page={max}&state=open&page={empty}"
            
        while not finished:
        
            response = requests.get(url.format(page), headers=self.auth)
            
            issues += list(filter(
                lambda a: 
                a is not None, 
                map(
                    lambda b: 
                    GitIssue.from_json(data=b, branch=self.branch), 
                    response.json()
                )
            ))
            
            if len(issues) / page < max:
                finished = True
        
            page += 1
        
        return issues
        
    def remote_users(self) -> Set[str]:
        
        users = []
        
        page = 1
        max = 100
        finished = False
        
        empty = "{}"
    
        url = f"https://api.github.com/repos/{self.repo}/collaborators?per_page={max}&affiliation=all&page={empty}"
            
        while not finished:
        
            response = requests.get(url.format(page), headers=self.auth)
            
            users += list(map(
                lambda a:
                a["login"],
                response.json()
            ))
            
            if len(users) / page < max:
                finished = True
        
            page += 1
        
        return set(users)
        
    def sync_issues(self, report: LintReport) -> int:

        updates = {}
        
        for local in self.local_issues(report = report):
            updates[local.title] = {"local": local, "remote": None}

        for remote in self.remote_issues():
            if remote.title in updates:
                updates[remote.title]["remote"] = remote
            else:
                updates[remote.title] = {"local": None, "remote": remote}

        count = 0

        for title, update in updates.items():
            print(title)
            if update["remote"] is None:
                self.create_issue(issue = update["local"])
                count += 1
            elif update["local"] is None and self.branch == update["remote"].branch:
                self.close_issue(issue = update["remote"])
            elif update["local"] is not None and update["remote"] is not None:
                self.update_issue(new = update["local"], old = update["remote"])
                count += 1

        return count

    def create_issue(self, issue: GitIssue): 

        response = requests.post(
            f"https://api.github.com/repos/{self.repo}/issues", 
            headers = self.auth, 
            json = issue.prepare_create()
        )
        
        print(response)
        print(response.json())

    def close_issue(self, issue: GitIssue):

        response = requests.patch(
            f"https://api.github.com/repos/{self.repo}/issues/{issue.number}", 
            headers = self.auth, 
            json = issue.prepare_close()
        )

    def update_issue(self, new: GitIssue, old: GitIssue):

        if (new.title == old.title) and (new.body == old.body) and (set(new.labels) == set(old.labels)) and (set(new.assignees) == set(old.assignees)):
            print("No update required")
            return

        response = requests.patch(
            f"https://api.github.com/repos/{self.repo}/issues/{old.number}", 
            headers = self.auth, 
            json = new.prepare_update()
        )
