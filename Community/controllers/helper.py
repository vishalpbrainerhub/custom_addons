import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import random

load_dotenv()

def send_registration_credentials(username, password, to_email):
    # Email account credentials
    gmail_user = os.getenv('SMTP_EMAIL')
    gmail_password = os.getenv('SMTP_PASSWORD')

    subject = "Welcome to Our Service - Account Created"
    body = f"""\
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Account Creation Confirmation</title>
        <style>
          body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
            color: #333;
          }}

          .container {{
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
          }}

          .header {{
            background: linear-gradient(135deg, #000000, #333333);
            color: #ffffff;
            padding: 30px;
            text-align: center;
          }}

          .header h1 {{
            margin: 0;
            font-size: 28px;
          }}

          .content {{
            padding: 20px;
            line-height: 1.8;
            border-top: 5px solid #000000;
          }}

          .content p {{
            margin: 0 0 15px;
          }}

          .content_header {{
            margin-bottom: 2rem;
          }}

          .content_header>p {{
            text-align: center;
          }}

          .content_credentials {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            border-left: 4px solid black;
            border-radius: 4px;
          }}

          .content_credentials>div {{
            width: 90%;
            margin: auto;
            min-width: 360px;
          }}

          .content b {{
            color: #000000;
          }}

          .footer {{
            background-color: #f4f4f4;
            text-align: center;
            padding: 15px;
            font-size: 0.9em;
            color: #555;
            border-top: 1px solid #dddddd;
          }}

          .footer p {{
            margin: 0;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Welcome to Our PrimaPaint Platform!</h1>
          </div>
          <div class="content">
            <div class="content_header">
              <h4>Your account has been created successfully. Here are your initial login credentials:</h4>
            </div>
            <div class="content_credentials">
              <div>
                <p>
                  <b>Username:</b> {username}
                </p>
                <p>
                  <b>Password:</b> {password}
                </p>
              </div>
            </div>
           
            <p>If you have any questions, feel free to contact our support team.</p>
            <p>
              <b>Note:</b> Please do not share your login details with anyone.
            </p>
          </div>
          <div class="footer">
            <p>Thank you for choosing us!</p>
          </div>
        </div>
      </body>
    </html>
    """

    # Create the container email message.
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Create server object with SSL option
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.quit()
        print("Registration email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")


def generate_password(email):
    characters = ["!", "@", "#", "$", "%", "&", "*"]
    test = email.split('@')[0].capitalize()
    password = test + characters[random.randint(0, 6)] + str(random.randint(111, 458962))

    return password


def forgot_password(email, password, to_email):
    gmail_user = os.getenv('SMTP_EMAIL')
    gmail_password = os.getenv('SMTP_PASSWORD')

    subject = "Welcome to Our Platform - Password Reset"

    body = f"""\
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset</title>
        <style>
          body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f0f0f0;
            color: #333;
          }}

          .container {{
            width: 100%;
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
          }}

          .header {{
            background: linear-gradient(135deg, #000000, #333333);
            color: #ffffff;
            padding: 30px;
            text-align: center;
          }}

          .header h1 {{
            margin: 0;
            font-size: 28px;
          }}

          .content {{
            padding: 20px;
            line-height: 1.8;
            border-top: 5px solid #000000;
          }}

          .content p {{
            margin: 0 0 15px;
          }}

          .content_header {{
            margin-bottom: 2rem;
          }}

          .content_header>p {{
            text-align: center;
          }}

          .content_credentials {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            border-left: 4px solid black;
            border-radius: 4px;
          }}

          .content_credentials>div {{
            width: 90%;
            margin: auto;
            min-width: 360px;
          }}

          .content b {{
            color: #000000;
          }}

          .footer {{
            background-color: #f4f4f4;
            text-align: center;
            padding: 15px;
            font-size: 0.9em;
            color: #555;
            border-top: 1px solid #dddddd;
          }}

          .footer p {{
            margin: 0;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>Password Reset</h1>
          </div>
          <div class="content">
            <div class="content_header">
              <h4>Your password has been reset successfully. Here are your new login credentials:</h4>
            </div>
            <div class="content_credentials">
              <div>
                <p>
                  <b>Username:</b> {email}
                </p>
                <p>
                  <b>Password:</b> {password}
                </p>
              </div>
            </div>
           
            <p>If you have any questions, feel free to contact our support team.</p>
            <p>
              <b>Note:</b> Please do not share your login details with anyone.
            </p>
          </div>
          <div class="footer">
            <p>Thank you for choosing us!</p>
          </div>
        </div>
        </body>
    </html>
    """

    # Create the container email message.
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        # Create server object with SSL option
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.quit()

        print("Password reset email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    
    return True
