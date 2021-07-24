#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# ----------------------------------------------------------------------------
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         generate_modbus_json.py
#  @date         June, 2021
#  @version      0.2.0
#  @brief        Generate a JSON file from a modbus register header file
#
#  @note         No numbers are allowed in the register name
#
#  @usage
#  python3 generate_modbus_json.py \
#   --input=modbusRegisters.h
#   --print \
#   --pretty \
#   --save \
#   --output=outputFolder \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   --input         Header file of modbus registers
#   --output        Path to output folder or file for JSON file, default name
#                   is set as 'registers.json' if path is provided
#   --pretty        Print collected info to stdout in human readable format
#   -p, --print     Print JSON to stdout
#   -s, --save      Save collected informations to file
#
#   -d, --debug     Flag, Output logger messages to stderr (default: False)
#   -v, --verbose   Verbosity level (default: None), sets debug flag to True
#                   '-v3' or '-vvvv' == INFO
#
# ----------------------------------------------------------------------------

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright by brainelectronics, ALL RIGHTS RESERVED"
__credits__ = ["Jonas Scharpf"]
__version__ = "0.2.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "info@brainelectronics.de"
__status__ = "Development"

import argparse
import json
import logging
from pathlib import Path
import re
import sys


class VAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(VAction, self).__init__(option_strings, dest, nargs, const,
                                      default, type, choices, required,
                                      help, metavar)
        self.values = 0

    def __call__(self, parser, args, values, option_string=None):
        # print('values: {v!r}'.format(v=values))
        if values is None:
            pass
            # do not increment here, so '-v' will use highest log level
            # self.values += 1
        else:
            try:
                self.values = int(values)
            except ValueError:
                # self.values = values.count('v')+1
                self.values = values.count('v')  # do not count the first '-v'
        setattr(args, self.dest, self.values)


