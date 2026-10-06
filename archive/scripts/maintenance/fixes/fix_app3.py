with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

if "if 'step' not in st.session_state:" not in code:
    code = code.replace("if st.session_state.step == 1:", "if 'step' not in st.session_state:\n    st.session_state.step = 1\n\nif st.session_state.step == 1:")
    
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)
