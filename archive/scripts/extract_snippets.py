import os
import glob
import re
from markitdown import MarkItDown

def extract_snippets():
    md = MarkItDown()
    base_dir = r'data\raw\ctes'
    
    with open('data/processed/snippets.md', 'w', encoding='utf-8') as fout:
        for competitor in os.listdir(base_dir):
            comp_dir = os.path.join(base_dir, competitor)
            if not os.path.isdir(comp_dir): continue
            
            pdfs = glob.glob(os.path.join(comp_dir, '**', '*.pdf'), recursive=True)
            if not pdfs: continue
            
            fout.write(f"\n\n# {competitor}\n")
            
            valid_found = 0
            for pdf in pdfs:
                if valid_found >= 2: break # Check up to 2 valid PDFs
                
                try:
                    text = md.convert(pdf).text_content
                    text_lower = text.lower()
                    
                    keywords = ['pun', 'psv', 'commercializzazione', 'dispbt', 'materia energia', 'quota fissa']
                    if sum(1 for k in keywords if k in text_lower) < 2:
                        continue
                        
                    valid_found += 1
                    fout.write(f"## {os.path.basename(pdf)}\n")
                    
                    lines = text.split('\n')
                    printed = 0
                    for i, line in enumerate(lines):
                        if printed > 15: break
                        if 'commercializzazione' in line.lower() or 'quota fissa' in line.lower() or 'pun ' in line.lower() or 'psv ' in line.lower() or '€/kwh' in line.lower() or '/kwh' in line.lower() or '/pod' in line.lower():
                            context = "\n".join(lines[max(0, i-2):i+3])
                            fout.write(f"```\n{context}\n```\n")
                            printed += 1
                            
                except:
                    pass

if __name__ == "__main__":
    os.makedirs('data/processed', exist_ok=True)
    extract_snippets()
