import yfinance as yf
ticker = yf.Ticker("SPY")
expirations = ticker.options
if expirations:
    print("Found expirations:", len(expirations))
    opt = ticker.option_chain(expirations[0])
    puts = opt.puts
    print("Found puts:", len(puts))
    print(puts.head(1).to_json(orient="records"))
