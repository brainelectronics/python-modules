#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Module helper

Collection of helper functions used in other modules
"""

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


class ModuleHelper(object):
    """docstring for ModuleHelper"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(ModuleHelper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

    def create_logger(self, logger_name: str = None) -> logging.Logger:
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
                self.logger.info('{} is not a valid option'.format(option))

        return result

    def check_option_values(self,
                            options: List[str],
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

    def format_timestamp(self, timestamp: int, format: str) -> str:
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

    def get_unix_timestamp(self) -> int:
        """
        Get the unix timestamp.

        :returns:   The unix timestamp.
        :rtype:     int
        """
        return (int(time.time()))

    def get_random_string(self, length: int) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits,
                                      k=length))

    def sort_by_name(self, a_list: list, descending: bool = False) -> bool:
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

    def is_json(self, content: dict) -> bool:
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
                       pretty: bool = True) -> bool:
        """
        Save content as a JSON file.

        :param      path:     The path to save the file to
        :type       path:     str
        :param      content:  The content to save
        :type       content:  dict
        :param      pretty:   Save content human readable with indentations
        :type       pretty:   bool

        :returns:   True if the content has been saved, False otherwise.
        :rtype:     bool
        """
        result = False

        try:
            with open(str(path), 'w') as outfile:
                if pretty:
                    json.dump(content, outfile, indent=4, sort_keys=True)
                else:
                    json.dump(content, outfile, sort_keys=True)

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
                          mode: str = 'w') -> bool:
        """
        Save list of lines to a file.

        :param      file_path:  The path to save the file to
        :type       file_path:  str
        :param      content:    The content to save
        :type       content:    list
        :param      mode:       Type of writing to the file
        :type       mode:       str, optional

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

            self.logger.debug('Content successfully saved to {}'.
                              format(file_path))
            result = True
        except Exception as e:
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed to save content to file: {}'.format(e))

        return result
