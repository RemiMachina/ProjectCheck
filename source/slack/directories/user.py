#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import Directory, DirectoryObject

class User(DirectoryObject):
    
    def __init__(self, id: str, name: str = None, email: str = None, github: str = None):
        
        self.id = id
        self.name = name
        self.email = email
        self.github = github

class UserDirectory(Directory):
    
    # The directory attribute is required by the Directory super class and is used to lookup DirectoryObjects
    directory = []
        


        