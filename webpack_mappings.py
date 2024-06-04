import json, os, sys, uuid

option_latest = "--latest" in sys.argv

with open("css_mappings.json") as fp:
    mappings = json.load(fp)

with open("webpack.json") as fp:
    webpack = json.load(fp)

webpack_length = len(webpack)
duplicate_webpack = []

for x in webpack:
    if len(webpack[x]) > 1:
        duplicate_webpack.append(x)

for x in duplicate_webpack:
    del webpack[x]

print(f"Stripped {len(duplicate_webpack)}/{webpack_length} duplicate mappings")

added_count = 0
skipped_count = 0
edited_count = 0

added_dict = {}

for x in webpack:
    success = False

    # Pass 1
    for y in mappings:
        val = webpack[x][0]
        val_in_mappings = val in mappings[y]
        key_in_mappings = x in mappings[y]

        if key_in_mappings and val_in_mappings:
            skipped_count += 1
            success = True
            break
        elif key_in_mappings and not val_in_mappings:
            edited_count += 1

            if option_latest:
                mappings[y].append(val)
            else:
                mappings[y].insert(0, val)

            success = True
            break

    # Pass 2
    if not success:
        for y in mappings:
            val = webpack[x][0]
            val_in_mappings = val in mappings[y]
            key_in_mappings = x in mappings[y]

            if val_in_mappings and not key_in_mappings:
                edited_count += 1
                mappings[y].insert(0, x)
    
                success = True
                break
    
    if not success:
        print(f"Couldn't map {webpack[x][0]} -> {x}")
        added_count += 1
        added_dict[str(uuid.uuid4())] = [x, val]

print(f"Added {added_count}, skipped {skipped_count}, edited {edited_count}")

if (added_count > 0):
    print("New translations for your consideration: css_mappings_new.json")

    with open("css_mappings_new.json", 'w') as fp:
        json.dump(added_dict, fp)

with open("css_mappings_edited.json", 'w') as fp:
    json.dump(mappings, fp)