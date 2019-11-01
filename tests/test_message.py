from base64 import b64encode
from email.mime.multipart import MIMEMultipart
from emailer.message import Message
from emailer.recipient import Recipient


def test_message_has_email_message():
  assert isinstance(Message().email_message, MIMEMultipart)


def test_message_fields_are_in_email_message():
  sender = Recipient('sender')
  recipient = Recipient('to@example.com')
  replyto = Recipient('replyto@example.com')
  message = Message(subject='Hi',
                    sender=sender,
                    recipient=recipient,
                    replyto=replyto)
  items = message.email_message.items()
  assert ('Subject', 'Hi') in items
  assert ('From', sender.email) in items
  assert ('To', recipient.email) in items
  assert ('Reply-To', replyto.email) in items


def test_message_body_is_email_message_content():
  plain = 'Hi\n'
  html = '<h1>Hi</h1>\n'
  message = Message(html_body=html, plain_body=plain)
  payloads = [m.get_payload() for m in message.email_message.get_payload()]
  # `plain` is not base64 encoded, because 'Hi\n' doesn't include unicode characters.
  expected = [plain, b64encode(html.encode('utf-8')).decode('utf-8') + '\n']
  assert payloads == expected


def test_message_bytes_pass_through_to_email_message_as_bytes():
  message = Message()
  assert bytes(message) == message.email_message.as_bytes()
