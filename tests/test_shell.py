import json
import sys

import pytest

from emailer import args, shell, fetcher, api, auth, config as config_module
from emailer.config import Config
from emailer.name import EMAILS, RECIPIENTS
from emailer.options import Options


def test_process(monkeypatch):
  mock_sheet = {'mock_sheet': {}}
  output_sheet_called = False

  def mock_input_source(options, config, creds):
    assert options.group == 'test'
    assert config is not None
    assert creds is None
    return lambda: [mock_sheet]

  def mock_output_sheet(options, config, markdown_outputs, message_outputs,
                        sheet):
    nonlocal output_sheet_called
    output_sheet_called = True
    assert options.group == 'test'
    assert config is not None
    assert markdown_outputs is not None
    assert message_outputs is not None
    assert sheet == mock_sheet

  monkeypatch.setattr(shell, "decide_input_source", mock_input_source)
  monkeypatch.setattr(shell, "output_sheet", mock_output_sheet)
  monkeypatch.setattr(shell, "needs_valid_creds", lambda _: False)
  monkeypatch.setattr(shell, "load_config", lambda _: Config())
  monkeypatch.setattr(shell, "compose_output_gmail_sender",
                      lambda _: lambda _: None)

  opts = Options(args.get_parsed_args(['--test']))
  shell.process(opts)
  assert output_sheet_called


def test_decide_input_from_stdin():
  """Given the --stdin argument, Then the input source should be stdin."""
  options = Options(args.get_parsed_args(['--stdin']))
  config = Config()
  creds = None
  # pylint: disable=comparison-with-callable
  assert shell.decide_input_source(options, config,
                                   creds) == shell.input_sheet_from_stdin


def test_decide_input_from_google(monkeypatch):
  """Given --stdin is not set, Then the input source should be Google Sheets."""

  def mock_sheets_fetcher():
    """fake Google Sheets fetcher"""

  def mock_input_google_sheets(options, config, creds):
    """internal function that generates a google sheets fetcher"""
    assert not options.stdin
    assert config is not None
    assert creds == 'uh... sure'
    return mock_sheets_fetcher

  monkeypatch.setattr(shell, "compose_input_google_sheets",
                      mock_input_google_sheets)

  opts = Options(args.get_parsed_args([]))
  cfg = Config()
  # pylint: disable=comparison-with-callable
  assert shell.decide_input_source(opts, cfg,
                                   'uh... sure') == mock_sheets_fetcher
  mock_sheets_fetcher()  # 100% coverage


def test_google_sheets_fetcher_called_with_ids(monkeypatch):
  monkeypatch.setattr(fetcher, "values",
                      lambda sheet_id, _: 'fetched_' + sheet_id)
  monkeypatch.setattr(api, "sheets", lambda creds: None)

  config = Config(keys={'a': '1', 'b': '2'})
  options = Options(args.get_parsed_args(['--all-keys']))
  sheets_fetcher = shell.compose_input_google_sheets(options=options,
                                                     config=config,
                                                     creds='sup')
  sheets = sheets_fetcher()

  assert set(sheets) == {'fetched_1', 'fetched_2'}


def test_sheet_from_stdin(monkeypatch):
  monkeypatch.setattr(sys.stdin, "read", lambda: '{"json":"data"}')
  subject = shell.input_sheet_from_stdin()
  assert list(subject) == [{"json": "data"}]


def test_decide_markdown_outputs():
  options = Options(args.get_parsed_args(['--stdout-markdown']))
  subject = shell.decide_markdown_outputs(options)
  assert subject == [shell.output_stdout_markdown]


