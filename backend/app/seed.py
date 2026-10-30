"""Opt-in illustrative catalog. These are NOT real vendor listings."""
from PIL import Image, ImageDraw
from .database import Base,engine,Session
from .models import Seller,Asset
from .main import MEDIA

def seed():
    Base.metadata.create_all(engine)
    products=[('sofa','Arc lounge sofa','Sofa','Organic',890,210,80,90,4,'#b5a38a'),('lamp','Halo floor lamp','Lighting','Minimal',145,45,165,45,2,'#e0bb70'),('chair','Sculpt accent chair','Chair','Organic',320,78,85,80,3,'#8b987c'),('table','Orbit side table','Table','Minimal',180,65,45,65,2,'#a17455')]
    with Session() as db:
        if not db.get(Seller,'demo'): db.add(Seller(id='demo',name='Demo Studio — illustrative inventory'));db.flush()
        for ident,name,category,style,price,w,h,d,days,color in products:
            path=MEDIA/f'demo_{ident}.png'
            im=Image.new('RGBA',(600,600));draw=ImageDraw.Draw(im)
            if ident=='sofa':
                draw.rounded_rectangle((50,220,550,460),radius=45,fill=color);draw.rounded_rectangle((90,180,510,360),radius=45,fill=color);draw.line((300,210,300,420),fill='#756957',width=4)
                draw.rectangle((100,460,120,500),fill='#55483e');draw.rectangle((480,460,500,500),fill='#55483e')
            elif ident=='lamp':
                draw.ellipse((180,490,420,525),fill='#343332');draw.rectangle((290,175,305,500),fill=color);draw.polygon([(200,100),(400,100),(455,240),(145,240)],fill=color)
            elif ident=='chair':
                draw.rounded_rectangle((155,140,440,430),radius=70,fill=color);draw.rounded_rectangle((110,325,475,450),radius=30,fill=color);draw.rectangle((155,445,175,520),fill='#524437');draw.rectangle((410,445,430,520),fill='#524437')
            else:
                draw.rectangle((195,240,220,510),fill=color);draw.rectangle((385,240,410,510),fill=color);draw.ellipse((100,160,500,300),fill=color)
            im.save(path)
            if not db.get(Asset,ident): db.add(Asset(id=ident,seller_id='demo',name=name,category=category,style=style,price=price,currency='USD',width_cm=w,height_cm=h,depth_cm=d,image_url=f'/media/{path.name}',latitude=24.8607,longitude=67.0011,stock=10,delivery_days=days))
        db.commit()
if __name__=='__main__': seed()
