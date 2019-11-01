from . import composer, markdown
from .message import Message
from .name import FROM, REPLY_TO


def create_message_for_recipient(recipient, subject, body, values):
  highlighted_body = markdown.mark_text(body, recipient.highlights, values)
  html_body = markdown.convert(highlighted_body)
  sender = composer.get_recipient(FROM, values)
  replyto = composer.get_recipient(REPLY_TO, values)
  return Message(subject=subject,
                 sender=sender,
                 recipient=recipient,
                 replyto=replyto,
                 html_body=html_body,
                 plain_body=body)
