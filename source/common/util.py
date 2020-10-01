#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess

from typing import List

class util:
    
    @staticmethod
    def exec(command) -> str:
        
        return subprocess.run(command, shell=True, capture_output=True).stdout.decode("utf-8")
    
    @staticmethod
    def files() -> List[str]:
        
        return list(map(lambda b: b, filter(lambda a: a != "", util.exec("find . -type f -name '*.py'").split("\n"))))
