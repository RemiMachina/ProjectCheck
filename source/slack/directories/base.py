#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .errors import DirectoryObjectNotFound

import abc
from functools import reduce

class Directory(abc.ABC):
    
    @classmethod    
    def lookup(cls, **kwargs):
        
        results = list(filter(lambda user: user.lookup(**kwargs), cls.directory))
        
        if len(results) == 0:
            raise DirectoryObjectNotFound(f"No object could be found with the following lookup criteria: {kwargs}")
            
        return results[0]
        
    @property
    @abc.abstractmethod
    def directory(self):
        raise NotImplementedError("The directory property needs to be implemented")

class DirectoryObject(abc.ABC):
    
    def lookup(self, **kwargs) -> bool:
        
        """ Directory Object: Lookup

        Args:
            **kwargs (Any): Any lookup arguments to be check against the object.

        Returns:
            bool: A boolean flag indicating if the object passed the lookup check.

        """
        
        # Set of all non-None class attributes
        attributes = set(dict(filter(lambda a: a[1] != None, self.__dict__.items())).keys())
        
        if len(set(kwargs.keys()) - attributes) != 0:
            # If lookup conditions are specified that are not in this object 
            return False
        
        return reduce(lambda a, b: a and (self.safe_compare(left = getattr(self, b[0]), right = b[1])), kwargs.items(), True)
        
    def safe_compare(self, left: any, right: any) -> bool:
        
        if type(left) == str and type(right) == str:
            return left.lower() == right.lower()
        else:
            return left == right
        
        
class Sender(DirectoryObject):

    pass
    
class Receiver(DirectoryObject):
    
    pass