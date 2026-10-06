import xml.etree.ElementTree as ET
from collections import defaultdict
import gzip
import argparse
import yaml
from pathlib import Path
from lxml import etree

def infer_type(value: str) -> str:
    if not value or not value.strip():
        return "string"
    val = value.strip()
    if val.isdigit():
        return "integer"
    try:
        float(val.replace(',', '.'))
        return "float"
    except ValueError:
        pass
    if len(val) == 10 and val.count("-") == 2:
        return "date"
    return "string"

def introspect(file_path: Path):
    print(f"Analizzando {file_path}...")
    paths = defaultdict(lambda: {"count": 0, "types": set(), "max_occurrences_per_parent": 0})
    
    source = gzip.open(file_path, 'rb') if file_path.suffix == '.gz' else str(file_path)
    context = etree.iterparse(source, events=('start', 'end'))
    
    path_stack = []
    occurrence_tracker = defaultdict(int)
    
    for event, elem in context:
        tag = elem.tag
        if event == 'start':
            path_stack.append(tag)
            current_path = "/" + "/".join(path_stack)
            occurrence_tracker[current_path] += 1
        elif event == 'end':
            current_path = "/" + "/".join(path_stack)
            paths[current_path]["count"] += 1
            if elem.text and elem.text.strip():
                paths[current_path]["types"].add(infer_type(elem.text))
            
            paths[current_path]["max_occurrences_per_parent"] = max(
                paths[current_path]["max_occurrences_per_parent"],
                occurrence_tracker[current_path]
            )
            occurrence_tracker[current_path] = 0
            
            path_stack.pop()
            elem.clear()
            
    mapping = {}
    for p, stats in paths.items():
        mapping[p] = {
            "type": list(stats["types"])[0] if len(stats["types"]) == 1 else "mixed",
            "is_list": stats["max_occurrences_per_parent"] > 1,
            "target_field": f"TODO_map_{p.split('/')[-1].lower()}"
        }
        
    out_file = file_path.with_suffix('.yaml')
    with open(out_file, 'w', encoding='utf-8') as f:
        yaml.dump(mapping, f, sort_keys=True, allow_unicode=True)
    print(f"Introspezione completata. Mapping template generato in {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Estrae i percorsi XPath da un file XML grezzo.")
    parser.add_argument("xml_file", type=Path, help="Percorso del file XML (o .xml.gz)")
    args = parser.parse_args()
    introspect(args.xml_file)
