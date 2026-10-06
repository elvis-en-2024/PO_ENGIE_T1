from bs4 import BeautifulSoup
import re
with open('ELE_2700.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')
for card in soup.select('div.search-results-list div[class*=card]')[:15]:
    offer_name = card.select_one('.offer-title')
    price = card.select_one('.price-value')
    if offer_name and price:
        print(offer_name.text.strip(), price.text.strip())
