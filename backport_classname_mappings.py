import os, json

with open("./classname_mappings.json", 'r') as fp:
    data = json.load(fp)

def generate(data : dict, version : int):
    print(f"Generating for version {version}")
    final = {}

    for module_id in data["module_mappings"]:
        module = data["module_mappings"][module_id]

        for classname_id in module["classname_mappings"]:
            key = f"{module_id}_{classname_id}"
            if key not in final:
                final[key] = []

            items = sorted(module["classname_mappings"][classname_id].items(), key=lambda x: int(x[0]))

            for i, (k, v) in enumerate(items):
                if v not in final[key] and int(k) <= version:
                    final[key].append(v)

            for i, (k, v) in enumerate(items):
                if v not in final[key]:
                    final[key].insert(len(final[key]) - 1, v)

    return final

last_beta = sorted([int(x[0]) for x in data["versions"].items() if x[1] == "beta"])[-1]
last_stable = sorted([int(x[0]) for x in data["versions"].items() if x[1] == "stable"])[-1]

beta = generate(data, last_beta)
stable = generate(data, last_stable)

with open("./beta.json", 'w') as fp:
    json.dump(beta, fp)

with open("./stable.json", 'w') as fp:
    json.dump(stable, fp)