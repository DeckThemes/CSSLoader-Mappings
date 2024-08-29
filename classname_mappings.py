from lib.version import Version
from lib.webpack import Webpack
import os
import json

base_path = "./webpack"
versions : dict[Version, Webpack] = {}
for x in [Version(f) for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))]:
    versions[x] = x.load()

with open("./ignore.json", 'r') as fp:
    ignore = json.load(fp)

def find_version(id : str) -> Version:
    for x in versions:
        if id == x.timestamp:
            return x
    
    return None

def filter_single(key : str, val : str) -> bool:
    return len(val) <= 0 or val[0].isnumeric() or " " in val

class ModuleMapping:
    def __init__(self, data : dict[str, str], webpack_id : str):
        self.webpack_id = webpack_id
        self.raw = data
        self.mappings : dict[str, dict[str, str]] = {}
        self.valid = True
        self.ignore_webpack_name = []
        self.generate()

    def generate(self):
        first_version = find_version(next(iter(self.raw)))
        first_webpack_module = versions[first_version].ids[self.webpack_id]

        if len(first_webpack_module.mappings) >= 1000:
            self.valid = False
            return

        ids_to_not_map = [x for x in first_webpack_module.mappings if filter_single(x, first_webpack_module.mappings[x])]

        for x in ignore:
            if x in first_webpack_module.mappings:
                self.ignore_webpack_name.append(x)

        if len(ids_to_not_map) == len(first_webpack_module.mappings):
            self.valid = False
            return

        for x in self.raw:
            version = find_version(x)
            webpack_module = versions[version].ids[self.raw[x]]

            for y in webpack_module.mappings:
                if y in ids_to_not_map:
                    continue

                if y not in self.mappings:
                    self.mappings[y] = {}

                self.mappings[y][version.timestamp] = webpack_module.mappings[y]

    # TODO: Slow
    def match_value(self, css_class : str) -> dict[str, str]|None:
        for x in self.mappings:
            if css_class in self.mappings[x].values():
                return self.mappings[x]

        return None

    def to_dict(self) -> dict:
        for x in self.mappings:
            self.mappings[x] = dict(sorted(self.mappings[x].items(), key= lambda x: int(x[0])))

        return {
            "name": None,
            "ids": self.raw,
            "classname_mappings": self.mappings,
            "ignore_webpack_keys": self.ignore_webpack_name
        }


with open("webpack_id_mappings.json", 'r') as fp:
    data = json.load(fp)

modules = [ModuleMapping(data[x], x) for x in data]

with open("./beta.orig.json", "r") as fp:
    data = json.load(fp)

for i, (k, v) in enumerate(data.items()):
    items = v
    has_match = False

    for y in items[::-1]:

        if has_match:
            break

        for module in [z for z in modules if z.valid]:
            match = module.match_value(y)

            if match is None:
                continue

            items_to_add = [x for x in items if x not in match.values()]
            i = 0

            for item in items_to_add:
                while str(i) in match:
                    i += 1

                match[str(i)] = item

            has_match = True
            break
        
    if not has_match:    
        print(f"{items} had no matches")

final = {}
versions_dict = {}

for x in [z for z in modules if z.valid]:
    final[x.webpack_id] = x.to_dict()

for x in versions:
    versions_dict[x.timestamp] = x.type

with open("classname_mappings.json", 'w') as fp:
    json.dump({"versions": versions_dict, "module_mappings": final}, fp)