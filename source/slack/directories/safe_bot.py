#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import Directory, DirectoryObject

class Bot(DirectoryObject):
    
    def __init__(self, oauth: str):
    
        self.oauth = oauth