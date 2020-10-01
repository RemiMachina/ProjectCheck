#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

from typing import List

class util:
    
    @staticmethod
    def exec(command) -> str:
        
        run = subprocess.run(command, shell=True, capture_output=True)
        
        if run.stderr == b"":
            return run.stdout.decode("utf-8")
        else:
            print("Execution Error")
            print(f"Input: {command}")
            print(f"Output: {run.stderr.decode('utf-8')}")
            return run.stderr.decode("utf-8")
    
    @staticmethod
    def files() -> List[str]:
        
        return list(map(lambda b: b[2:], filter(lambda a: a != "", util.exec("find . -type f -name '*.py'").split("\n"))))
