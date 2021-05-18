#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Software configuration management wrapper

Collection of repository related functions
"""

from git import Commit, Repo, TagReference
from gitdb.exc import BadObject, BadName
from git.exc import InvalidGitRepositoryError, NoSuchPathError, GitCommandError
import logging
import os
from pathlib import Path
from typing import List

# custom imports
from module_helper.module_helper import ModuleHelper


class GitWrapper(ModuleHelper):
    """docstring for GitWrapper"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(GitWrapper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self.repo = None
        self.git_dict = dict()

        self.logger.debug('GitWrapper init finished')

    def set_repo_path(self, path: str) -> bool:
        """
        Set the path to a repository.

        :param      path:  The path to the repository
        :type       path:  str

        :returns:   Result of creating a Repo object
        :rtype:     bool
        """
        repo_path = Path(path)

        if not repo_path.exists():
            return False

        try:
            self.repo = Repo(str(repo_path), search_parent_directories=True)
        except NoSuchPathError as e:    # by base.py @ __init__
            # use warning instead of exception to not raise it automatically
            self.logger.warning('No such path to repo: {}'.format(e))
            return False
        except (OSError, IOError) as e:    # by fun.py @ find_worktree_git_dir
            # use warning level instead of exception level to not raise error
            self.logger.warning('Failed due to OSError/IOError {}'.format(e))
            return False
        except InvalidGitRepositoryError as e:  # by base.py @ _to_relative_path
            # use warning level instead of exception level to not raise error
            self.logger.warning('Invalid git repository {}'.format(e))
            return False
        except GitCommandError as e:
            # use warning instead of exception to not raise it automatically
            self.logger.warning('Git command error {}'.format(e))
            return False

        return True

    def get_repo(self) -> Repo:
        """
        Get the repo object.

        :returns:   The repo.
        :rtype:     Repo
        """
        return self.repo

    def get_valid_repo(self, repo=None):
        """
        Get the valid repo.

        :param      repo:  The repo
        :type       repo:  Repo, optional

        :returns:   A valid repo or None.
        :rtype:     None or Repo object
        """
        if repo is None:
            # no repo given as argument, check configured repo
            if isinstance(self.repo, Repo):
                return self.repo
            else:
                self.logger.warning('Repo is not yet set, use set_repo_path()')
                return None
        else:
            # something is given as argument
            if isinstance(repo, Repo):
                # return given argument if it is already a repo object
                return repo
            elif isinstance(repo, str):
                # try to find a repo at the given path
                try:
                    repo_path = Path(repo)
                    self.repo = Repo(str(repo_path), search_parent_directories=True)
                    return self.repo
                except Exception as e:
                    # use warning instead of exception to not raise it automatically
                    self.logger.warning(e)
                    return None
            else:
                self.logger.warning('Given parameter is not a Repo object or path to a repo')
                return None

    def get_repo_root(self, repo=None) -> str:
        """
        Get the path to the first found git root.

        :param      repo:  The repo
        :type       repo:  Repo, optional


        :returns:   The git root.
        :rtype:     str
        """
        repo_root = ""

        this_repo = self.get_valid_repo(repo=repo)

        if this_repo is not None:
            repo_root = str(this_repo.working_dir)

        return repo_root

    def get_current_branch_name(self, repo=None) -> str:
        """
        Get the current branch name.

        :param      repo:  The repo
        :type       repo:  Repo, optional

        :returns:   The current branch name.
        :rtype:     str
        """
        branch_name = ""

        this_repo = self.get_valid_repo(repo=repo)

        if this_repo is not None:
            branch_name = str(this_repo.active_branch)

        return branch_name

    def get_all_tags(self, repo=None) -> List[TagReference]:
        """
        Get all tags of the repo sorted by committed datetime.

        :param      repo:  The repo
        :type       repo:  Repo, optional

        :returns:   All tags.
        :rtype:     list
        """
        tags = list()

        this_repo = self.get_valid_repo(repo=repo)

        if this_repo is not None:
            tags = sorted(this_repo.tags,
                          key=lambda t: t.commit.committed_datetime)

        return tags

    def get_commits(self,
                    branch: str,
                    repo=None,
                    max_count: int = None) -> List[Commit]:
        """
        Get the commits of the branch.

        :param      branch:     The branch
        :type       branch:     str
        :param      repo:       The repo
        :type       repo:       Repo, optional
        :param      max_count:  The maximum number of commits since HEAD
        :type       max_count:  int

        :returns:   The commits.
        :rtype:     list of Commits objects
        """
        commits = list()

        this_repo = self.get_valid_repo(repo=repo)

        if this_repo is not None:
            if max_count is None:
                commits = list(this_repo.iter_commits(rev=branch))
            else:
                commits = list(this_repo.iter_commits(rev=branch,
                                                      max_count=max_count))

        return commits

    def get_tags_of_branch(self,
                           branch: str,
                           repo=None,
                           max_count: int = None) -> List[TagReference]:
        """
        Get the tags of a branch sorted by committed datetime.

        :param      branch:     The branch
        :type       branch:     str
        :param      repo:       The repo
        :type       repo:       Repo, optional
        :param      max_count:  The maximum number of commits since HEAD
        :type       max_count:  int, optional

        :returns:   The tags on the branch.
        :rtype:     list
        """
        tags_of_branch = list()

        this_repo = self.get_valid_repo(repo=repo)

        if this_repo is not None:
            commits_of_branch = self.get_commits(branch=branch,
                                                 max_count=max_count)
            all_tags = self.get_all_tags()

            for tag in all_tags:
                if tag.commit in commits_of_branch:
                    tags_of_branch.append(tag)

        return tags_of_branch

    def convert_string_to_commit_obj(self,
                                     commits: List[str],
                                     repo=None) -> List[Commit]:
        """
        Try to convert a list of strings to commit objects, if available.

        The commit SHA is usually given as a string by the user.
        To use the commit content later on, commit objects are required.

        Individual elements are None on error

        :param      commits:  The commits
        :type       commits:  list
        :param      repo:     The repo
        :type       repo:     Repo, optional

        :returns:   The commit objects.
        :rtype:     list
        """
        commit_objs = [None] * len(commits)

        this_repo = self.get_valid_repo(repo=repo)

        if this_repo is not None:
            for idx, ele in enumerate(commits):
                self.logger.debug('Check {} at idx {}'.format(ele, idx))
                try:
                    if isinstance(ele, str):
                        commit_objs[idx] = this_repo.commit(ele)
                        self.logger.debug('Converted to commit object')
                    elif isinstance(ele, Commit):
                        self.logger.debug('Is already commit object')
                        commit_objs[idx] = ele
                except BadObject as bad_object:
                    # use warning instead of exception to not raise it automatically
                    self.logger.warning(bad_object)
                except BadName as bad_name:
                    # use warning instead of exception to not raise it automatically
                    self.logger.warning('HEX SHA not found: {}'.format(bad_name))

        return commit_objs

    def parse_git_informations(self,
                               repo_path: str = None,
                               repo_obj: Repo = None) -> bool:
        """
        Collect git informations.

        :param      repo_path:  Path to the git repository with a .git folder
        :type       repo_path:  str
        :param      repo_obj:   Git repo object
        :type       repo_obj:   Repo

        :returns:   Result of parsing.
        :rtype:     bool
        """
        by_object = False
        by_path = False

        if repo_path is not None:
            # collect informations by this path
            by_path = True
        if repo_obj is not None:
            # collect informations by this object
            by_object = True

        if not by_path and not by_object:
            self.logger.error('Either a path or a Repo object has to be given')
            return False

        if by_object and isinstance(repo_obj, Repo):
            # looks like a valid Repo object
            repo = repo_obj
        else:
            if by_path and isinstance(repo_path, str):
                # looks like a valid path
                repo = self.get_valid_repo(repo=repo_path)
            else:
                self.logger.error('Both string path and repo object are invalid')
                return False

        # a given path is rated higher than a given object
        if by_path and isinstance(repo_path, str):
            # looks like a valid path
            repo = self.get_valid_repo(repo=repo_path)
        else:
            if by_object and isinstance(repo_obj, Repo):
                # looks like a valid Repo object
                repo = repo_obj

        head_commit = repo.head.commit

        committed_date = head_commit.committed_date
        # 1620041410
        self.logger.debug('committed_date: {}'.format(committed_date))

        commit_message = head_commit.message.rstrip()
        # Hotfix: missed to replace some config for apply
        self.logger.debug('commit_message: {}'.format(commit_message))

        committer = '{}'.format(head_commit.committer)
        # Jonas Scharpf
        self.logger.debug('committer: {}'.format(committer))

        hex_sha = head_commit.hexsha
        # a0b7719a3c96001a83a5efefc9ed53dbda85fff6
        self.logger.debug('hex_sha: {}'.format(hex_sha))

        hex_sha_short = head_commit.hexsha[0:11]
        # a0b7719a3c9
        self.logger.debug('hex_sha_short: {}'.format(hex_sha_short))

        try:
            reference = '{}'.format(repo.head.reference)
            # bugfix/some-branch-name
        except TypeError as e:
            self.logger.debug('HEAD is detached')
            reference = head_commit.hexsha
            # a0b7719a3c96001a83a5efefc9ed53dbda85fff6
        self.logger.debug('reference: {}'.format(reference))

        repo_remotes = ', '.join([str(remote) for remote in repo.remotes])
        # origin
        self.logger.debug('repo_remotes: {}'.format(repo_remotes))

        repo_remotes_urls = ', '.join([remote.url for remote in repo.remotes])
        # ssh://git@host.com:port/path/to/repo.git
        self.logger.debug('repo_remotes_urls: {}'.format(repo_remotes_urls))

        # untracked_files_list = [file for file in repo.untracked_files]
        # [several, items]
        # self.logger.debug('untracked_files_list: {}'.format(untracked_files_list))

        is_dirty = repo.is_dirty()
        # false
        self.logger.debug('is_dirty: {}'.format(is_dirty))

        is_detached = repo.head.is_detached
        # false
        self.logger.debug('is_detached: {}'.format(is_detached))

        project_name = os.path.splitext(os.path.basename(repo_remotes_urls))[0]
        # buildsystem
        self.logger.debug('project_name: {}'.format(project_name))

        # clear dict
        self.git_dict.clear()

        self.git_dict['committed_date'] = committed_date
        self.git_dict['message'] = commit_message
        self.git_dict['committer'] = committer
        self.git_dict['sha'] = hex_sha
        self.git_dict['sha_short'] = hex_sha_short
        self.git_dict['reference'] = reference
        self.git_dict['repo_remotes'] = repo_remotes
        self.git_dict['repo_remotes_urls'] = repo_remotes_urls
        self.git_dict['is_dirty'] = is_dirty
        self.git_dict['is_detached'] = is_detached
        self.git_dict['project_name'] = project_name
        # self.git_dict['untracked_files'] = untracked_files_list

        return True

    def get_git_dict(self) -> dict:
        """
        Get the git dictionary.

        Dictionary contains informations parsed by :py:func:`parse_git_informations`

        :returns:   The latest git dictionary.
        :rtype:     dictionary
        """
        return self.git_dict
