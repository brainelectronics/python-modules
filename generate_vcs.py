#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# ----------------------------------------------------------------------------
#
#  @author       Jonas Scharpf (info@brainelectronics.de) brainelectronics
#  @file         generate_vcs.py
#  @date         July, 2021
#  @version      0.3.0
#  @brief        Generate vcs info file based on available Git informations
#
#  @usage
#  python generate_vcs.py \
#   --directory=../../ \
#   --hw-semver=4.0.0 \
#   --print \
#   --save \
#   --output=./ \
#   -v4 -d
#
#  python generate_vcs.py \
#   --directory=../../ \
#   --print \
#   -v4 -d
#
#  optional arguments:
#   -h, --help
#
#   --directory     Path to the root git folder
#   --hw-semver     SemVer of hardware revision
#   -o, --output    Path to the output directory or file
#   --print         Print content to stdout
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
__version__ = "0.3.0"
__maintainer__ = "Jonas Scharpf"
__email__ = "jonas@brainelectronics.de"
__status__ = "Beta"

import argparse
import datetime
import json
import logging
from pathlib import Path
import semver
import sys

# custom imports
from git_wrapper.git_wrapper import GitWrapper
from module_helper.module_helper import ModuleHelper


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
        if values is None:
            pass
            # do not increment here, so '-v' will use highest log level
        else:
            try:
                self.values = int(values)
            except ValueError:
                self.values = values.count('v')  # do not count the first '-v'
        setattr(args, self.dest, self.values)


def parse_arguments() -> argparse.Namespace:
    """
    Parse CLI arguments.

    :raise  argparse.ArgumentError
    :return: argparse object
    """
    parser = argparse.ArgumentParser(description="""
    Generate vcsInfo.h file
    """, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # default arguments
    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='Output logger messages to stderr')
    parser.add_argument('-v', "--verbose",
                        nargs='?',
                        action=VAction,
                        dest='verbose',
                        help='Set level of verbosity')

    # specific arguments
    parser.add_argument('--directory',
                        required=True,
                        type=lambda x: ModuleHelper.parser_valid_dir(parser,
                                                                     x),
                        help='Path to the root git folder')

    parser.add_argument('--hw-semver',
                        dest='hw_semver',
                        help='SemVer of hardware revision')

    parser.add_argument('-o', '--output',
                        required=False,
                        help='Path to the output directory or file')

    parser.add_argument('--print',
                        dest='print_result',
                        action='store_true',
                        help='Print collected info to stdout')

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


def create_vcs_content_dict(semver_dict: dict,
                            git_dict: dict,
                            module_helper: ModuleHelper,
                            logger: logging.Logger) -> dict:
    """
    Create vcs content dictionary.

    :param      semver_dict:    The semver dictionary
    :type       semver_dict:    dict
    :param      git_dict:       The git dictionary
    :type       git_dict:       dict
    :param      module_helper:  The module helper
    :type       module_helper:  ModuleHelper object
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
    commit_number_list = module_helper.convert_string_to_uint16t(
        content=commit_sha_short)

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
                      file_name: str,
                      module_helper: ModuleHelper,
                      logger: logging.Logger) -> list:
    """
    Replace vcs placeholders with content

    :param      lines:          The lines of the vcs template file
    :type       lines:          list
    :param      semver_dict:    The semver dictionary
    :type       semver_dict:    dict
    :param      git_dict:       The git dictionary
    :type       git_dict:       dict
    :param      file_name:      The file name
    :type       file_name:      str
    :param      module_helper:  The module helper
    :type       module_helper:  ModuleHelper object
    :param      logger:         The logger
    :type       logger:         logger object

    :returns:   Filled vcs content lines
    :rtype:     list
    """
    changed_lines = list()

    content_dict = create_vcs_content_dict(semver_dict=semver_dict,
                                           git_dict=git_dict,
                                           module_helper=module_helper,
                                           logger=logger)
    content_dict['FILENAME'] = file_name
    c_file_name = file_name.replace('.', '_').replace('-', '_')
    content_dict['FILENAME_FOR_C'] = c_file_name

    # iterate over all lines and replace placeholders
    for line in lines:
        for key, val in content_dict.items():
            placeholder = '${}$'.format(key)
            if placeholder in line:
                if placeholder == '$COMMIT_SHA_I$':
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


if __name__ == '__main__':
    helper = ModuleHelper(quiet=True)

    logger = helper.create_logger(__name__)

    # parse CLI arguments
    args = parse_arguments()

    # set verbose level based on user setting
    helper.set_logger_verbose_level(logger=logger,
                                    verbose_level=args.verbose,
                                    debug_output=not args.debug)

    # log the provided arguments
    logger.debug(args)

    # take CLI parameters
    repo_path = args.directory
    hw_semver = args.hw_semver
    output_path = args.output
    print_result = args.print_result
    save_content = args.save_content

    git_wrapper = GitWrapper(logger=logger, quiet=not args.debug)
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

    result = False

    current_path = Path(__file__).resolve()
    vcs_template_path = current_path.parent / 'example'
    vcs_template_file = vcs_template_path / 'vcsInfo.h.template'
    logger.debug('VCS template path: {}'.format(vcs_template_file))
    raw_lines = helper.get_raw_file_content(file_path=vcs_template_file)
    vcs_template_lines = raw_lines.splitlines()

    if len(vcs_template_lines):
        default_file_name = 'vcsInfo.h'
        if ((output_path is not None) and (not Path(output_path).is_dir())):
            file_name = Path(output_path).name
        else:
            file_name = default_file_name

        filled_vcs_lines = fill_vcs_template(lines=vcs_template_lines,
                                             semver_dict=semver_dict,
                                             git_dict=git_dict,
                                             file_name=file_name,
                                             module_helper=helper,
                                             logger=logger)

        if save_content:
            if output_path is not None:
                output_path = Path(output_path)

                if output_path.is_dir():
                    output_file = output_path / default_file_name
                    logger.info('Given path is a directory, saving output as'.
                                format(output_file))
                else:
                    output_file = output_path

                result = helper.save_list_to_file(file_path=output_file,
                                                  content=filled_vcs_lines,
                                                  with_new_line=True)
                logger.debug('Result of saving info {}'.format(result))
            else:
                logger.warning('Can not save to not specified file')

        # do print as last step
        if print_result:
            for line in filled_vcs_lines:
                print(line)

    if result:
        sys.exit()
    else:
        sys.exit(1)
