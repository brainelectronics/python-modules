#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Module helper

Collection of helper functions used in other modules
"""

import argparse
from datetime import datetime
import json
import logging
from pathlib import Path
import random
import string
import sys
import time
from typing import List
import yaml


class ModuleHelperError(Exception):
    """Base class for exceptions in this module."""
    pass


class ModuleHelper(object):
    """docstring for ModuleHelper"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(ModuleHelper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

    @staticmethod
    def create_logger(logger_name: str = None) -> logging.Logger:
        """
        Create a logger.

        :param      logger_name:  The logger name
        :type       logger_name:  str, optional

        :returns:   Configured logger
        :rtype:     logging.Logger
        """
        custom_format = '[%(asctime)s] [%(levelname)-8s] [%(filename)-15s @'\
                        ' %(funcName)-15s:%(lineno)4s] %(message)s'

        # configure logging
        logging.basicConfig(level=logging.INFO,
                            format=custom_format,
                            stream=sys.stdout)

        if logger_name and (isinstance(logger_name, str)):
            logger = logging.getLogger(logger_name)
        else:
            logger = logging.getLogger(__name__)

        # set the logger level to DEBUG if specified differently
        logger.setLevel(logging.DEBUG)

        return logger

    @staticmethod
    def set_logger_verbose_level(logger: logging.Logger,
                                 verbose_level: int,
                                 debug_output: bool) -> None:
        """
        Set the logger verbose level and debug output

        :param      logger:         The logger to apply the settings to
        :type       logger:         logging.Logger
        :param      verbose_level:  The verbose level
        :type       verbose_level:  int
        :param      debug_output:   The debug mode
        :type       debug_output:   bool
        """
        LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        LOG_LEVELS = LOG_LEVELS[::-1]

        if verbose_level is None:
            if not debug_output:
                # disable the logger
                logger.disabled = True
        else:
            log_level = min(len(LOG_LEVELS) - 1, max(verbose_level, 0))
            log_level_name = LOG_LEVELS[log_level]

            # set the level of the logger
            logger.setLevel(log_level_name)

    def get_option_values(self, options: List[dict], option: str) -> List[str]:
        """
        Get the option values.

        :param      options:  The options
        :type       options:  list
        :param      option:   The option
        :type       option:   str

        :returns:   The option values.
        :rtype:     list
        """
        result = list()

        for ele in options:
            if option not in ele:
                result.append(option)
            else:
                raise ModuleHelperError('{} is not a valid option of {}'.
                                        format(option, options))

        return result

    @staticmethod
    def check_option_values(options: List[str],
                            option: str,
                            raise_error: bool = False) -> bool:
        """
        Check whether a option is a valid option by list comparison

        :param      options:        Available options
        :type       options:        list
        :param      option:         The individual option
        :type       option:         str
        :param      raise_error:    Flag to raise error if option is unknown
        :type       raise_error:    bool

        :returns:   True is the option is valid, False otherwise
        :rtype:     bool
        """
        result = False

        if option in options:
            result = True
        else:
            if raise_error:
                raise ValueError('{} is no valid option of {}'.format(option,
                                                                      options))

        return result

    @staticmethod
    def format_timestamp(timestamp: int, format: str) -> str:
        """
        Get timestamp as string in specified format

        :param      timestamp:  The timestamp
        :type       timestamp:  int
        :param      format:     The format
        :type       format:     str

        :returns:   Formatted timestamp
        :rtype:     str
        """
        return datetime.fromtimestamp(timestamp).strftime(format)

    @staticmethod
    def get_unix_timestamp() -> int:
        """
        Get the unix timestamp.

        :returns:   The unix timestamp.
        :rtype:     int
        """
        return (int(time.time()))

    @staticmethod
    def get_random_string(length: int) -> str:
        """
        Get a random string with characters and numbers.

        :param      length:  The length of the string to generate
        :type       length:  int

        :returns:   The random string.
        :rtype:     str
        """
        return ''.join(random.choices(string.ascii_uppercase + string.digits,
                                      k=length))

    @staticmethod
    def convert_string_to_uint16t(content: str) -> list:
        """
        Convert string to list of uint16_t values

        :param      content:  The string content to convert
        :type       content:  str

        :returns:   Unicode converted list of uint16_t numbers
        :rtype:     list
        """
        # convert all characters to their unicode code, 'A' -> 65 ...
        unicode_list = [ord(x) for x in content]
        # self.logger.debug('Content as unicode: {}'.format(unicode_list))

        # iter the list and create tuples
        # represented by 8 bit, two unicode chars can be represented by 16 bit
        it = iter(unicode_list)
        tuple_list = zip(it, it)

        # create a 16 bit number of two unicode numbers
        number_list = list()
        for ele in tuple_list:
            number_list.append((ele[0] << 8) | ele[1])

        # self.logger.debug('Content as numbers: {}'.format(number_list))

        return number_list

    @staticmethod
    def sort_by_name(a_list: list, descending: bool = False) -> bool:
        """
        Sort list by name.

        Given list is sorted, no copy is made.

        :param      a_list:      The list to sort
        :type       a_list:      list
        :param      descending:  Flag for descending sort order
        :type       descending:  bool

        :returns:   True if the list has been sorted, False otherwise
        :rtype:     boolean
        """
        result = False

        if isinstance(a_list, list):
            a_list.sort(reverse=descending)
            result = True
        else:
            result = False

        return result

    @staticmethod
    def is_json(content: dict) -> bool:
        """
        Determine whether the specified content is json.

        :param      content:  The content to check
        :type       content:  dict

        :returns:   True if the specified content is json, False otherwise.
        :rtype:     boolean
        """
        try:
            if not isinstance(content, dict):
                # dicts are by default valid json
                json.loads(content)
        except ValueError:
            return False
        except TypeError:
            # the JSON object must be str, bytes or bytearray
            return False

        return True

    @staticmethod
    def parser_valid_file(parser: argparse.ArgumentParser, arg: str) -> str:
        """
        Determine whether file exists.

        :param      parser:                 The parser
        :type       parser:                 parser object
        :param      arg:                    The file to check
        :type       arg:                    str
        :raise      argparse.ArgumentError: Argument is not a file

        :returns:   Input file path, parser error is thrown otherwise.
        :rtype:     str
        """
        if not Path(arg).is_file():
            parser.error("The file {} does not exist!".format(arg))
        else:
            return arg

    @staticmethod
    def parser_valid_dir(parser: argparse.ArgumentParser, arg: str) -> str:
        """
        Determine whether directory exists.

        :param      parser:                 The parser
        :type       parser:                 parser object
        :param      arg:                    The directory to check
        :type       arg:                    str
        :raise      argparse.ArgumentError: Argument is not a directory

        :returns:   Input directory path, parser error is thrown otherwise.
        :rtype:     str
        """
        if not Path(arg).is_dir():
            parser.error("The directory {} does not exist!".format(arg))
        else:
            return arg

    @staticmethod
    def check_file(file_path: str, suffix: str) -> bool:
        """
        Check existance and type of file

        :param      file_path:  The path to file
        :type       file_path:  string
        :param      suffix:     Suffix of file
        :type       suffix:     string

        :returns:   Result of file check
        :rtype:     boolean
        """
        result = False
        file_path = Path(file_path)

        if file_path.is_file():
            if file_path.suffix == suffix:
                result = True

        return result

    @staticmethod
    def check_folder(folder_path: str) -> bool:
        """
        Check existance of folder

        :param      folder_path:  The path to the folder
        :type       folder_path:  string

        :returns:   Result of folder check
        :rtype:     boolean
        """
        result = False

        if Path(folder_path).is_dir():
            result = True

        return result

    @staticmethod
    def get_current_path() -> Path:
        """
        Get the full path to this file.

        :returns:   The path of this file
        :rtype:     Path object
        """
        return ModuleHelper.get_full_path(base=__file__)

    @staticmethod
    def get_full_path(base: str) -> Path:
        """
        Return full path to parent of path

        :param      base:  The base
        :type       base:  str

        :returns:   The full path.
        :rtype:     Path
        """
        return Path(base).parent.resolve()

    def save_yaml_file(self, path: str, content: dict) -> bool:
        """
        Save content as an YAML file.

        :param      path:        The path to save the file to
        :type       path:        str
        :param      content:     The content to save
        :type       content:     dict

        :returns:   True if the content has been saved, False otherwise.
        :rtype:     bool

        :raises     Exception:   Exception is thrown on error
        """
        result = False

        try:
            with open(str(path), 'w') as outfile:
                yaml.dump(content, outfile, default_flow_style=False)

            self.logger.debug('File {} saved successfully'.format(path))
            result = True
        except OSError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to OSError: {}'.format(e))
        except ValueError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to ValueError: {}'.format(e))
        except yaml.YAMLError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to YAMLError: {}'.format(e))
        except Exception as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to save the file with: {}'.format(e))

        return result

    def load_yaml_file(self, path: str) -> dict:
        """
        Load content of YAML file.

        :param      path:  The path to load the content from
        :type       path:  str

        :returns:   Loaded content of file
        :rtype:     dict
        """
        content = dict()

        try:
            with open(str(path)) as file:
                parsed_content = yaml.safe_load_all(file)

                for data in parsed_content:
                    content.update(data)

            self.logger.debug('Content of {} loaded successfully'.format(path))
        except OSError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to OSError: {}'.format(e))
        except ValueError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to ValueError: {}'.format(e))
        except yaml.YAMLError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to YAMLError: {}'.format(e))
        except Exception as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to load file content: {}'.format(e))

        return content

    def save_json_file(self,
                       path: str,
                       content: dict,
                       pretty: bool = True,
                       sort_keys: bool = True) -> bool:
        """
        Save content as a JSON file.

        :param      path:       The path to save the file to
        :type       path:       str
        :param      content:    The content to save
        :type       content:    dict
        :param      pretty:     Save content human readable with indentations
        :type       pretty:     bool
        :param      sort_keys:  Sort content alphabetically
        :type       sort_keys:  bool

        :returns:   True if the content has been saved, False otherwise.
        :rtype:     bool
        """
        result = False

        try:
            with open(str(path), 'w') as outfile:
                if pretty:
                    json.dump(content, outfile, indent=4, sort_keys=sort_keys)
                else:
                    json.dump(content, outfile, sort_keys=sort_keys)

            self.logger.debug('File {} saved successfully'.format(path))
            result = True
        except OSError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to OSError: {}'.format(e))
        except ValueError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to ValueError: {}'.format(e))
        except Exception as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to save the file with: {}'.format(e))

        return result

    def load_json_file(self, path: str) -> dict:
        """
        Load content of JSON file.

        :param      path:  The path to load the content from
        :type       path:  str

        :returns:   Loaded content of file
        :rtype:     dict
        """
        content = dict()

        try:
            with open(str(path)) as file:
                content = json.load(file)

            self.logger.debug('Content of {} loaded successfully'.format(path))
        except OSError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to OSError: {}'.format(e))
        except ValueError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to ValueError: {}'.format(e))
        except Exception as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to load file content: {}'.format(e))

        return content

    def save_dict_to_file(self, file_path: str, content: dict) -> bool:
        """
        Save a dictionary as a file.

        Type of file is choosen based on suffix of file path.
        JSON or YAML are supported

        :param      file_path:  The path to save the file to
        :type       file_path:  str
        :param      content:    The content to save
        :type       content:    dict

        :returns:   True if the content has been saved, False otherwise.
        :rtype:     boolean
        """
        result = False
        supported_file_types = ['.json', '.yaml']
        file_path = Path(file_path)
        file_type = file_path.suffix.lower()

        if not self.check_option_values(options=supported_file_types,
                                        option=file_type):
            self.logger.warning('{} is not valid option of {}'.
                                format(file_type, supported_file_types))
            return result

        # check for existing parent directory of specified file
        # and to be either a dict or a valid json
        if not file_path.parents[0].is_dir():
            self.logger.warning('Given path is not a directory')
            return result

        if not isinstance(content, dict):
            self.logger.warning('Given content is not a dictionary')
            return result

        self.logger.debug('Save file to: {}'.format(str(file_path)))
        if file_type == '.json':
            if not self.is_json(json.dumps(content)):
                self.logger.warning('Given content is not a valid json')
                return result

            result = self.save_json_file(path=str(file_path), content=content)
        elif file_type == '.yaml':
            result = self.save_yaml_file(path=str(file_path), content=content)

        return result

    def load_dict_from_file(self, file_path: str) -> dict:
        """
        Load a dictionary from file.

        :param      file_path:  The path to the file to load
        :type       file_path:  str

        :returns:   Loaded content
        :rtype:     dict
        """
        result = dict()
        supported_file_types = ['.json', '.yaml']
        file_path = Path(file_path)
        file_type = file_path.suffix.lower()

        if not self.check_option_values(options=supported_file_types,
                                        option=file_type):
            self.logger.warning('{} is not valid option of {}'.
                                format(file_type, supported_file_types))
            return result

        # check for existing parent directory of specified file
        # and to be either a dict or a valid json
        if not file_path.is_file():
            self.logger.warning('Given path is not a valid file')
            return result

        self.logger.debug('Load file from: {}'.format(str(file_path)))
        if file_type == '.json':
            result = self.load_json_file(path=str(file_path))
        elif file_type == '.yaml':
            result = self.load_yaml_file(path=str(file_path))

        return result

    def get_raw_file_content(self, file_path: str) -> str:
        """
        Get the raw file content as string.

        :param      file_path:  The path to the file to read
        :type       file_path:  str

        :returns:   The raw file content.
        :rtype:     str
        """
        content = ''

        try:
            with open(str(file_path), 'r') as input_file:
                content = input_file.read()

            self.logger.debug('Content of {} read successfully'.
                              format(file_path))
        except OSError as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to read the file content {}'.format(e))

        return content

    def save_list_to_file(self,
                          file_path: str,
                          content: list,
                          with_new_line: bool = False,
                          mode: str = 'w') -> bool:
        """
        Save list of lines to a file.

        :param      file_path:      The path to save the file to
        :type       file_path:      str
        :param      content:        The content to save
        :type       content:        list
        :param      with_new_line:  Flag to save each line with a linebreak
        :type       with_new_line:  bool, optional
        :param      mode:           Type of writing to the file
        :type       mode:           str, optional

        :returns:   True if the content has been saved, False otherwise.
        :rtype:     bool
        """
        result = False
        supported_file_modes = ['a', 'w']

        if not isinstance(content, list):
            self.logger.warning('Content to save must be list')
            return result

        if not self.check_option_values(options=supported_file_modes,
                                        option=mode):
            self.logger.warning('{} is not valid option of {}'.
                                format(mode, supported_file_modes))
            return result

        try:
            with open(str(file_path), mode) as outfile:
                for line in content:
                    outfile.write(line)

                    if with_new_line:
                        outfile.write("\n")

            self.logger.debug('Content successfully saved to {}'.
                              format(file_path))
            result = True
        except Exception as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to save content to file: {}'.format(e))

        return result
