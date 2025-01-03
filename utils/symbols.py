
def get_symbols():
    with open('tickers.txt', 'r') as f:
        symbols = [line.strip() for line in f if line.strip()]
    return symbols
