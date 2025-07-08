from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string

load_dotenv()
EMAIL = os.getenv("Email")
PASSWORD = os.getenv("App_Password")

def send_email_CodeFolio(name,email,subject, message):
    
    # Email configuration
    sender_email = EMAIL
    receiver_email = EMAIL
    password = PASSWORD
    
   
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = "Request from contact form:"+subject 
    body=f"""
        Username: { name }
        Email: { email }
        Message: { message }
            The team is requested to resolve this query  as soon as possible.
            Please do not reply to this email. This is an automated message.
"""    
    # Attach the message body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.set_debuglevel(0)
            server.starttls()
            server.login(EMAIL,password)
            server.send_message(msg)
            return True
    except Exception as e:
        #print(f"Error sending email: {e}")
        return False

def send_email_User(name,user_email,subject):
    
    # Email configuration
    sender_email = EMAIL
    receiver_email = user_email
    password = PASSWORD

    # Create the email content
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = " Received your query regarding:"+subject

    body=f"""
        Dear { name },

            Thank you for reaching out to us. We have received your query regarding { subject }.
        We will get back to you as soon as possible.
        If you have any further questions, please feel free to reach out to us at { sender_email }. 
        
        Best regards,
        CodeFolio Team  
        CodeFolio
"""    
    # Attach the message body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            return True
    except Exception as e:
        return False    
    

def send_email_OTP(name,user_email,subject):
    # Email configuration
    sender_email = EMAIL
    receiver_email = user_email
    password = PASSWORD
    otp= generate_otp()
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    body=f"""
        Dear { name },
            { subject }: { otp }.
        This OTP is valid for 5 minutes.
        Please do not share this OTP with anyone.
        If you did not request this OTP, please ignore this email.

        If you have any further questions, please feel free to reach out to us at { sender_email }. 
            
        Best regards,
        CodeFolio Team  
        CodeFolio
"""    
    # Attach the message body
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            return True, otp
    except Exception as e:
        return False, None   
    
def generate_otp():    
    """Generate a 6-digit OTP."""
    digits = string.digits
    otp = ''.join(random.choice(digits) for _ in range(6))
    return otp