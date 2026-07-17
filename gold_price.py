import requests

# آیدی عددی ادمین
ADMIN_ID = 106546961

async def send_alert_to_admin(context, message):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=message)
    except:
        pass

def get_gold_price_18k():
    try:
        response = requests.get(
            'https://api.tgju.online/v1/data/market',
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if 'response' in data and 'gold_18k' in data['response']:
                price = data['response']['gold_18k'].get('p')
                if price:
                    return float(price)
    except:
        pass
    
    try:
        response = requests.get(
            'https://bonbast.com/graph/18k/latest',
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                return float(data['price'])
    except:
        pass
    
    return 5_000_000

def calculate_price(weight, purity, profit_percent, labor_percent, is_new):
    base_price_18k = get_gold_price_18k()
    
    purity_factors = {
        14: 14/18,
        18: 1.0,
        21: 21/18,
        22: 22/18,
        24: 24/18
    }
    
    purity_factor = purity_factors.get(purity, 1.0)
    gram_price = base_price_18k * purity_factor
    
    raw_price = weight * gram_price
    profit = raw_price * (profit_percent / 100)
    labor = raw_price * (labor_percent / 100)
    
    if not is_new:
        labor = labor / 2
    
    final_price = raw_price + profit + labor
    
    return {
        'base_price_18k': base_price_18k,
        'gram_price': gram_price,
        'raw_price': raw_price,
        'profit': profit,
        'labor': labor,
        'final_price': final_price
    }
