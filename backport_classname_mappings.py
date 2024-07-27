import os, json

final = {}

with open("./classname_mappings.json", 'r') as fp:
    data = json.load(fp)

for module_id in data["module_mappings"]:
    module = data["module_mappings"][module_id]

    for classname_id in module["classname_mappings"]:
        key = f"{module_id}_{classname_id}"
        if key not in final:
            final[key] = []
        
        for x in module["classname_mappings"][classname_id].values():
            if x not in final[key]:
                final[key].append(x)

with open("./beta.json", 'w') as fp:
    json.dump(final, fp)