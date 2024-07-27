from .version import Version
from .webpack import Webpack, WebpackModuleMatch
from .utils import MATCH_LIMIT
from time import time

class MappingDiff:
    def __init__(self, base : Version, new : Version):
        self.base = base
        self.new = new
    
    def process(self) -> tuple[dict[str, WebpackModuleMatch], list[WebpackModuleMatch]]:
        start = time()
        base = self.base.load()
        new = self.new.load()

        tracked_matches : list[WebpackModuleMatch] = []
        exists_count = 0
        mappings = {}
        new_ids = []

        for x in new.modules:
            if x.id in base.ids:
                exists_count += 1
                continue

            matches = base.match(x)

            if len(matches.matches) <= 0:
                new_ids.append(matches)
            else:
                tracked_matches.append(matches)
        
        tracked_matches.sort(key=lambda x: x.first_match_percentage(), reverse=True)

        for x in tracked_matches:
            found = False
            for y in x.matches:
                if y.module.id not in mappings:
                    found = True
                    mappings[y.module.id] = x
                    print(f"Mapped {y.module.id} -> {x.search.id} with {y.match_percentage * 100}% confidence")
                    break

            if not found:
                print(f"New module with id {x.search.id} found no candidates ({str(x)}), assuming this is a new module")
                new_ids.append(x)

        print(f"Finished mapping {self.base.timestamp} -> {self.new.timestamp} in {time() - start}s\nExists: {exists_count}, New: {len(new_ids)}, Mapped: {len(mappings)}\nBase module count: {len(base.modules)}, New module count: {len(new.modules)}")
        
        return (mappings, new_ids)