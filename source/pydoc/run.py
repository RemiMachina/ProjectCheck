#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
import math
import subprocess

from functools import reduce

# Pylint arguments and checks
inputs = {
    "config": "/source/pydocstyle/.pydocstyle",
}

parse = lambda key, value: f"--{key} {value}" if value != "" else  f"--{key}"
arguments = " ".join(list(map(lambda a: parse(*a), inputs.items())))

processed = {}

unknown_mapping = "💩 Unknown"
pydoc_mappings = {
    "🔍 Missing": {"key": "missing", "codes": ["D100", "D101", "D102", "D103", "D104", "D105", "D106", "D107"]},
    "👎 Conventions": {"key": "conventions", "codes": list(map(lambda n: f"D{n}", list(range(200, 216)) + list(range(300, 303)) + list(range(400, 418))))}
}

code_mappings = dict(reduce(lambda c, d: c + d, list(map(lambda a: list(map(lambda b: (b, a[0]), a[1]["codes"])), pydoc_mappings.items())), []))
key_mappings = dict(list(map(lambda a: (a[0], a[1]["key"]), pydoc_mappings.items())) + [(unknown_mapping, "unknown")])

max_code = 0

output = subprocess.run(f"find . -type f -name '*.py' | xargs pydocstyle {arguments}", shell = True, capture_output = True).stdout.decode("utf-8").split("\n")

print(output)

for source, reason in zip(output[0::2], output[1::2]):
    
    path = re.split(r":([0-9]+)", source)[0][2:]
    line = re.search(r":([0-9]+)", source)[0][1:]
    
    try:
        module = re.search(r"`(.*)`", source)[0][1:-1]
    except TypeError: 
        module = None
    
    code = re.search(r"( [A-Z][0-9]+:)", reason)[0][1:-1]
    message = re.split(r"( [A-Z][0-9]+: )", reason)[2]
    
    max_code = max(len(code), max_code)
    
    if path not in processed:
        processed[path] = {"codes": {}, "counts": dict(map(lambda a: (a, 0), list(pydoc_mappings.keys()) + [unknown_mapping]))}
    
    if code not in processed[path]["codes"]:
        processed[path]["codes"][code] = []
    
    if code not in code_mappings:
        code_mappings[code] = unknown_mapping
    
    processed[path]["counts"][code_mappings[code]] += 1
    
    processed[path]["codes"][code].append({
        "path": path,
        "line": int(line),
        "module": module,
        "code": code,
        "message": message
    })
    
total_missing = 0
total_conventions = 0
total_unknown = 0

for file, data in processed.items():
    
    print("")
    print("")
    print(f" *** {file} ***")
    print("")
    
    for title, count in list(filter(lambda a: a[1] != 0, data["counts"].items())):
        print(f" {title} | {count}")
        globals()[f"total_{key_mappings[title]}"] += count
    
    for code, items in sorted(data["codes"].items(), key = lambda a: a[0]):
    
        code_indent = " " * (max_code - len(code))
    
        print("")
        print(f" {code_indent}{code}")
    
        for item in sorted(items, key = lambda a: a["line"]):
    
            line_indent = " " * (max_code - len(str(item["line"])))
            module = f"`{item['module']}` - " if item["module"] is not None else ""
    
            print(f" {line_indent}({item['line']}) : {module}{item['message']}")
    
        
# Output to Github  
print(f"::set-output name=pydoc_missing::{total_missing}")
print(f"::set-output name=pydoc_conventions::{total_conventions}")
# print(f"::set-output name=pydocstyle_unknown::{total_unknown}")

