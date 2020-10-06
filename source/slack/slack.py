#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Type, Dict, List, Tuple
import requests
import json

from . import directories

class slack:
    
    # Action Methods
    
    api_url = lambda endpoint: f"https://slack.com/api/{endpoint}"
    
    # @classmethod
    # def send_basic(cls, text: str, from: Type[Sender], to: Type[Recevier]):
    
    # "conversations.list"
    
    @classmethod
    def send_blocks(cls, blocks: List[Dict], sender: directories.Bot, receiver: directories.Channel):
        
        response = requests.post(
            url = cls.api_url("chat.postMessage"), 
            data = json.dumps({
                "channel": receiver.id,
                "token": sender.oauth,
                "blocks": blocks
            }),
            headers = cls._slack_api_auth(token = sender.oauth)
        )
        
        print(response)
        print(response.json())
        
    @classmethod
    def send_file(cls, data: str, sender: directories.Bot, receiver: directories.Channel):
    
        response = requests.post(
            url = cls.api_url("files.upload"),
            data = json.dumps({
                "channels": receiver.id,
                "token": sender.oauth,
                "file": data,
                "filename": path.split("/")[-1],
                "filetype": path.split(".")[-1]
            }),
            headers = cls._slack_api_auth(token = sender.oauth)
        )
        
        print(response)
        print(response.json())
    
    @classmethod
    def _slack_api_auth(cls, token: str) -> Dict[str, str]:
    
        return {"Content-Type": "application/json;charset=utf-8", "Authorization": "Bearer {}".format(token)}
    
    # def _slack_get(self, method: str, token):
    # 
    #     get = requests.get(url.format(method), headers = )
    
    # Lookup Methods
    
    @classmethod
    def _lookup_filter(cls, locals: List[Tuple[str, any]]) -> Dict[str, any]:
    
        return dict(filter(lambda a: a[0] not in ["kwargs", "cls"] and a[1] is not None, locals))
    
    @classmethod
    def lookup_user(cls, name: str = None, email: str = None, github: str = None) -> directories.User:
        
        # Filter down to only listed & provided arguments
        lookup = cls._lookup_filter(locals = locals().items())

        if len(lookup) == 0:
            raise directories.UserNotFound("No valid user lookup details were provided")

        try:
            user = directories.UserDirectory.lookup(**lookup)
        except directories.DirectoryObjectNotFound:
            raise directories.UserNotFound(f"No user could be found with the following lookup criteria: {lookup}")
            
        return user

    @classmethod
    def lookup_channel(cls, name: str = None) -> directories.Channel:
        
        # Filter down to only listed & provided arguments
        lookup = cls._lookup_filter(locals = locals().items())

        if len(lookup) == 0:
            raise directories.ChannelNotFound("No valid channel lookup details were provided")

        try:
            channel = directories.ChannelDirectory.lookup(**lookup)
        except directories.DirectoryObjectNotFound:
            raise directories.ChannelNotFound(f"No channel could be found with the following lookup criteria: {lookup}")
            
        return channel
        
    # @classmethod
    # def lookup_bot(cls, name: str = None) -> directories.Bot:
    # 
    #     # Filter down to only listed & provided arguments
    #     lookup = cls._lookup_filter(locals = locals().items())
    # 
    #     if len(lookup) == 0:
    #         raise directories.BotNotFound("No valid bot lookup details were provided")
    # 
    #     try:
    #         bot = directories.BotDirectory.lookup(**lookup)
    #     except directories.DirectoryObjectNotFound:
    #         raise directories.BotNotFound(f"No bot could be found with the following lookup criteria: {lookup}")
    # 
    #     return bot
        
    @classmethod
    def lookup_bot(cls, oauth) -> directories.Bot:
        
        # Temp workaround because the action has to be public
        return directories.Bot(oauth = oauth)