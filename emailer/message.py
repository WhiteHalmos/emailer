import dataclasses
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from .recipient import Recipient


@dataclasses.dataclass(frozen=True)
class Message():
  subject: str = ''
  sender: Optional[Recipient] = None
  recipient: Optional[Recipient] = None
  replyto: Optional[Recipient] = None
  plain_body: str = ''
  html_body: str = ''

  @property
  def email_message(self):
    message = MIMEMultipart('alternative')
    message['Subject'] = self.subject
    if self.sender:
      message['From'] = self.sender.email
    if self.recipient:
      message['To'] = self.recipient.email
    if self.replyto:
      message['Reply-To'] = self.replyto.email

    # setting boundary so that it's deterministic for tests
    message.set_boundary('--=== multiple formats ===--')

    # the plain version is for non-html readers
    plain = MIMEText(self.plain_body, 'plain')
    plain.set_boundary('--=== plain message ===---')
    message.attach(plain)

    # html is the formatted version
    html = MIMEText(self.html_body, 'html', 'utf-8')
    html.set_boundary('--=== html formatted message ===--')
    message.attach(html)
    return message

  def __bytes__(self):
    return bytes(self.email_message)
