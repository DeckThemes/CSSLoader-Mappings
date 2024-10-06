import os, json

from lib.mapping_diff import MappingDiff
from lib.version import Version
from lib.webpack import WebpackModuleMatch

base_path = "./webpack"
base_module_path = "./webpack-mappings"
#modules = [ModuleMapping(x, raw_modules[x]) for x in raw_modules]
files = [Version(f) for f in os.listdir(base_path) if os.path.isfile(os.path.join(base_path, f))]
files.sort(key=lambda x: x.timestamp)
beta = [x for x in files if x.type.lower() == "beta"]
stable = [x for x in files if x.type.lower() == "stable"]

print(beta)
print(stable)

class MappingEntry:
    def from_file(self, raw : dict):
        self.raw = raw
        self.dst = raw["new"]
        self.possible_mappings = raw["possible_mappings"]

        return self

    def from_generation(self, module_match : WebpackModuleMatch):
        self.dst = module_match.search.id
        self.possible_mappings = {}

        for x in module_match.matches:
            self.possible_mappings[x.module.id] = x.match_percentage

        return self

    def to_dict(self) -> dict:
        return {
            "new": self.dst,
            "possible_mappings": self.possible_mappings
        }

class Mapping:
    def __init__(self, base : Version, new : Version):
        self.base_version = base
        self.new_version = new
        self.new_ids = new.load().ids # TODO: Pull this from somewhere else

    def from_file(self, filename : str):
        with open(filename, 'r') as fp:
            self.raw = json.load(fp)
        
        self.new : list[MappingEntry] = [MappingEntry().from_file(x) for x in self.raw["new"]]
        self.mapped : dict[str, MappingEntry] = {}

        for x in self.raw["mapped"]:
            self.mapped[x] = MappingEntry().from_file(self.raw["mapped"][x])

    def from_generation(self, output : tuple[dict[str, WebpackModuleMatch], list[WebpackModuleMatch]]):
        self.new : list[MappingEntry] = [MappingEntry().from_generation(x) for x in output[1]]
        self.mapped : dict[str, MappingEntry] = {}

        for x in output[0]:
            self.mapped[x] = MappingEntry().from_generation(output[0][x])

    def to_file(self, filename : str):
        self.raw = {"new": [x.to_dict() for x in self.new], "mapped": {} }
        for x in self.mapped:
            self.raw["mapped"][x] = self.mapped[x].to_dict()
        
        with open(filename, 'w') as fp:
            json.dump(self.raw, fp)
        
    def map(self, base_id : str) -> str|None:
        if base_id in self.mapped:
            return self.mapped[base_id].dst
        
        if base_id not in self.new_ids:
            return None

        return base_id
    
    def __str__(self) -> str:
        return f"{str(self.base_version)}->{str(self.new_version)}"
    
    def __repr__(self) -> str:
        return str(self)

def generate(base : Version, new : Version) -> Mapping:
    filename = os.path.join(base_module_path, f"{base.timestamp}to{new.timestamp}.json")
    mapping = Mapping(base, new)

    if os.path.exists(filename):
        print(f"{filename} exists already, loading...")
        mapping.from_file(filename)
        return mapping
    
    mappingDiff = MappingDiff(base, new)
    diff = mappingDiff.process()
    mapping.from_generation(diff)
    mapping.to_file(filename)
    return mapping

# Map stable -> beta, then chain beta -> beta and stable -> stable

def add_all_new_mappings(mappings : list[Mapping], data : dict, check_if_new_exists : bool = False):
    translations = {}

    if check_if_new_exists:
        for x in data:
            for y in data[x]:
                if data[x][y] in translations and translations[data[x][y]] != x:
                    raise Exception("ID conflict!!")
                
                translations[data[x][y]] = x

    for mapping in mappings:
        for new in mapping.new:
            if check_if_new_exists and new.dst in translations:
                print(f"[Warn] Existing module found in version {mapping.new_version.timestamp} that is marked as new: {new.dst}")
                data[translations[new.dst]][mapping.new_version.timestamp] = new.dst
                continue

            if new.dst in data:
                data[new.dst][mapping.new_version.timestamp] = new.dst
                continue
            
            data[new.dst] = {
                mapping.new_version.timestamp: new.dst
            }

def add_all_existing_mappings(mappings : list[Mapping], data : dict, id : str):
    current_id = id
    hack = False
    run = False
    for mapping in mappings:
        # Hack to only start computing mapping from new version
        if len(data[id]) == 1:
            starting_version = next(iter(data[id]))
            if mapping.base_version.timestamp != starting_version:
                #print(f"Found mapping with id {data[id][starting_version]} that only starts at version {starting_version}, but currently at base version {mapping.base_version.timestamp}")
                hack = True
                continue

        run = True
        new = mapping.map(current_id)

        # Chain has ended, we can safely break
        if new is None:
            print(f"[{id}] Base module id {current_id} on version {mapping.base_version} has no related module in newer version {mapping.new_version}")
            break

        current_id = new
        data[id][mapping.new_version.timestamp] = new
    
    if hack and not run:
        starting_version = next(iter(data[id]))
        if starting_version != mappings[-1].new_version.timestamp:
            print(f"Mapping with id {id} does not have anything to map to. Suppost to start from {starting_version}")

if __name__ == "__main__":
    all : dict[str, list[str]] = {}
    first_stable = stable[0]
    first_beta = beta[0]
    first_stable_data = first_stable.load()
    for x in first_stable_data.ids.keys():
        all[x] = { first_stable.timestamp: x }

    stable_chain = [generate(stable[idx], stable[idx + 1]) for idx, x in enumerate(stable[:-1])]
    beta_chain = [generate(first_stable, first_beta)] + [generate(beta[idx], beta[idx + 1]) for idx, x in enumerate(beta[:-1])]

    add_all_new_mappings(beta_chain, all)

    for id in all:
        add_all_existing_mappings(beta_chain, all, id)

    add_all_new_mappings(stable_chain, all, True)

    for id in all:
        add_all_existing_mappings(stable_chain, all, id)
        
    
    with open("./webpack_id_mappings.json", 'w') as fp:
        json.dump(all, fp)



