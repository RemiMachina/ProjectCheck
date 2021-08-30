#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import copy
import itertools

from typing import List, Dict
from functools import reduce

from .util import util
# from .git import GitBlame



# Data Structures
        
class LintIssue:
    
    def __init__(self, issue: Dict[str, str], blame):
        
        self.blame = blame
        
        self.path = issue["path"]
        self.line = issue["line"]
        self.column = issue["column"]
        self.symbol = issue["symbol"]
        self.message = issue["message"]
        self.message_id = issue["message-id"]
        self.type = issue["type"]
        
        # JSON output appears to have duplicate warnings
        # This key prevents those duplications from being processed
        self.key = f'{self.line}:{self.column}:{self.type}:{self.symbol}:{self.message}'
        self.hash = f"{self.path}:{self.message_id}"
    
        self.new = True
    
        self.print = []
        left_chop = 0

        # Split multi-line outputs
        for index, line in enumerate(list(filter(lambda a: a != "", self.message.replace("{", "{{").replace("}", "}}").split("\n")))):

            if index == 1 and len(line) - len(line.lstrip()) != 0:
                left_chop = len(line) - len(line.lstrip())

            if index >= 1 and left_chop != 0:
                line = line[left_chop:]

            if index == 0:
                self.print.append(" {}" + f"{self.line}:{self.column}" + "{} - " + f"({self.message_id})" + "{} " + line + f" ({self.symbol})")
            else:
                self.print.append(" {}" + line) 
        
class LintCounter:
    
    def __init__(self):
        
        self.new = 0
        self.old = 0
        
    def increment(self, new: bool):
        
        if new:
            self.new += 1
        else:
            self.old += 1
            
    def __add__(self, other):
        
        self.new += other.new
        self.old += other.old
        
        return self
        
    @property
    def total(self) -> int:
        return self.new + self.old
        
class LintCategories:
    
    def __init__(self):
        
        self.warnings = LintCounter()
        self.errors = LintCounter()
        self.totals = LintCounter()
    
    def update(self, issue: LintIssue):
        
        if issue.type == "warning":
            self.warnings.increment(issue.new)
        elif issue.type == "errors":
            self.errors.increment(issue.new)
        else:
            return
            
        self.totals.increment(issue.new)
        
    def __add__(self, other):
        
        self.warnings += other.warnings
        self.errors += other.errors
        self.totals += other.totals
        
        return self
            
class LintMaximums:
    
    def __init__(self):
        
        self.line = 0
        self.column = 0
        self.message_id = 0
        
    def __add__(self, other):
        
        self.line = max(self.line, other.line)
        self.column = max(self.column, other.column)
        self.message_id = max(self.message_id, other.message_id)
        
        return self
        
    def length(self, number: int) -> int:
        
        return math.floor(math.log10(number) + 1) if number > 0 else len(str(number))
    
    def update(self, issue: LintIssue):
        
        self.line = max(self.line, self.length(issue.line))
        self.column = max(self.column, self.length(issue.column))
        self.message_id = max(self.message_id, len(issue.message_id))      
    
class LintFile:
    
    def __init__(self, path, blame):
        
        self.path = path
        self.blame = blame
        self.counts = LintCategories()
        self.maximums = LintMaximums()
        self.lints = {}
        self.keys = set()
    
    def is_duplicate(self, issue: LintIssue) -> bool:
        
        return issue.key in self.keys
    
    def append(self, issue: LintIssue):
        
        self.maximums.update(issue)
        self.counts.update(issue)
        
        self.keys.add(issue.key)
        
        if issue.hash not in self.lints:
            self.lints[issue.hash] = []
    
        self.lints[issue.hash].append(issue)

class LintReport:
    
    def __init__(self):

        self.reports = {}
        self.counts = LintCategories()
        self.maximums = LintMaximums()
        
    def __setitem__(self, path, report):
        
        self.counts += report.counts
        self.maximums += report.maximums
        
        self.reports[path] = report
        
    def __getitem__(self, path):
        return self.reports[path]


        
# Executors
    
class Linter:
    
    def __init__(self, rcfile = "/source/config/.pylintrc"):
    
        self.categories = {
            "warning": "⚠️ Warnings",
            "error": "🛑 Errors",
            "fatal": "🚨 Fatal Errors",
            "convention": "👎 Conventions",
            "information": "💁‍♀️ Information",
            "refactor": "🔧 Refactor"
        }
        
        pylint_arguments = {
            "rcfile": rcfile
        }
        
        self.arguments = " ".join(list(map(
            lambda a: 
            f"--{a[0]}" + (f"={a[1]}" if a[1] != "" else ""), 
            pylint_arguments.items()
        )))

    def lint(self, git) -> LintReport:
        
        report = LintReport()
        files = " ".join(list(map(lambda file: file.replace(" ", "\ "), util.files())))

        print(files)
    
        for path, issues in itertools.groupby(json.loads(util.exec(f"pylint {self.arguments} {files}")), key = lambda a: a["path"]):
            
            print(path)

            if len(issues) == 0:
                print(f"✓ - {path}")
            else:
                print(f"× - {path} ({len(issues)} issue(s) found)")

            blame = git.blame(path = path)
            file = LintFile(path = path, blame = blame)
        
            for issue in (LintIssue(issue = raw, blame = blame[raw["line"] - 1]) for raw in issues):
                
                if file.is_duplicate(issue):  
                    continue
                
                file.append(issue)
        
            report[path] = file
        
        return report
    
    def terminal(self, report: LintReport):
        
        indent = " " * (report.maximums.line + 1 + report.maximums.column + 3 + 2 + report.maximums.message_id + 2)
        
        for path, file_report in report.reports.items():
        
            print("")
            print("")
            print(f" *** {path} ***")
            print("")

            for hash, lints in file_report.lints.items():
                
                for issue in lints:

                    line_indent = " " * (file_report.maximums.line - file_report.maximums.length(issue.line))
                    column_indent = " " * (file_report.maximums.column - file_report.maximums.length(issue.column))
                    id_indent = " " * (file_report.maximums.message_id - len(issue.message_id))

                    for index, line in enumerate(issue.print):

                        if index == 0:
                            print(line.format(line_indent, column_indent, id_indent))
                        else:
                            print(line.format(indent))
