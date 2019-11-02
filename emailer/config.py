import dataclasses
import json
import os.path
from typing import Optional

from .recipient import Recipient
from .auth import create_or_deserialize_creds

CONFIG_FILES = ['.emailer.json', 'emailer.json']


class InvalidFileError(Exception):
  pass


@dataclasses.dataclass(frozen=True)
class Config():
  client_secret: Optional[dict] = None
  serialized_creds: Optional[dict] = None
  keys: Optional[dict] = None
  extra_emails: Optional[dict] = None
  extra_values: Optional[dict] = None

  @property
  def creds(self):
    return create_or_deserialize_creds(self.serialized_creds,
                                       self.client_secret)

  def validate(self):
    if self.client_secret is None:
      raise InvalidFileError(
          'Unable to locate client_secret key in config: '
          'https://developers.google.com/identity/protocols/OAuth2')

  def get_extra_recipients_for_group(self, group):
    if self.extra_emails is None:
      return []
    return [Recipient(email) for email in self.extra_emails.get(group, [])]

  def get_extra_values(self):
    if self.extra_values is None:
      return {}
    return self.extra_values

  def get_all_keys(self):
    if self.keys is None:
      return set()
    return self.get_keys(self.keys.keys())

  def get_keys(self, names):
    if self.keys is None:
      return set()
    return {self.keys.get(name) for name in names}

  def set_serialized_creds(self, serialized_creds):
    return dataclasses.replace(self, serialized_creds=serialized_creds)

  def save_to_file(self, config_path):
    with open(config_path, 'w') as config_file:
      json.dump(dataclasses.asdict(self), config_file, indent=2, sort_keys=True)


def files(root_path):
  for config_file in CONFIG_FILES:
    root = root_path
    while True:
      dirname = os.path.dirname(root)
      yield os.path.join(root, config_file)
      if root == dirname:
        break
      root = dirname
    yield os.path.join(os.path.expanduser('~'), config_file)


def find_config_file(root):
  for path in files(root):
    if os.path.exists(path):
      return path
  return None


def load_from_file(config_path):
  if not config_path or not os.path.exists(config_path):
    raise InvalidFileError(config_path)
  with open(config_path, 'r') as config_file:
    try:
      return Config(**json.load(config_file))
    except json.JSONDecodeError:
      raise InvalidFileError(f'{config_path} must be a valid JSON file.')
