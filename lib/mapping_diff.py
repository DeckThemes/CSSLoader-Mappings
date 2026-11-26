from .version import Version
from .webpack import Webpack, WebpackModuleMatch
from .utils import MATCH_LIMIT
from time import time

SUBSET_MIN_SHARED_KEYS = 8
SUBSET_MATCH_MARGIN = 0.15

class MappingDiff:
    def __init__(self, base : Version, new : Version):
        self.base = base
        self.new = new

    @staticmethod
    def _match_shrunken_module(base: Webpack, new_module) -> WebpackModuleMatch | None:
        """Match a new CSS module that retained most of an older module's exports.

        Steam sometimes removes exports from a CSS module without changing the
        remaining property names. The normal symmetric score penalizes that
        change by dividing by the larger module, so a new module that is a
        near-complete subset of its old version can fall below MATCH_LIMIT.
        Only accept subset matches with at least eight shared properties and a
        clear lead over the next candidate; otherwise leave the module unmapped.
        """
        new_keys = set(new_module.mapping_keys)
        if not new_keys:
            return None

        candidates = []
        for old_module in base.modules:
            shared = len(new_keys.intersection(old_module.mapping_keys))
            if shared < SUBSET_MIN_SHARED_KEYS:
                continue

            coverage = shared / len(new_keys)
            if coverage >= MATCH_LIMIT:
                candidates.append((old_module, coverage))

        candidates.sort(key=lambda x: x[1], reverse=True)
        if not candidates:
            return None

        if len(candidates) > 1 and candidates[0][1] - candidates[1][1] < SUBSET_MATCH_MARGIN:
            return None

        # Keep only the uniquely best candidate. Falling through to another
        # candidate after a collision would turn an ambiguous match into a
        # false positive.
        return WebpackModuleMatch(new_module, candidates[:1])
    
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
                subset_match = self._match_shrunken_module(base, x)
                if subset_match is None:
                    new_ids.append(matches)
                else:
                    tracked_matches.append(subset_match)
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
