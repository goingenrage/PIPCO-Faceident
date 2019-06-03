from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText


class Mail:

    def __init__(self):
        self.login = "gesichtsreidentifikation"
        self.password = "password123"
        self.provider = "mail.de"


    def send_message(self, subject, content, recipients):
        if not self.login or not self.password:
            return
        text = content
        message = MIMEText(text, 'plain')
        message['Subject'] = subject
        my_email = self.login + '@' + self.provider
        message['To'] = ', '.join("gesichtsreidentifikation@mail.de")
        if recipients:
            try:
                connection = SMTP("smtp." + self.provider, timeout=30)
                connection.set_debuglevel(False)
                connection.login(self.login, self.password)
                try:
                    connection.sendmail(my_email, "gesichtsreidentifikation@mail.de", message.as_string())
                finally:
                    connection.close()
            except Exception as exc:
                print("sending mail failed")