def create_logger(logger_name: str = None) -> logging.Logger:
    """
    Creates a logger.

    :param      logger_name:  The logger name
    :type       logger_name:  str

    :returns:   Logger
    :rtype:     logging.Logger
    """

    # define a format
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


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.

    :raise  argparse.ArgumentError
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Generate JSON of modbus register header file
    """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Output logger messages to stderr')
    parser.add_argument('-v', "--verbose",
                        nargs='?',
                        action=VAction,
                        dest='verbose',
                        help='Set level of verbosity')

    parser.add_argument('--input',
                        required=True,
                        help='Header file of modbus registers')

    parser.add_argument('--output',
                        required=False,
                        help='Path to output folder or file for JSON file, '
                        'default name is set as "registers.json" if path is '
                        'provided')

    parser.add_argument('--pretty',
                        dest='print_pretty',
                        action='store_true',
                        help='Print collected info to stdout in human readable'
                        'format')

    parser.add_argument('-p', '--print',
                        dest='print_result',
                        action='store_true',
                        help='Print collected info to stdout')

    parser.add_argument('-s', '--save',
                        dest='save_info',
                        action='store_true',
                        help='Save collected informations to file specified'
                        'Specified with --output or -o')

    parsed_args = parser.parse_args()

    return parsed_args


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


def check_folder(folder_path: str) -> bool:
    """
    Check existance of folder

    :param      folder_path:  The path to the folder
    :type       folder_path:  string

    :returns:   Result of folder check
    :rtype:     boolean
    """
    result = False

    folder_path = Path(folder_path)

    if Path(folder_path).is_dir():
        result = True

    return result


def extract_defined_registers(file_path: str, logger: logging.Logger) -> dict:
    """
    Extract all registers, their unit, description, length and range from the
    header file and return a dict of that informations

    :param      file_path:  The path to the input modbus register file
    :type       file_path:  string
    :param      logger:     The logger
    :type       logger:     logger object

    :returns:   Dictionary of extracted informations
    :rtype:     dictionary
    """
    # create dict of register names
    registers_dict = dict()
    registers_dict['COILS'] = dict()
    registers_dict['HREGS'] = dict()
    registers_dict['ISTS'] = dict()
    registers_dict['IREGS'] = dict()
    registers_dict['META'] = dict()

    # read all lines of the file
    file_lines = []
    with open(str(file_path), 'r') as file:
        file_lines = file.read().splitlines()

    # extract lines of register definition or addtional comment only
    definition_lines = []
    for idx, line in enumerate(file_lines):
        if idx < 10:
            if 'Modified on ' in line:
                modified_date = line.split('Modified on ')[1]
                logger.debug('Modified: {}'.format(modified_date))
                registers_dict['META']['modified'] = modified_date

            if ('Created ' in line) and (' on ' in line):
                creation_date = line.split(' on ')[1]
                logger.debug('Created: {}'.format(creation_date))
                registers_dict['META']['created'] = creation_date

        # use only lines with a comment for register extraction
        if '//<' in line:
            definition_lines.append(line)

    # iterate all register lines
    for idx, line in enumerate(definition_lines):
        # take only line of register definiton
        if line.startswith('#define '):
            # get the register name which must be given in capital letters and
            # must be more or equal to 3 characters
            register_name = re.findall(r'[A-Z_]{3,}', line)[0]

            # get the first number with any length, which shall be the register
            register_register = re.findall(r'\d+', line)[0]

            # loop over all additional registers if any available in the next
            # line
            i = 1
            nextelem = definition_lines[(idx + i) % len(definition_lines)]
            while not nextelem.startswith('#define '):
                i += 1
                nextelem = definition_lines[(idx + i) % len(definition_lines)]

            # do not count the start register itself as it is repeated
            if i > 1:
                i -= 1

            # get the description of that register after the doxygen comment
            register_description = line.split('//< ')[1]

            # try to get unit of register description provided as '[something]'
            register_unit_list = re.findall(r'\[(.*?)\]', register_description)
            register_range = ''
            register_unit = ''
            # check for any matches
            if register_unit_list:
                # check for range info, like [0, 4095]
                if ',' in register_unit_list[0]:
                    register_range = register_unit_list[0]
                else:
                    # take it as unit
                    register_unit = register_unit_list[0]

            # fill this registers dictionaly with content
            this_register_dict = dict()
            this_register_dict['register'] = int(register_register)
            this_register_dict['len'] = int(i)
            this_register_dict['description'] = register_description
            this_register_dict['range'] = register_range
            this_register_dict['unit'] = register_unit

            # add this register dict to the proper section of the overall dict
            if register_name.endswith('_COIL'):
                registers_dict['COILS'][register_name] = this_register_dict
            elif register_name.endswith('_HREG'):
                registers_dict['HREGS'][register_name] = this_register_dict
            elif register_name.endswith('_ISTS'):
                registers_dict['ISTS'][register_name] = this_register_dict
            elif register_name.endswith('_IREG'):
                registers_dict['IREGS'][register_name] = this_register_dict

    # logger.debug(json.dumps(registers_dict, indent=4, sort_keys=False))
    return registers_dict


def save_json_file(file_path: str,
                   registers_dict: dict,
                   file_name: str,
                   logger: logging.Logger) -> bool:
    """
    Save content of dictionary as JSON file to parent directory.

    :param      file_path:       The file path
    :type       file_path:       str
    :param      registers_dict:  The registers dictionary
    :type       registers_dict:  dict
    :param      file_name:       Name of file
    :type       file_name:       str, optional
    :param      logger:          The logger
    :type       logger:          logging.Logger

    :returns:   Result of saving the file
    :rtype:     bool
    """
    result = False
    file_path = Path(file_path)
    json_file_path = None
    if not file_name:
        file_name = 'registers.json'
        logger.info('No file name given, using default: {}'.format(file_name))

    if file_path.is_dir():
        json_file_path = file_path / file_name
    elif file_path.is_file():
        if file_path.parent.is_dir():
            json_file_path = file_path.with_suffix('.json')

    if json_file_path:
        logger.debug('JSON file path: {}'.format(json_file_path.resolve()))

        with open(str(json_file_path), 'w') as file:
            json.dump(registers_dict, file, indent=4)
            result = True

    return result


if __name__ == '__main__':
    logger = create_logger(__name__)

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    verbose_level = args.verbose
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_LEVELS = LOG_LEVELS[::-1]

    if verbose_level is None:
        if not args.debug:
            # disable the logger of this file and the ReleaseInfoGenerator
            logger.disabled = True
    else:
        log_level = min(len(LOG_LEVELS) - 1, max(verbose_level, 0))
        log_level_name = LOG_LEVELS[log_level]

        # set the level of the logger of this file and the ReleaseInfoGenerator
        logger.setLevel(log_level_name)

    # take CLI parameters
    file_path = Path(args.input)
    output_arg = args.output
    if output_arg:
        if check_folder(output_arg) or check_file(output_arg, '.json'):
            output_path = Path(output_arg)
        else:
            logger.warning('Can not save JSON to {}'.format(output_path))
    else:
        output_path = file_path

    save_info = args.save_info
    print_result = args.print_result
    print_pretty = args.print_pretty

    # log the provided arguments
    logger.debug(args)

    logger.debug('Input file: {}'.format(file_path))

    file_check_result = check_file(file_path, '.h')
    logger.debug('Input file check result: {}'.format(file_check_result))

    registers_dict = dict()

    if file_check_result:
        registers_dict = extract_defined_registers(file_path=file_path,
                                                   logger=logger)

        if save_info:
            file_name = None
            if output_path.is_file():
                file_name = output_path.name

            result = save_json_file(file_path=output_path,
                                    registers_dict=registers_dict,
                                    file_name=file_name,
                                    logger=logger)
            logger.debug('Result of saving info as JSON: {}'.format(result))

        # do print as last step
        if print_result:
            if print_pretty:
                print(json.dumps(registers_dict, indent=4, sort_keys=True))
            else:
                print(json.dumps(registers_dict, sort_keys=True))
