# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import os
import sys
import stat
from six.moves import configparser

from .util import ensure_dir

_CONFIG_FILE_NAME = 'config'
_UNSET = object()


def get_config_parser():
    return configparser.ConfigParser() if sys.version_info.major == 3 else configparser.SafeConfigParser()


class CLIConfig(object):
    _BOOLEAN_STATES = {'1': True, 'yes': True, 'true': True, 'on': True,
                       '0': False, 'no': False, 'false': False, 'off': False}

    def __init__(self, config_dir_name, config_env_var_name):
        config_env_var_name = config_env_var_name or config_dir_name
        self.config_parser = get_config_parser()
        env_var_prefix = '{}_'.format(config_env_var_name.upper())
        # TODO The default config dir should be configurable instead of using config_dir_name
        default_config_dir = os.path.expanduser(os.path.join('~', '.{}'.format(config_dir_name.lower())))
        self.config_dir = os.environ.get('{}CONFIG_DIR'.format(env_var_prefix), default_config_dir)
        self.config_path = os.path.join(self.config_dir, _CONFIG_FILE_NAME)
        self._env_var_format = env_var_prefix + '{section}_{option}'
        self.config_parser.read(self.config_path)

    def env_var_name(self, section, option):
        return self._env_var_format.format(section=section.upper(),
                                           option=option.upper())

    def has_option(self, section, option):
        if self.env_var_name(section, option) in os.environ:
            return True
        return self.config_parser.has_option(section, option)

    def get(self, section, option, fallback=_UNSET):
        try:
            env = self.env_var_name(section, option)
            return os.environ[env] if env in os.environ else self.config_parser.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is _UNSET:
                raise
            else:
                return fallback

    def getint(self, section, option, fallback=_UNSET):
        return int(self.get(section, option, fallback))

    def getfloat(self, section, option, fallback=_UNSET):
        return float(self.get(section, option, fallback))

    def getboolean(self, section, option, fallback=_UNSET):
        val = str(self.get(section, option, fallback))
        if val.lower() not in CLIConfig._BOOLEAN_STATES:
            raise ValueError('Not a boolean: {}'.format(val))
        return CLIConfig._BOOLEAN_STATES[val.lower()]

    def set(self, config):
        ensure_dir(self.config_dir)
        with open(self.config_path, 'w') as configfile:
            config.write(configfile)
        os.chmod(self.config_path, stat.S_IRUSR | stat.S_IWUSR)
        # reload config
        self.config_parser.read(self.config_path)

    def set_value(self, section, option, value):
        config = get_config_parser()
        config.read(self.config_path)
        try:
            config.add_section(section)
        except configparser.DuplicateSectionError:
            pass
        config.set(section, option, value)
        self.set(config)
