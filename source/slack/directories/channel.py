#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .base import Directory, DirectoryObject

class Channel(DirectoryObject):
    
    def __init__(self, id: str, name: str = None):
        
        self.id = id
        self.name = name
        self.hash_name = "#" + name

class ChannelDirectory(Directory):
    
    # The directory attribute is required by the Directory super class and is used to lookup DirectoryObjects
    directory = [
        Channel(id = "C018EDFN5NJ", name = "github-actions")
    ]
    
    # logging = "CJ6JV6JR2"
    # errors = "CJ0RM8GGH"
    # general = "C0B13A6MR"
    