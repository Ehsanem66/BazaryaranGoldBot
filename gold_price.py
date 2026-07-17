import requests

def get_gold_price_18k():
    """دریافت قیمت لحظه‌ای طلا ۱۸ عیار"""
    try:
        # API جایگزین سازگار با PythonAnywhere
        response = requests.get(
            'https://bonbast.com/graph/18k/latest',
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'price' in data:
                return float(data['price'])
    except:
        pass
    
    try:
        # API دوم
        response = requests.get(
            'https://api.exchangerate.host/latest?base=USD&symbols=IRR'
        )
        
        if response.status_code == 200:
            data = response.json()
            usd_to_irr = data['rates']['IRR']
            gold_per_gram = (2500 * usd_to_irr) / 31.1035
            return gold_per_gram
    except:
        pass
    
    # قیمت پیش‌فرض
    return 3_500_000

def calculate_price(weight, purity, profit_percent, labor_percent, is_new):
    """محاسبه قیمت نهایی طلا"""
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
