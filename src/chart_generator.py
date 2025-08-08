import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
from datetime import datetime

def generate_price_chart(historical_data: list, token_symbol: str, period: str) -> bytes:
    """
    Generates a price chart from a list of historical data points and returns it as a byte stream.
    """
    if not historical_data:
        return b""

    prices = [float(p['price']) for p in historical_data]
    # The timestamp key is 'ts' from the OKX API
    timestamps = [datetime.fromtimestamp(int(p['ts']) / 1000) for p in historical_data]

    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, prices, marker='o', linestyle='-')
    
    plt.title(f'{token_symbol}/USD Price Chart ({period})')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    return buf.getvalue()
