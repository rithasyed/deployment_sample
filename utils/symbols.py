
def get_symbols():
    with open('symbols.txt') as f:
        symbols = [line.strip() for line in f]
    return symbols
