from email.message import Message
from email import generator
import email
import io


class Email:
    def __init__(self, data):
        if type(data) == Message:
            # The data is already a Message
            self.email = data
        elif type(data) == io.TextIOWrapper:
            # The data is the path of the file thant contains the message
            self.email = email.message_from_file(data)
        else:
            # We have to convert the data to Message
            self.email = email.message_from_string(data[0][1].decode())

    def sender(self):
        """Returns the sender of the email"""
        return self.email["from"]  # It might return something like "Name Surname <email>" or just the email

    def receiver(self):
        """Returns the receiver of the email"""
        return self.email["to"]

    def subject(self):
        """Returns the subject of the email"""
        return self.email["subject"]

    def content(self):
        """Returns a list with the payload of the email (files attached, text in html, text in plaintext)"""
        if not self.email.is_multipart():
            return self.email.get_payload()  # It only has the text (no files, no html)
        payload = self.email.get_payload()
        return [Email(x) for x in payload]

    def content_type(self):
        """Returns the content type of the email"""
        return self.email["content-type"]

    def message_id(self):
        """Returns the message id of the email"""
        return self.email["message-id"]

    def save(self, path):
        """It saves the email in the path and returns the size of the file"""
        with open(path, "w") as outfile:
            gen = generator.Generator(outfile)
            gen.flatten(self.email)
            size = outfile.tell()
        return size

    def reset_date(self):
        """Deletes the reception date from the email"""
        del self.email["date"]

    def str(self):
        """Return the email in string format"""
        return str(self.email)
