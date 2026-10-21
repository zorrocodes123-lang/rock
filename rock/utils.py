from typing import Any, Callable
from .views import View
import re

class Path:
    def __init__(self, path:str, view:View):
        self.path = path
        self.view = view
        
