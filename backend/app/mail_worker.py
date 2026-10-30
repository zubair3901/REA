"""Run regularly: python -m app.mail_worker. Never logs mail bodies or reset links."""
import os,smtplib,ssl
from email.message import EmailMessage
from sqlalchemy import select
from .database import Session
from .workspace_models import MailQueue

def run():
    if not all(os.getenv(k) for k in ('SMTP_HOST','SMTP_FROM')):raise SystemExit('Configure SMTP_HOST and SMTP_FROM first')
    with Session() as db:
        rows=db.scalars(select(MailQueue).where(MailQueue.status=='pending',MailQueue.attempts<5).with_for_update(skip_locked=True).limit(20)).all()
        for row in rows:
            row.attempts+=1
            message=EmailMessage();message['From']=os.environ['SMTP_FROM'];message['To']=row.recipient;message['Subject']=row.subject;message.set_content(row.body)
            try:
                with smtplib.SMTP(os.environ['SMTP_HOST'],int(os.getenv('SMTP_PORT','587')),timeout=20) as smtp:
                    smtp.starttls(context=ssl.create_default_context())
                    if os.getenv('SMTP_USER'):smtp.login(os.environ['SMTP_USER'],os.environ.get('SMTP_PASSWORD',''))
                    smtp.send_message(message)
                row.status='sent';row.body=''
            except (OSError,smtplib.SMTPException):
                if row.attempts>=5:row.status='failed';row.body=''
        db.commit()
if __name__=='__main__':run()