def test_decide_message_outputs(monkeypatch):

  def mock_compose_output_gmail_sender(creds):
    assert creds == 'sup'
    return 'test gmail sender'

  monkeypatch.setattr(shell, "compose_output_gmail_sender",
                      mock_compose_output_gmail_sender)

  options = Options(args.get_parsed_args(['--stdout-email', '--skip-send']))
  outputs = shell.decide_message_outputs(options=options, creds='sup')
  assert len(outputs) == 1, "should have a stdout sender"
  # pylint: disable=comparison-with-callable
  assert outputs[0] == shell.output_stdout_email

  options = Options(args.get_parsed_args(['--stdout-email']))
  outputs = shell.decide_message_outputs(options=options, creds='sup')
  assert len(outputs) == 2, "should have both stdout and gmail senders"
  # pylint: disable=comparison-with-callable
  assert outputs[0] == shell.output_stdout_email
  assert outputs[1] == 'test gmail sender'

  options = Options(args.get_parsed_args([]))
  outputs = shell.decide_message_outputs(options=options, creds='sup')
  assert len(outputs) == 1, "should have a gmail sender"
  assert outputs[0] == 'test gmail sender'

  options = Options(args.get_parsed_args(['--skip-send']))
  outputs = shell.decide_message_outputs(options=options, creds='sup')
  assert len(outputs) == 0, "should have zero senders"


class OutputMock:

  def __init__(self):
    self.sheet = {
        EMAILS: [
            ["email_date", "", "2019-10-17"],
            ["email_subject", "", "test subject"],
            ["email_body", "", "test body\n$test_var"],
            ["test_var", "", "hi"],
        ],
        RECIPIENTS: [
            ["Email", "Active", "Dryrun", "Test"],
            ["test@example.com", "", "", "x"],
        ]
    }
    self.markdown_called, self.message_called = False, False

  def stub_markdown_output(self, markdowns):
    self.markdown_called = True
    assert len(markdowns) == 1, "at least one message should be markdown"
    subject, body, _ = markdowns[0]
    assert subject == 'test subject'
    assert body == 'test body\nhi'

  def stub_message_output(self, messages):
    self.message_called = True
    assert len(messages) == 1, "at least one message should be sent to output"
    message = messages[0]
    assert message.subject == 'test subject'
    assert message.recipient.email == 'test@example.com'


@pytest.fixture
def output_fixture():
  return OutputMock()


def test_output(output_fixture):
  config = Config(keys={'a': 1, 'b': 2})
  options = Options(
      args.get_parsed_args(['-d', '2019-10-17', '--all-keys', '--test']))
  markdown_outputs = [output_fixture.stub_markdown_output]
  message_outputs = [output_fixture.stub_message_output]
  shell.output_sheet(options, config, markdown_outputs, message_outputs,
                     output_fixture.sheet)
  assert output_fixture.markdown_called
  assert output_fixture.message_called


def test_output_no_message_handlers(output_fixture):
  config = Config(keys={'a': 1, 'b': 2})
  options = Options(
      args.get_parsed_args(['-d', '2019-10-17', '--all-keys', '--test']))
  markdown_outputs = [output_fixture.stub_markdown_output]
  message_outputs = []
  shell.output_sheet(options, config, markdown_outputs, message_outputs,
                     output_fixture.sheet)
  assert output_fixture.markdown_called
  assert not output_fixture.message_called


def test_save_sheet(tmpdir):
  out_json = tmpdir.join('out.json')
  out_json.write('')
  shell.save_sheet(out_json.strpath, [{'test': 'data'}])
  assert out_json.read() == '[\n    {\n        "test": "data"\n    }\n]'


def test_get_emails_parses_and_composes():
  sheet = {
      EMAILS: [["email_date", "", "2019-10-17"],
               ["email_subject", "", "test subject"],
               ["email_body", "", "test body\n$test_var"],
               ["test_var", "", "hi"]]
  }
  markdowns = shell.markdown_emails_for_date(sheet=sheet,
                                             send_date='2019-10-17',
                                             group='test',
                                             extra_values={})
  markdowns = list(markdowns)
  assert len(markdowns) == 1, "one markdown should be generated"
  subject, body, values = markdowns[0]
  assert subject == 'test subject'
  assert body == 'test body\nhi'
  assert values.get('email_date') == '2019-10-17'


def test_stdout_markdown(capsys):
  emails = [('test subject', 'test body', {})]

  shell.output_stdout_markdown(emails)

  out, _err = capsys.readouterr()
  j = json.loads(out)
  assert j == [{'body': 'test body', 'subject': 'test subject'}]


