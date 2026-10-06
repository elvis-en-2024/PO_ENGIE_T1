import re
html = open('page_source.html', 'r', encoding='utf-8').read()
apis = re.findall(r'\"([^\"]*api[^\"]*)\"', html)
urls = re.findall(r'\"(/[^\"]*ricerca[^\"]*)\"', html)
print("APIs:", set(apis))
print("URLs:", set(urls))
