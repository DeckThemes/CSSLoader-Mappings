import os, json, hashlib, base64

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
        self.is_beta = new.type.lower() == "beta" 
        self.base_version = base
        self.new_version = new
        self.base_ids = base.load().ids # TODO: Pull this from somewhere else
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

def get_module_id(version: str, module_id: str, is_beta : bool) -> str:
    m = hashlib.sha256()
    m.update(f"{version}:{module_id}:{'b' if is_beta else 's'}".encode('utf-8'))
    
    return base64.urlsafe_b64encode(m.digest()).decode('utf-8').replace("-", "z").replace("_", "Z")[:8]
    
TRACKER = {}

class Chain:
    def __init__(self, starting_version : str, starting_module_id : str, is_starting_beta : bool):
        self.id = get_module_id(starting_version, starting_module_id, is_starting_beta)
        self.chain = {}
        self.add(starting_version, starting_module_id, is_starting_beta)
    
    def add(self, version : str, module_id : str, is_beta : bool):
        self.chain[version] = module_id

        id = get_module_id(version, module_id, is_beta)
        if id in TRACKER:
            print(self.chain)
            print(TRACKER[id].chain)
            print(TRACKER[id] == self)
            raise Exception(f"Chain with id {id} already exists!")
        
        TRACKER[id] = self

if __name__ == "__main__":
    all : dict[str, list[str]] = {}
    first_stable = stable[0]
    first_beta = beta[0]
    first_stable_data = first_stable.load()

    stable_version_chain = [generate(stable[idx], stable[idx + 1]) for idx, x in enumerate(stable[:-1])]
    beta_version_chain = [generate(first_stable, first_beta)] + [generate(beta[idx], beta[idx + 1]) for idx, x in enumerate(beta[:-1])]
    all_version_chain = stable_version_chain + beta_version_chain
    all_version_chain.sort(key=lambda x: x.new_version.timestamp, reverse=False)
    chains : list[Chain] = []

    last_beta = last_stable = first_stable.timestamp

    for x in first_stable_data.ids.keys():
        chains.append(Chain(first_stable.timestamp, first_stable_data.ids[x].id, False))

    for mapping in all_version_chain:
        success = 0
        fail = 0

        for new_module in mapping.new:
            existing_stable_chain_id = get_module_id(last_stable, new_module.dst, False)
            existing_beta_chain_id = get_module_id(last_beta, new_module.dst, True)

            if existing_beta_chain_id in TRACKER:
                chain : Chain = TRACKER[existing_beta_chain_id]
                chain.add(mapping.new_version.timestamp, new_module.dst, mapping.is_beta)
            elif existing_stable_chain_id in TRACKER:
                chain : Chain = TRACKER[existing_stable_chain_id]
                chain.add(mapping.new_version.timestamp, new_module.dst, mapping.is_beta)
            else:
                chains.append(Chain(mapping.new_version.timestamp, new_module.dst, mapping.is_beta))
                
            success += 1

        for old_module_id in mapping.base_ids:
            new_module_id = mapping.map(old_module_id)

            if new_module_id is None:
                print(f"Module {old_module_id} from {mapping.base_version.timestamp} does not exist in {mapping.new_version.timestamp}")
                fail += 1
                continue

            existing_stable_chain_id = get_module_id(last_stable, old_module_id, False)
            existing_beta_chain_id = get_module_id(last_beta, old_module_id, True)

            if existing_beta_chain_id in TRACKER:
                chain : Chain = TRACKER[existing_beta_chain_id]
            elif existing_stable_chain_id in TRACKER:
                chain : Chain = TRACKER[existing_stable_chain_id]
            else:
                fail += 1
                print(f"Chain from {last_stable}|{last_beta}:{old_module_id} to {mapping.new_version.timestamp}:{new_module_id} does not exist!")
                continue

            success += 1
            chain.add(mapping.new_version.timestamp, new_module_id, mapping.is_beta)
        
        if mapping.is_beta:
            last_beta = mapping.new_version.timestamp
        else:
            last_stable = mapping.new_version.timestamp

        print(f"Successfully mapped {success} modules, failed to map {fail} modules in mapping {mapping.base_version.timestamp}->{mapping.new_version.timestamp}.")

    for chain in chains:
        all[chain.id] = chain.chain
        
    with open("./webpack_id_mappings.json", 'w') as fp:
        json.dump(all, fp)