def test_stdout_email(capsys, stub):
  messages = [stub(email_message='a'), stub(email_message='b')]

  shell.output_stdout_email(messages)

  out, _err = capsys.readouterr()
  j = json.loads(out)
  assert j == ['a', 'b']


def test_output_gmail(monkeypatch):
  messages = []
  monkeypatch.setattr(api, "gmail", lambda creds: None)
  monkeypatch.setattr(shell, 'GmailSender', lambda _: None)
  monkeypatch.setattr(shell, 'send_messages',
                      lambda ms, s: [messages.append(m) for m in ms])
  sender = shell.compose_output_gmail_sender('sup')
  sender(['a', 'b', 'c'])
  assert messages == ['a', 'b', 'c']


def test_get_messages():
  sheet = {
      EMAILS: [["email_date", "", "2019-10-17"],
               ["email_subject", "", "test subject"],
               ["email_body", "", "test body\n$test_var"],
               ["test_var", "", "hi"]],
      RECIPIENTS: [
          ["Email", "Active", "Dryrun", "Test"],
          ["test@example.com", "", "x", "x"],
      ]
  }
  emails = [('subject', 'body', {})]
  group = 'test'
  cfg = Config(extra_emails={"test": ["Extra Tester <extra@example.com>"]})
  extra_recipients = cfg.get_extra_recipients_for_group('test')

  result = shell.messages_from_markdown(sheet, emails, group, extra_recipients)

  result = list(result)
  assert len(result) == 2
  msg1, msg2 = result

  assert msg1.subject == 'subject'
  assert 'body' in msg1.html_body
  assert msg1.recipient.email == 'test@example.com'

  assert msg2.subject == 'subject'
  assert 'body' in msg2.html_body
  assert msg2.recipient.email == 'Extra Tester <extra@example.com>'


def test_validate_creds(monkeypatch):
  options = Options(args.get_parsed_args(['--all-keys']))
  config = Config()
  monkeypatch.setattr(config_module, 'find_config_file', lambda _: None)
  monkeypatch.setattr(Config, 'validate', lambda _: None)
  monkeypatch.setattr(Config, 'creds', 'sup')
  monkeypatch.setattr(auth, 'serialize', lambda _: 'sup')
  monkeypatch.setattr(Config, 'set_serialized_creds', lambda _self, _: _self)
  monkeypatch.setattr(Config, 'save_to_file', lambda _self, _: None)
  new_config, creds = shell.validate_creds(options, config)
  assert new_config is config
  assert creds == 'sup'


def test_validate_creds_heuristic_for_when_not_used(monkeypatch):
  options = Options(args.get_parsed_args(['--stdin', '--skip-send']))
  config = Config()
  monkeypatch.setattr(shell, 'needs_valid_creds', lambda _: False)
  new_config, creds = shell.validate_creds(options, config)
  assert new_config is config
  assert creds is None


def test_load_config(monkeypatch):
  config = Config()
  monkeypatch.setattr(config_module, 'find_config_file', lambda _: None)
  monkeypatch.setattr(config_module, 'load_from_file', lambda _: config)
  assert shell.load_config('test_dir') is config


def test_needs_valid_creds(stub):
  assert shell.needs_valid_creds(stub(stdin=True, skip_send=True)) is False
  assert shell.needs_valid_creds(stub(stdin=False, skip_send=True)) is True
  assert shell.needs_valid_creds(stub(stdin=True, skip_send=False)) is True
  assert shell.needs_valid_creds(stub(stdin=False, skip_send=False)) is True


def test_gets_all_sheet_ids():
  options = Options(args.get_parsed_args(['--all-keys']))
  config = Config(keys={'a': 1, 'b': 2})
  assert shell.google_sheet_ids(options, config) == {1, 2}


def test_gets_selected_sheet_ids():
  options = Options(args.get_parsed_args(['-k', 'a', 'b']))
  config = Config(keys={'a': '1', 'b': '2', 'c': '3'})
  assert shell.google_sheet_ids(options, config) == {'1', '2'}
