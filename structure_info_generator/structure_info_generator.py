#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Structure info generator.

Create JSON file with structure of child folders
"""

import logging
from pathlib import Path

# custom imports
from be_helpers import ModuleHelper


class StructureInfoGenerator(ModuleHelper):
    """docstring for StructureInfoGenerator"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(StructureInfoGenerator, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self.info_dict = dict()

        self.logger.debug('StructureInfoGenerator init finished')

    def create_info_dict(self, root_path: str) -> None:
        """
        Create an information dictionary of the structure.

        :param      root_path:  The path to the top root folder
        :type       root_path:  str
        """
        self.info_dict = self._process_directory(root_path=root_path)

    def _process_directory(self, root_path: str) -> dict:
        """
        Process a directory to extract all subfolders and call them recursive

        :param      root_path:  The path to the top root folder
        :type       root_path:  str

        :returns:   Dictionary of informations about this folder
        :rtype:     dict
        """
        root_path = Path(root_path)
        info_dict = dict()

        # crawl all elements in this directory
        for ele in root_path.iterdir():
            if ele.is_dir():
                # crawl child folder in recursive way
                info_dict[ele.name] = self._process_directory(root_path=ele)
            elif ele.is_file():
                # check for an compilation info json file
                if ele.name == 'compilation-info.json':
                    info_dict['info'] = 'compilation-info.json'
                else:
                    # check for detailed informations about this folder
                    for name in ['targets.txt', 'brief.txt']:
                        if ele.name == name:
                            file_content = self.get_raw_file_content(
                                file_path=str(ele))
                            # add content of file to dict
                            if file_content:
                                info_dict[ele.stem] = file_content
                                # info_dict['targets'] = 'esp8266, esp32'
                                # info_dict['brief'] = 'Simple blinking sketch'

        return info_dict

    def get_info_dict(self) -> dict:
        """
        Get the latest information dictionary.

        :returns:   The information dictionary.
        :rtype:     dict
        """
        return self.info_dict
