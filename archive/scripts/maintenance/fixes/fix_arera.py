import json

with open('data/config/arera_tariffs.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for zone in data['GAS_VOL']:
    tiers = data['GAS_VOL'][zone]
    # change the last tier limit from 999999 to 9999999
    if tiers[-1][0] == 999999:
        tiers[-1][0] = 9999999

with open('data/config/arera_tariffs.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=4)
