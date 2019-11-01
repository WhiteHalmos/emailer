import json
import logging
import sys

from . import api, auth, composer, fetcher, parser, config as config_module
from .config import Config
from .gmailsender import GmailSender
from .messagebuilder import create_message_for_recipient
from .name import SUBJECT, BODY, EMAILS, RECIPIENTS, PREFIX
from .options import Options
from .send import send_messages


def process(options: Options):
  """Gather input data, format it, and send out email."""
  config = load_config(options.config_dir)
  config, creds = validate_creds(options, config)

  input_source = decide_input_source(options=options,
                                     config=config,
                                     creds=creds)
  markdown_outputs = decide_markdown_outputs(options=options)
  message_outputs = decide_message_outputs(options=options, creds=creds)

  for sheet in input_source():
    save_sheet(save_sheet_to=options.save_sheet_to, sheet=sheet)
    output_sheet(options=options,
                 config=config,
                 markdown_outputs=markdown_outputs,
                 message_outputs=message_outputs,
                 sheet=sheet)
  return 0


def decide_input_source(options: Options, config: Config, creds):
  """:return: a function that returns sheets"""
  if options.stdin:
    return input_sheet_from_stdin
  return compose_input_google_sheets(options=options,
                                     config=config,
                                     creds=creds)


def decide_markdown_outputs(options: Options):
  """:return: a list of functions that output markdown"""
  markdown_senders = []
  if options.stdout_markdown:
    markdown_senders.append(output_stdout_markdown)
  return markdown_senders


def decide_message_outputs(options: Options, creds):
  """:return: a list of functions that output email messages"""
  message_senders = []
  if options.stdout_email:
    message_senders.append(output_stdout_email)
  if not options.skip_send:
    message_senders.append(compose_output_gmail_sender(creds))
  return message_senders


def save_sheet(save_sheet_to: str, sheet):
  """
  If the filename is set, then it will save the sheet to the location.
  :param save_sheet_to: filename location where the sheet will be dumped
   as JSON
  :param sheet: data to be dumped into the file
  """
  if save_sheet_to:
    with open(save_sheet_to, 'w+') as stream:
      json.dump(sheet, stream, indent=4)


def output_sheet(options: Options, config: Config, markdown_outputs: list,
                 message_outputs: list, sheet):
  """send the sheet to the output functions"""
  extra_values = config.get_extra_values()
  markdowns = list(
      markdown_emails_for_date(sheet=sheet,
                               send_date=options.send_date,
                               group=options.group,
                               extra_values=extra_values))
  for send_output in markdown_outputs:
    send_output(markdowns)

  if len(message_outputs) == 0:
    # won't send any messages so don't need to generate them
    return

  extra_recipients = config.get_extra_recipients_for_group(options.group)
  messages = list(
      messages_from_markdown(sheet, markdowns, options.group, extra_recipients))

  for send_output in message_outputs:
    send_output(messages)


def markdown_emails_for_date(sheet, send_date, group, extra_values):
  """Yields composed markdown emails for the given date."""
  emails = parser.parse_emails_for_date(sheet.get(EMAILS), send_date)
  prefix = composer.get_prefix_for_group(group)
  for email in emails:
    values = composer.replace_values({PREFIX: prefix, **email, **extra_values})
    body = composer.substitute_for_key(BODY, values)
    subject = composer.substitute_for_key(SUBJECT, values)
    logging.info(subject)
    logging.info(body)
    yield (subject, body, values)


def messages_from_markdown(sheet, markdowns, group, extra_recipients):
  """Yields messages formatted for each recipient."""
  recipients = parser.parse_recipients_in_group(sheet.get(RECIPIENTS), group)
  all_recipients = [*recipients, *extra_recipients]
  for (subject, body, values) in markdowns:
    for recipient in all_recipients:
      if recipient.is_valid():
        yield create_message_for_recipient(recipient, subject, body, values)


def compose_input_google_sheets(options: Options, config: Config, creds):
  """
  Returns a function `()->Generator(sheet)` to get spreadsheets from Google.
  """

  def get_google_sheets():
    sheet_ids = google_sheet_ids(options, config)
    for sheet_id in sheet_ids:
      yield fetcher.values(sheet_id, api.sheets(creds))

  return get_google_sheets


def input_sheet_from_stdin():
  """Yields the full contents of a sheet supplied via stdin piping."""
  data = sys.stdin.read()
  yield json.loads(data)


def output_stdout_markdown(markdowns):
  """Prints the markdown version of the email to the console in JSON."""
  data = [{
      'subject': subject,
      'body': body
  } for (subject, body, _) in markdowns]
  print(json.dumps(data, indent=4))


def compose_output_gmail_sender(creds):
  """Returns a function (messages)->Null to send each message via Gmail."""
  sender = GmailSender(api.gmail(creds))

  def output_gmail_sender(messages):
    send_messages(messages, sender)

  return output_gmail_sender


def output_stdout_email(messages):
  """Prints rendered emails for each recipient to the console in JSON."""
  data = [str(message.email_message) for message in messages]
  print(json.dumps(data, indent=4))


def load_config(config_dir):
  """Opens the config file, doesn't check for creds."""
  config_path = config_module.find_config_file(config_dir)
  config = config_module.load_from_file(config_path)
  return config


def needs_valid_creds(options: Options) -> bool:
  return not (options.stdin and options.skip_send)


def validate_creds(options: Options, config: Config):
  """
  Creates new creds or uses serialized creds.
  :return: (config, creds)
  """
  if not needs_valid_creds(options):
    return config, None  # not using creds, no need to refresh token
  config_path = config_module.find_config_file(options.config_dir)
  config.validate()
  # Accessing creds either creates new creds or uses serialized creds.
  creds = config.creds
  config = config.set_serialized_creds(auth.serialize(creds))
  config.save_to_file(config_path)
  return config, creds


def google_sheet_ids(options: Options, config: Config):
  """Returns a set of google sheet ids from config and options"""
  if options.all_keys:
    return config.get_all_keys()
  return config.get_keys(options.key_names)
