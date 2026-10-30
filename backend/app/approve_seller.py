"""Operator-only command in the backend host; no public approval endpoint."""
import argparse
from .database import Session
from .models import Seller
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('seller_id');p.add_argument('--disable',action='store_true');args=p.parse_args()
    with Session() as db:
        seller=db.get(Seller,args.seller_id)
        if not seller: raise SystemExit('Seller not found')
        seller.active=not args.disable;db.commit()
        print('Seller disabled' if args.disable else 'Seller approved')
