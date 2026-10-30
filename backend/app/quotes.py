from decimal import Decimal, ROUND_HALF_UP
from math import ceil

def money(v): return float(Decimal(v).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
def quote(assets, area, category):
    currencies = {a.currency for a in assets}
    if len(currencies) != 1: raise ValueError('Select items priced in the same currency')
    # Explicit configurable baseline, NOT a contractor quote.
    import os, json
    rates = json.loads((os.getenv('LABOR_RATES_JSON') or '{"USD": {"living": 8, "bedroom": 7, "office": 6}}'))
    currency = next(iter(currencies))
    rate = rates.get(currency,{}).get(category)
    if rate is None: raise ValueError('No labor rate configured for this currency and room category')
    items = [{'asset_id':a.id,'seller_id':a.seller_id,'name':a.name,'quantity':1,'unit_price':float(a.price),'subtotal':float(a.price)} for a in assets]
    subtotal = sum((a.price for a in assets), Decimal(0))
    labor = Decimal(str(rate)) * Decimal(str(area))
    setup_days = max(1,ceil(area / 20))
    return {'items':items,'currency':currency,'items_subtotal':money(subtotal),'labor':money(labor),'total':money(subtotal+labor),'timeline_days':max(a.delivery_days for a in assets)+setup_days,'installation_days':setup_days,'labor_rate_per_m2':rate,'estimate_only':True,'exclusions':['Taxes','Shipping fees','Structural work'],'inventory_reserved':False}
