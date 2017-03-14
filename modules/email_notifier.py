
#file email_notifier.py
import smtplib


class Email_notifier(object):
    """Parameters: mail_server_address - address of mail server for sending the email
                    error_type - string containing text used in email subject line
    """
    def __init__(self,mail_server_address,error_type = 'test error'):
        self._mail_server_address = mail_server_address
        self._error_type = error_type

    def send_message(self,receivers,message = "Test System Error"):
        """sends an email notification to the list of receivers

            Parameters: receivers - list containing email addresses to receive the message
                        message - string containing email body message
        """
        sender = 'test_system@cameronhealth.com'
        receivers_string = ""
        for person in receivers:
            receivers_string = receivers_string + person
        email = "From: " + sender + "\nTo: " + receivers_string + "\nSubject: " + self._error_type +\
        "\n\n" + message + "\n"

        smtpObj = smtplib.SMTP(self._mail_server_address)
        smtpObj.sendmail(sender,receivers,email)
        smtpObj.quit()

