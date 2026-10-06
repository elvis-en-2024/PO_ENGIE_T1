import app
import datetime as dt

df = app.load_data(dt.date.today().strftime('%Y-%m-%d'))
print(f'Total offers loaded: {len(df)}')
