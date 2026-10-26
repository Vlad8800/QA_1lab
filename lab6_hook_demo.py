RATES = {number: number for number in range(1, 12)}

def demo_rate(value):
    return RATES.get(value, 0)
