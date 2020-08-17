#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import math
import argparse
import subprocess


# Script arguments
parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", help = "The path to run the linting process inside")

args = parser.parse_args()

# Pylint arguments and checks
arguments = {
    "output-format": "json",
    "jobs": "0",
    "persistent": "n",
    "exit-zero": ""
}

parse = lambda key, value: f"--{key} {value}" if value != "" else  f"--{key}"
parsed = " ".join(list(map(lambda a: parse(*a), arguments.items())))

processed = {}

max_line = 0
max_column = 0
max_id = 0

length = lambda number: math.floor(math.log10(number) + 1) if number > 0 else len(str(number))


# Execute linting
for issue in json.loads(subprocess.run(f"find {args.path} -type f -name '*.py' | xargs pylint {parsed}", shell = True, capture_output = True).stdout.decode("utf-8")):
    
    if issue["path"] not in processed:
        processed[issue["path"]] = {"issues": [], "counts": {"warning": 0, "error": 0, "fatal": 0, "convention": 0, "information": 0, "refactor": 0}}
    
    processed[issue["path"]]["counts"][issue["type"]] += 1
    
    max_line = max(max_line, length(issue["line"]))
    max_column = max(max_column, length(issue["column"]))
    max_id = max(max_id, len(issue["message-id"]))    
    
    issue["print"] = []
    
    # Split multi-line outputs
    for index, line in enumerate(list(filter(lambda a: a != "", issue["message"].replace("{", "[").replace("}", "]").split("\n")))):
        
        if index == 0:
            issue["print"].append(" {}" + f"{issue['line']}:{issue['column']}" + "{} - " + f"({issue['message-id']})" + "{} " + line)
        else:
            issue["print"].append(" {}" + line) 
               
    processed[issue["path"]]["issues"].append(issue)


# Run formatting and output
newline_indent = " " * (max_line + 1 + max_column + 3 + 2 + max_id + 2)

lint_titles = {
    "warning": "⚠️ Warnings",
    "error": "🛑 Errors",
    "fatal": "🚨 Fatal Errors",
    "convention": "👍 Conventions",
    "information": "💁‍♀️ Information",
    "refactor": "🔧 Refactor"
}

total_errors = 0
total_warnings = 0

for file, data in processed.items(): 
    
    print("")
    print("")
    print(f" *** {file} ***")
    print("")
    
    for key, count in list(filter(lambda a: a[1] != 0, data["counts"].items())):
        print(" {lint_titles[key]}: {count}")
        
    for issue in data["issues"]:    
        
        # Calculate indentations
        line_indent = " " * (max_line - length(issue["line"]))
        column_indent = " " * (max_column - length(issue["column"]))
        id_indent = " " * (max_id - len(issue["message-id"]))
        
        for index, line in enumerate(issue["print"]):
            
            if index == 0:
                print(line.format(line_indent, column_indent, id_indent))
            else:
                print(line.format(newline_indent))


# Output to Github environment            
subprocess.run(f"echo \"::set-env name=lint_errors::{total_errors}\"", shell = True)
subprocess.run(f"echo \"::set-env name=lint_warnings::{total_warnings}\"", shell = True)