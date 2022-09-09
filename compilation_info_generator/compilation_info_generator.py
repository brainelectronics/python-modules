#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Compilation info generator.

Save JSON file with environment, git and file info related data
"""

import logging
import os
from pathlib import Path

# custom imports
from be_helpers import ModuleHelper
from git_wrapper import GitWrapper


class CompilationInfoGenerator(GitWrapper, ModuleHelper):
    """docstring for CompilationInfoGenerator"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(CompilationInfoGenerator, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self.env_dict = dict()
        self.info_dict = dict()

        self.logger.debug('CompilationInfoGenerator init finished')

    def _collect_env_vars(self) -> None:
        """ Collect relevant environment variables"""
        self.env_dict.clear()

        # add env variables to dict with fallback value
        self.env_dict['build_id'] = os.environ.get('BUILD_ID', 0)
        self.env_dict['job_name'] = os.environ.get('JOB_NAME', '')
        self.env_dict['creator'] = os.environ.get('USER', '')

    def get_env_vars(self) -> dict:
        """
        Get the environment variables dictionary.

        :returns:   The environment variables.
        :rtype:     dict
        """
        return self.env_dict

    def _collect_git_info(self, path: str) -> None:
        """
        Collect git informations

        :param      path:  The path to the git repository
        :type       path:  str
        """
        self.parse_git_informations(repo_path=path)

    def create_info_dict(self, git_path: str, file_path: str) -> None:
        """
        Create complete information dictionary.

        :param      git_path:   The path to the git repository
        :type       git_path:   str
        :param      file_path:  The path to the file
        :type       file_path:  str
        """
        info_dict = dict()

        # create empty info dict
        info_dict['ci'] = dict()
        info_dict['vcs'] = dict()
        info_dict['binary'] = dict()

        # collect env informations
        self._process_env_info(info_dict=info_dict)

        # collect git informations
        self._process_git_info(path=git_path,
                               info_dict=info_dict)

        # collect binary informations
        self._process_binary_info(path=file_path,
                                  info_dict=info_dict)

        self.logger.debug('Created info_dict: {}'.format(info_dict))

        self.info_dict = info_dict

    def _process_env_info(self, info_dict: dict) -> None:
        """
        Process environment informations and add it to the info dict

        :param      info_dict:  The information dictionary
        :type       info_dict:  dict
        """
        self._collect_env_vars()

        env_dict = self.get_env_vars()

        # use subset of environment variables for info dict
        info_dict['ci']['creator'] = env_dict['creator']
        info_dict['ci']['job_name'] = env_dict['job_name']
        info_dict['ci']['build_id'] = env_dict['build_id']

        self.logger.debug('Updated info_dict ci section: {}'.
                          format(info_dict['ci']))

    def _process_git_info(self, path: str, info_dict: dict) -> None:
        """
        Process git informations and add it to the info dict

        :param      path:       The path to the git repository
        :type       path:       str
        :param      info_dict:  The information dictionary
        :type       info_dict:  dict
        """
        self._collect_git_info(path=path)

        vcs_dict = self.get_git_dict()

        # use subset of git informations for info dict
        info_dict['vcs']['commit'] = vcs_dict['sha_short']
        info_dict['vcs']['date'] = vcs_dict['committed_date']

        self.logger.debug('Updated info_dict vcs section: {}'.
                          format(info_dict['vcs']))

    def _process_binary_info(self, path: str, info_dict: dict) -> None:
        """
        Process binary file informations and add it to the info dict

        :param      path:       The path to the file
        :type       path:       str
        :param      info_dict:  The information dictionary
        :type       info_dict:  dict
        """
        if path is None:
            self.logger.debug('No file path given, skip it')
            return

        path = Path(path)

        if path.is_file():
            stats = os.stat(path)

            # use subset of file informations for info dict
            info_dict['binary']['name'] = path.name
            info_dict['binary']['size'] = stats.st_size
            info_dict['binary']['timestamp'] = int(stats.st_ctime)

        self.logger.debug('Updated info_dict binary section: {}'.
                          format(info_dict['binary']))

    def get_info_dict(self) -> dict:
        """
        Get the latest information dictionary.

        :returns:   The information dictionary.
        :rtype:     dict
        """
        return self.info_dict
