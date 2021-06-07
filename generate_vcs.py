#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# ----------------------------------------------------------------------------
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         generate_vcs.py
#  @date         June, 2021
#  @version      0.2.0
#  @brief        Generate vcsInfo.h file based on available Git informations
#
#  @usage
#  python generate_vcs.py \
#   --directory=../../ \
#   --hw-semver=4.0.0 \
#   --output=./ \
#   --save \
#   --print \
#   -d -v4
#
#  python generate_vcs.py \
#   --directory=../../ \
#   --print \
#   -d -v4
#
#  optional arguments:
#   -h, --help
#
#   --directory     Path to the root git folder
#   --hw-semver     SemVer of hardware revision
#   -o, --output    Path to the output directory
#   -p, --print     Print content to stdout
#   -s, --save      Save collected informations to specified output directory
#
#   -d, --debug     Flag, Output logger messages to stderr (default: False)
#   -v, --verbose   Verbosity level (default: None), sets debug flag to True
#                   '-v3' or '-vvvv' == INFO
#
# ----------------------------------------------------------------------------

__author__ = "Jonas Scharpf"
__copyright__ = "Copyright by brainelectronics, ALL RIGHTS RESERVED"
__credits__ = ["Jonas Scharpf"]
__version__ = "0.1.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Alpha"

import argparse
import datetime
import json
import logging
from pathlib import Path
import semver
import sys

# custom imports
from git_wrapper.git_wrapper import GitWrapper


