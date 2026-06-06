import requests

url = "https://query2.finance.yahoo.com/v7/finance/options/SPY"
headers = {'User-Agent': 'Mozilla/5.0'}
res = requests.get(url, headers=headers)
print("Status:", res.status_code)
print(res.text[:200])
