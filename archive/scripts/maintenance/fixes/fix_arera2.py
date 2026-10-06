import json

with open('data/config/arera_tariffs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for section in ['GAS_VOL', 'GAS_ACCISE']:
    for key in data.get(section, {}):
        tiers = data[section][key]
        if isinstance(tiers, list) and len(tiers) > 0:
            if tiers[-1][0] == 999999:
                tiers[-1][0] = 9999999

with open('data/config/arera_tariffs.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
