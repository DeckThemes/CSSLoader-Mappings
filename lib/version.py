import os, json
from .utils import BASE_WEBPACK_PATH
from .webpack import Webpack

class Version:
    def __init__(self, filename : str):
        self.filename = filename
        split = filename.split(".")
        self.timestamp = split[0]
        self.type = split[1]
    
    def load(self) -> Webpack:
        with open(os.path.join(BASE_WEBPACK_PATH, self.filename), 'r') as fp:
            return Webpack(json.load(fp))
        
    def __str__(self) -> str:
        return f"{self.timestamp}.{self.type}"
    
    def __repr__(self) -> str:
        return str(self)