class VAction(argparse.Action):
    """docstring for VAction"""
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(VAction, self).__init__(option_strings, dest, nargs, const,
                                      default, type, choices, required,
                                      help, metavar)
        self.values = 0

    def __call__(self, parser, args, values, option_string=None):
        """Actual call or action to perform"""
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


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.

    :raise  argparse.ArgumentError
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Generate vcsInfo.h file
    """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Output logger messages to stderr')
    parser.add_argument('-v', "--verbose",
                        nargs='?',
                        action=VAction,
                        dest='verbose',
                        help='Set level of verbosity')

    parser.add_argument('--directory',
                        required=True,
                        help='Path to the root git folder')

    parser.add_argument('--hw-semver',
                        dest='hw_semver',
                        help='SemVer of hardware revision')

    parser.add_argument('-o', '--output',
                        required=False,
                        help='Path to the output directory')

    parser.add_argument('-p', '--print',
                        dest='print_content',
                        action='store_true',
                        help='Print content to stdout')

    parser.add_argument('-s', '--save',
                        dest='save_content',
                        action='store_true',
                        help='Save collected informations to specified output '
                        'directory')

    parsed_args = parser.parse_args()

    return parsed_args


def parse_semver(tag: str,
                 logger: logging.Logger,
                 identifier: str = 'sw') -> dict:
    """
    Parse the semantic version string

    :param      tag:        The tag
    :type       tag:        string
    :param      identifier: Identifier for semver, like 'hw' or 'sw'
    :type       identifier: string, optional
    :param      logger:     The logger
    :type       logger:     logger object

    :returns:   Informations of parsed semantic version
    :rtype:     dict
    """
    semver_dict = dict()

    if len(identifier):
        # extend the identifier with an underscore only if it is set
        identifier = identifier + '_'

    try:
        ver = semver.VersionInfo.parse(tag)
        logger.debug('SemVer tag: {}'.format(ver))

        # major, minor, patch, prerelease
        semver_dict['major_{}version'.format(identifier)] = ver.major
        semver_dict['minor_{}version'.format(identifier)] = ver.minor
        semver_dict['patch_{}version'.format(identifier)] = ver.patch
        semver_dict['prerelease_{}version'.format(identifier)] = ver.prerelease
        semver_dict['build_{}version'.format(identifier)] = ver.build

        logger.debug('SemVer dict: {}'.format(json.dumps(semver_dict,
                                                         indent=4,
                                                         sort_keys=True)))
    except Exception as e:
        logger.warning(e)

    return semver_dict


def convert_string_to_uint16t(content: str,
                              logger: logging.Logger) -> list:
    """
    Convert string to list of uint16_t values

    :param      content:  The string content to convert
    :type       content:  str
    :param      logger:   The logger
    :type       logger:   logger object

    :returns:   Unicode converted list of uint16_t numbers
    :rtype:     list
    """
    # convert all characters to their unicode code, 'A' -> 65 ...
    unicode_list = [ord(x) for x in content]
    logger.debug('Content as unicode: {}'.format(unicode_list))

    # iter the list and create tuples
    # represented by 8 bit, two unicode chars can be represented by a 16 bit
    it = iter(unicode_list)
    tuple_list = zip(it, it)

    # create a 16 bit number of two unicode numbers
    number_list = list()
    for ele in tuple_list:
        number_list.append((ele[0] << 8) | ele[1])

    logger.debug('Content as numbers: {}'.format(number_list))

    return number_list


def load_file_content(file_path: str,
                      logger: logging.Logger) -> list:
    """
    Get the content of a file.

    :param      file_path:  The file path
    :type       file_path:  str
    :param      logger:     The logger
    :type       logger:     logging.Logger

    :returns:   Content of file
    :rtype:     list
    """
    file_lines = list()

    if Path(file_path).is_file():
        logger.debug('Reading content of {}'.format(file_path))

        with open(str(file_path), 'r') as file:
            file_lines = file.read().splitlines()
    else:
        logger.warning('{} is not a valid file'.format(file_path))

    return file_lines


def create_vcs_content_dict(semver_dict: dict,
                            git_dict: dict,
                            logger: logging.Logger) -> dict:
    """
    Create vcs content dictionary.

    :param      semver_dict:    The semver dictionary
    :type       semver_dict:    dict
    :param      git_dict:       The git dictionary
    :type       git_dict:       dict
    :param      logger:         The logger
    :type       logger:         logger object

    :returns:   VCS content
    :rtype:     dict
    """
    content_dict = dict()

    date_today = datetime.datetime.today().strftime('%d.%m.%Y')
    epoch_datetime = datetime.datetime(year=1970, month=1, day=1)
    days_since_epoch = (datetime.datetime.utcnow() - epoch_datetime).days
    commit_sha_short = git_dict['sha_short']
    commit_number_list = convert_string_to_uint16t(content=commit_sha_short,
                                                   logger=logger)

    # file header content
    content_dict['MODIFIED_DATE'] = date_today
    content_dict['CREATED_DATE'] = content_dict['MODIFIED_DATE']
    content_dict['YEAR'] = datetime.datetime.today().strftime('%Y')

    # file definition content
    fw_version_number = int("{}{}{}".format(semver_dict['major_sw_version'],
                                            semver_dict['minor_sw_version'],
                                            semver_dict['patch_sw_version']))
    content_dict['CURRENT_FIRMWARE_VERSION'] = fw_version_number
    content_dict['MAJOR_SW_VERSION'] = semver_dict['major_sw_version']
    content_dict['MINOR_SW_VERSION'] = semver_dict['minor_sw_version']
    content_dict['PATCH_SW_VERSION'] = semver_dict['patch_sw_version']
    if 'major_hw_version' in semver_dict:
        content_dict['MAJOR_HW_VERSION'] = semver_dict['major_hw_version']
    if 'minor_hw_version' in semver_dict:
        content_dict['MINOR_HW_VERSION'] = semver_dict['minor_hw_version']
    if 'patch_hw_version' in semver_dict:
        content_dict['PATCH_HW_VERSION'] = semver_dict['patch_hw_version']
    content_dict['CREATION_DATE'] = days_since_epoch
    content_dict['COMMIT_SHA_I'] = commit_number_list[0]
    content_dict['COMMIT_SHA_II'] = commit_number_list[1]
    content_dict['COMMIT_SHA_III'] = commit_number_list[2]
    content_dict['COMMIT_SHA_IV'] = commit_number_list[3]

    logger.debug('VCS content dict: {}'.format(json.dumps(content_dict,
                                                          indent=4,
                                                          sort_keys=True)))

    return content_dict


def fill_vcs_template(lines: list,
                      semver_dict: dict,
                      git_dict: dict,
                      logger: logging.Logger) -> list:
    """
    Replace vcs placeholders with content

    :param      lines:          The lines of the vcs template file
    :type       lines:          list
    :param      semver_dict:    The semver dictionary
    :type       semver_dict:    dict
    :param      git_dict:       The git dictionary
    :type       git_dict:       dict
    :param      logger:         The logger
    :type       logger:         logger object

    :returns:   Filled vcs content lines
    :rtype:     list
    """
    changed_lines = list()

    content_dict = create_vcs_content_dict(semver_dict=semver_dict,
                                           git_dict=git_dict,
                                           logger=logger)

    # iterate over all lines and replace placeholders
    for line in lines:
        for key, val in content_dict.items():
            placeholder = '${}$'.format(key)
            if placeholder in line:
                if placeholder == '$COMMIT_SHA_I$':
                    print('add commit sha as comment')
                    logger.debug('Add commit sha as comment before {}'.
                                 format(placeholder))
                    commit_sha_comment = '// {}'.format(git_dict['sha_short'])
                    changed_lines.append(commit_sha_comment)

                logger.debug('found: {}, replace with: {}'.format(placeholder,
                                                                  val))
                line = line.replace(placeholder, str(val))
                break

        if line.count('$') >= 2:
            # skip lines which placeholders are not replaced
            logger.info('Skipping line: {}'.format(line))
        else:
            changed_lines.append(line)

    return changed_lines


def generate_vcs_info_file(output_path: str,
                           semver_dict: dict,
                           git_dict: dict,
                           print_content: bool,
                           save_content: bool,
                           logger: logging.Logger) -> bool:
    """
    Generate VCS file based on semver dict and git dict

    :param      output_path:    The output path
    :type       output_path:    string
    :param      semver_dict:    The semver dictionary
    :type       semver_dict:    dict
    :param      semver_dict:    The hardware dictionary
    :type       semver_dict:    dict
    :param      git_dict:       The git dictionary
    :type       git_dict:       dict
    :param      print_content:  Print content to console
    :type       print_content:  bool
    :param      save_content:   Save content to file
    :type       save_content:   bool
    :param      logger:         The logger
    :type       logger:         logger object

    :returns:   Result of reading, filling and saving the vcs file
    :rtype:     bool
    """

    result = False

    current_path = Path(__file__).resolve()
    vcs_template_path = current_path.parent / '..' / 'templates'
    vcs_template_file = vcs_template_path / 'vcsInfo.h.template'
    logger.debug('VCS template path: {}'.format(vcs_template_file))
    vcs_template_lines = load_file_content(file_path=vcs_template_file,
                                           logger=logger)

    if len(vcs_template_lines):
        filled_vcs_template_lines = fill_vcs_template(lines=vcs_template_lines,
                                                      semver_dict=semver_dict,
                                                      git_dict=git_dict,
                                                      logger=logger)

        if (save_content is True) and (output_path is not None):
            output_path = Path(output_path)
            if not output_path.is_dir():
                logger.error('Given path is not a directory')
            else:
                output_file = output_path / 'vcsInfo.h'
                result = save_list_to_file(file_path=output_file,
                                           content=filled_vcs_template_lines,
                                           logger=logger)
                logger.debug('Saved content to file: {}'.format(result))
        else:
            if output_path is None:
                logger.warning('Could not save content to file as output path'
                               ' is None')

        if print_content:
            for line in filled_vcs_template_lines:
                print(line)

    return result


def save_list_to_file(file_path: str,
                      content: list,
                      logger: logging.Logger) -> bool:
    """
    Save content list to file.

    :param      file_path:  The file path
    :type       file_path:  str
    :param      content:    The content to save
    :type       content:    list
    :param      logger:     The logger
    :type       logger:     logger object

    :returns:   Result of saving the file
    :rtype:     bool
    """
    result = False
    file_path = Path(file_path)
    logger.debug('Save content to {}'.format(file_path))

    with open(str(file_path), 'w') as file:
        for line in content:
            file.write("%s\n" % line)

        result = True

    return result


if __name__ == '__main__':
    logger = create_logger(__name__)

    # parse CLI arguments
    args = parse_arguments()
    verbose_level = args.verbose

    # set verbose level based on user setting
    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    LOG_LEVELS = LOG_LEVELS[::-1]

    if verbose_level is None:
        if not args.debug:
            # disable the logger of this file
            logger.disabled = True
    else:
        log_level = min(len(LOG_LEVELS) - 1, max(verbose_level, 0))
        log_level_name = LOG_LEVELS[log_level]

        # set the level of the logger of this file
        logger.setLevel(log_level_name)

    # log the provided arguments
    logger.debug(args)

    repo_path = args.directory
    hw_semver = args.hw_semver
    output_path = args.output
    print_content = args.print_content
    save_content = args.save_content

    git_wrapper = GitWrapper(logger=logger)
    git_wrapper.parse_git_informations(repo_path=repo_path)
    git_dict = git_wrapper.get_git_dict()

    sw_semver_dict = parse_semver(tag=git_dict['describe'],
                                  identifier='sw',
                                  logger=logger)
    if hw_semver:
        hw_semver_dict = parse_semver(tag=hw_semver,
                                      identifier='hw',
                                      logger=logger)
    else:
        hw_semver_dict = dict()
    semver_dict = {**hw_semver_dict, **sw_semver_dict}

    result = generate_vcs_info_file(output_path=output_path,
                                    semver_dict=semver_dict,
                                    git_dict=git_dict,
                                    print_content=print_content,
                                    save_content=save_content,
                                    logger=logger)

    if result:
        sys.exit()
    else:
        sys.exit(1)
