"""Print layout for immutable finalization snapshots; no HTTP or database access."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from ..database import DATA

def make_pdf(snapshot, booking_id):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as PDFImage
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    pdfmetrics.registerFont(TTFont("Roomform",str(Path(__file__).resolve().parents[1]/"fonts"/"manrope-400.ttf")))
    buf=BytesIO(); styles=getSampleStyleSheet(); story=[]
    for style in styles.byName.values():
        style.fontName='Roomform'
        style.wordWrap='CJK'
    def p(text,style='BodyText'):story.append(Paragraph(escape(str(text)),styles[style]));story.append(Spacer(1,8))
    p('Roomform | Project finalization request','Title');p('DRAFT AGREEMENT / ESTIMATE','Heading2');p('Booking '+booking_id);p('Stock and estimate checked at: '+snapshot.get('stock_checked_at',''))
    for key in ('project_name','design_id','customer_name','customer_email','phone','address','preferred_date'):
        p(key.replace('_',' ').title()+': '+str(snapshot.get(key,'')))
    image=snapshot.get('image_url','')
    if image.startswith('/media/') and Path(image).name==image.removeprefix('/media/'):
        image_path=DATA/'media'/Path(image).name
        if image_path.is_file():
            from PIL import Image
            with Image.open(image_path) as im:
                width,height=im.size
            factor=min(480/width,280/height)
            story.append(PDFImage(str(image_path),width=width*factor,height=height*factor))
    p('Selected products','Heading2')
    for i in snapshot['items']:
        p(i['name'],'Heading3');p('Unique item code: '+i['asset_id']+' | Seller: '+i['seller_id']);p(f"Quantity {i['quantity']} | Unit {snapshot['currency']} {i['unit_price']} | Line total {i['subtotal']} | Stock at booking {i['stock']}")
        p(f"Preparation {i['ready_min_days']}-{i['ready_max_days']} days; delivery {i['delivery_min_days']}-{i['delivery_max_days']} days")
    p('Project summary','Heading2')
    for key in ('budget','items_subtotal','labor','service_charge','total'):p(key.replace('_',' ').title()+': '+snapshot['currency']+' '+str(snapshot[key]))
    p(f"Expected project completion: {snapshot['min_days']}-{snapshot['max_days']} calendar days (including {snapshot['installation_days']} installation days)")
    p(snapshot['timeline_basis']);p('Excluded: '+', '.join(snapshot['exclusions']));p('Agreement terms','Heading2');p(snapshot['terms']);p('Customer requested finalization and consented to share the above details. This is not a signed contract.');p('Customer signature: __________________  Date: __________');p('Roomform representative: ______________  Date: __________')
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=45,leftMargin=45,topMargin=45,bottomMargin=45).build(story)
    return buf.getvalue()

