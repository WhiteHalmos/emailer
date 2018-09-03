import datetime

from emailer import parser
from emailer.recipient import Recipient


def test_parse_emails_replace_empty_string_with_default():
  res = list(parser.parse_emails([
      ['send-date', 'email-context'],
      ['', 'hi'],  # Defaults
      ['2018-01-01', ''],
      ]))
  assert res == [(datetime.date(2018, 1, 1), {
      'send-date': '2018-01-01',
      'email-context': 'hi',
      })]


def test_parse_emails_fills_rest_with_default():
  res = list(parser.parse_emails([
      ['send-date', 'other-data'],
      ['', 'bye'],  # Defaults
      ['2018-01-01'],  # Shortened row
      ]))
  assert res == [(datetime.date(2018, 1, 1), {
      'send-date': '2018-01-01',
      'other-data': 'bye',
      })]


def test_parse_emails_returns_multiple_emails_for_same_date():
  res = list(parser.parse_emails([
      ['send-date'],
      [''],  # Defaults
      ['2018-01-01'],
      ['2018-01-01'],
      ]))
  assert len(res) == 2


def test_parse_emails_with_date_returns_only_that_date():
  res = list(parser.parse_emails_for_date([
      ['send-date'],
      [''],  # Defaults
      ['2018-01-01', ''],
      ['2018-01-02', ''],
      ], datetime.date(2018, 1, 2)))
  assert len(res) == 1
  assert res[0] == {'send-date': '2018-01-02'}


def test_parse_emails_with_date_returns_empty_if_nonexistent():
  res = list(parser.parse_emails_for_date([
      ['send-date'],
      [''],  # Defaults
      ], datetime.date(2018, 1, 2)))
  assert not res


def test_parse_recipients_returns_list_of_recipients_no_default_values():
  res = parser.parse_recipients([
      ['Email'],
      ['daniel@example.com'],
      ])
  for recipient in res:
    assert isinstance(recipient, Recipient)
    assert recipient.groups == ()
    assert recipient.highlights == ()


def test_parse_recipients_case_insensitive_highlights():
  res = list(parser.parse_recipients([
      ['Email', 'Highlight'],
      ['daniel@example.com', 'Hi'],
      ]))
  assert res[0].highlights == ('Hi',)


def test_parse_recipients_skip_empty_highlights():
  res = list(parser.parse_recipients([
      ['Email', 'Highlight'],
      ['daniel@example.com', ''],
      ]))
  assert res[0].highlights == ()


def test_parse_recipients_lower_case_groups():
  res = list(parser.parse_recipients([
      ['Email', 'Active'],
      ['daniel@example.com', 'X'],
      ]))
  assert res[0].groups == ('active',)


def test_parse_recipients_skip_empty_groups():
  res = list(parser.parse_recipients([
      ['Email', 'Active'],
      ['daniel@example.com', ''],
      ]))
  assert res[0].groups == ()


def test_parse_recipients_in_group_skips_those_not_in_group():
  res = list(parser.parse_recipients_in_group([
      ['Email', 'Active'],
      ['daniel@example.com', 'X'],
      ['paul@example.com', ''],
      ], 'active'))
  assert len(res) == 1
  assert res[0].email == 'daniel@example.com'


def test_parse_general_returns_generic_dict():
  res = parser.parse_general([
      ['Name', 'Value'],
      ['reply-to', 'Daniel'],
      ])
  assert res == {'reply-to': 'Daniel'}


def test_parse_general_returns_empty_dict_for_none():
  assert parser.parse_general(None) == {}
