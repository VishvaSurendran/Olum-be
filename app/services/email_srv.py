import smtplib
from email.mime.text import MIMEText
import os
from app.core.config import SMTP_EMAIL, SMTP_PASSWORD

def send_otp_email(recipient_email: str, otp_code: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("WARNING: Email credentials not set. Printing OTP to terminal instead.")
        print(f"--- OTP FOR {recipient_email}: {otp_code} ---")
        return

    subject = "Your AI SaaS Verification Code"
    body = f"Hello,\n\nYour login/signup verification code is: {otp_code}\n\nThis code will expire in 10 minutes.\n\nThanks,\nAI Support Team"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"AI SaaS <{SMTP_EMAIL}>"
    msg['To'] = recipient_email

    try:
        # Connect to Gmail's SMTP server (change host/port if using Outlook/SendGrid)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, recipient_email, msg.as_string())
        server.quit()
        print(f"OTP sent successfully to {recipient_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e
    

def send_unanswered_question_email(admin_email: str, question: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print(f"WARNING: Email credentials not set. Alert for {admin_email} about question: {question}")
        return

    subject = "Action Required: Your AI Bot needs help"
    body = f"""Hello,

A visitor on your website just asked your AI agent a question it couldn't answer:

"{question}"

Please log in to your Admin Dashboard to teach the bot the correct answer so it can handle this automatically next time!

Thanks,
olum.ai Support Team
"""
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = f"olum.ai Alerts <{SMTP_EMAIL}>"
    msg['To'] = admin_email

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, admin_email, msg.as_string())
        server.quit()
        print(f"Alert email successfully sent to {admin_email}")
    except Exception as e:
        print(f"Failed to send alert email: {e}")