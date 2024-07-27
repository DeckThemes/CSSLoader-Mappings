from .utils import MATCH_LIMIT

class WebpackModule:
    def __init__(self, id : str, mappings : dict):
        self.id = id
        self.mappings : dict[str, str] = mappings
        self.mapping_keys = mappings.keys()

    def match(self, other) -> float:
        if len(self.mapping_keys) <= 0 or len(other.mapping_keys) <= 0:
            return 0

        bigger = other.mapping_keys if len(other.mapping_keys) > len(self.mapping_keys) else self.mapping_keys
        smaller = self.mapping_keys if bigger is other.mapping_keys else other.mapping_keys

        match = 0

        for x in bigger:
            if x in smaller:
                match += 1

        return match / len(bigger)

class WebpackModuleMatchEntry:
    def __init__(self, module : WebpackModule, match_percentage : float):
        self.module = module
        self.match_percentage = match_percentage

    def __str__(self) -> str:
        return f"[{self.module.id}: {self.match_percentage * 100}%]"

class WebpackModuleMatch:
    def __init__(self, search : WebpackModule, matches : list[tuple[WebpackModule, float]]):
        self.search = search
        self.matches : list[WebpackModuleMatchEntry] = [WebpackModuleMatchEntry(x[0], x[1]) for x in matches]

    def first_match_percentage(self):
        return self.matches[0].match_percentage
    
    def __str__(self) -> str:
        return f"Search module ID: {self.search.id}, Matches: {','.join([str(x) for x in self.matches])}"

class Webpack:
    def __init__(self, data : dict):
        self.raw = data
        self.ids : dict[str, WebpackModule] = {}
        self.modules : list[WebpackModule] = []

        for x in data:
            module = WebpackModule(x, data[x])
            self.ids[x] = module
            self.modules.append(module)

    def match(self, webpack_module : WebpackModule) -> WebpackModuleMatch:
        if webpack_module.id in self.ids:
            return WebpackModuleMatch(webpack_module, [(self.ids[webpack_module.id], 1)])
        
        matches = [(x, x.match(webpack_module)) for x in self.modules]
        matches.sort(key=lambda x: x[1], reverse=True)
        return WebpackModuleMatch(webpack_module, [x for x in matches if x[1] > MATCH_LIMIT])
