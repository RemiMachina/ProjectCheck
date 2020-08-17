#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import subprocess

print(subprocess.run("pwd", shell = True, capture_output = True).stdout.decode("utf-8"))

# Pylint arguments and checks
arguments = {
    "rcfile": "/source/pylint/.pylintrc",
    "exit-zero": ""
}

parse = lambda key, value: f"--{key} {value}" if value != "" else  f"--{key}"
parsed = " ".join(list(map(lambda a: parse(*a), arguments.items())))

processed = {}

max_line = 0
max_column = 0
max_id = 0

length = lambda number: math.floor(math.log10(number) + 1) if number > 0 else len(str(number))

lint_titles = {
    "warning": "⚠️ Warnings",
    "error": "🛑 Errors",
    "fatal": "🚨 Fatal Errors",
    "convention": "👍 Conventions",
    "information": "💁‍♀️ Information",
    "refactor": "🔧 Refactor"
}


# Execute linting
for issue in json.loads(subprocess.run(f"find . -type f -name '*.py' | xargs pylint {parsed}", shell = True, capture_output = True).stdout.decode("utf-8")):
    
    if issue["path"] not in processed:
        processed[issue["path"]] = {"issues": [], "counts": dict(map(lambda a: (a, 0), lint_titles.keys())), "keys": []}
    
    # JSON output appears to have duplicate warnings
    # This key prevents those duplications from being added
    key = f"{issue['line']}:issue['column']:issue['type']:issue['symbol']:issue['message']"
    
    if key in processed[issue["path"]]["keys"]:
        continue
        
    processed[issue["path"]]["keys"].append(key)
    
    processed[issue["path"]]["counts"][issue["type"]] += 1
    
    max_line = max(max_line, length(issue["line"]))
    max_column = max(max_column, length(issue["column"]))
    max_id = max(max_id, len(issue["message-id"]))    
    
    issue["print"] = []
    
    left_chop = 0
    
    # Split multi-line outputs
    for index, line in enumerate(list(filter(lambda a: a != "", issue["message"].replace("{", "{{").replace("}", "}}").split("\n")))):
        
        if index == 1 and len(line) - len(line.lstrip()) != 0:
            left_chop = len(line) - len(line.lstrip())
        
        if index >= 1 and left_chop != 0:
            line = line[left_chop:]
        
        if index == 0:
            issue["print"].append(" {}" + f"{issue['line']}:{issue['column']}" + "{} - " + f"({issue['message-id']})" + "{} " + line + f" ({issue['symbol']})")
        else:
            issue["print"].append(" {}" + line) 
               
    processed[issue["path"]]["issues"].append(issue)


# Run formatting and output
newline_indent = " " * (max_line + 1 + max_column + 3 + 2 + max_id + 2)

total_errors = 0
total_warnings = 0
total_suggestions = 0

for file, data in processed.items(): 
    
    print("")
    print("")
    print(f" *** {file} ***")
    print("")
    
    for key, count in list(filter(lambda a: a[1] != 0, data["counts"].items())):
        print(f" {lint_titles[key]} | {count}")
        
        if key == "error" or key == "fatal":
            total_errors += count
        elif key == "warning":
            total_warnings += count
        else:
            total_suggestions += count
        
    print("")
        
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
                

# Output to Github  
subprocess.run(f"echo \"::set-output name=pylint_errors::{total_errors}\"", shell = True) 
subprocess.run(f"echo \"::set-output name=pylint_warnings::{total_warnings}\"", shell = True) 
subprocess.run(f"echo \"::set-output name=pylint_suggestions::{total_suggestions}\"", shell = True) 

