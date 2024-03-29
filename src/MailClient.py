from smtplib import SMTP_SSL as SMTP
from email.mime.text import MIMEText
from builtins import input
import time
import threading

class MailClient:

    def __init__(self, data):
        self.data = data
        self.login = "gesichtsreidentifikation"
        self.password = "password123"
        self.provider = "mail.de"

    def __send_message(self, subject, content, recipients):
        if not self.login or not self.password:
            return
        text = content
        message = MIMEText(text, 'plain')
        message['Subject'] = subject
        my_email = self.login + '@' + self.provider
        message['To'] = ', '.join(recipients)
        if recipients:
            try:
                connection = SMTP("smtp." + self.provider, timeout=30)
                connection.set_debuglevel(True)
                connection.login(self.login, self.password)
                try:
                    connection.sendmail(my_email, recipients, message.as_string())
                finally:
                    connection.close()
            except Exception as exc:
                print("sending mail failed")

    def notify_motion_detected(self):
        subject = "Bewegung erkannt"
        message = "Haben Sie sich gerade bewegt? Falls nein, werden Sie wahrscheinlich gerade ausgeraubt."
        recipients = [mail.address for mail in self.data.get_mails().values() if mail.notify]
        thread = threading.Thread(target=self.__send_message, args=[subject, message, recipients])
        thread.start()

    def notify_unknown_person_detected(self):
        subject = "Unbekannte Person erkannt!"
        message = "Am " + time.strftime("%d_%m_%Y") + " um " + time.strftime("%H_%M_%S") + " wurde eine unbekannte Person entdeckt!"
        recipients = [mail.address for mail in self.data.get_mails().values() if mail.notify]
        thread = threading.Thread(target=self.__send_message, args=[subject, message, recipients])
        thread.start()

    def notify_storage_full(self):
        subject = "Speicher voll"
        message = "Es können keine weiteren Videos mehr gespeichert werden, da der von Ihnen freigegebene Speicherplatz belegt ist."
        recipients = [mail.address for mail in self.data.get_mails().values() if mail.notify]
        thread = threading.Thread(target=self.__send_message, args=[subject, message, recipients])
        thread.start()
