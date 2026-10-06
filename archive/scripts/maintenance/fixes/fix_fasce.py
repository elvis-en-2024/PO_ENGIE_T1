with open('engine/sas_calculator_fast.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_code = '''            if fasce in ('A Fasce', 'Biorario', 'Multiorario'):
                keep = ~dichiarata_mono
                if falsa_multioraria in ('escludi', 'riclassifica'):
                    keep &= ~falsa
                _drop(keep, f'fasce={fasce}')'''

new_code = '''            if fasce in ('A Fasce', 'Biorario', 'Multiorario'):
                if falsa_multioraria in ('escludi', 'riclassifica'):
                    keep = ~dichiarata_mono & ~falsa
                else:
                    # Il Portale Offerte MANTIENE anche le monorarie (e false multiorarie)
                    # nelle ricerche A Fasce se l'utente lo desidera.
                    import pandas as pd
                    keep = pd.Series(True, index=f.index)
                _drop(keep, f'fasce={fasce}')'''

content = content.replace(old_code, new_code)
with open('engine/sas_calculator_fast.py', 'w', encoding='utf-8') as f:
    f.write(content)
