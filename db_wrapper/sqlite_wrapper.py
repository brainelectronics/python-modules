#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
SQLite wrapper

Collection of database related functions
"""

import logging
from pathlib import Path
import random
import sqlite3
from typing import List

# custom imports
from module_helper.module_helper import ModuleHelper


class SQLiteWrapper(ModuleHelper):
    """docstring for SQLiteWrapper"""
    def __init__(self, logger: logging.Logger = None, quiet: bool = False):
        super(SQLiteWrapper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self.repo = None
        self.git_dict = dict()

        self.logger.debug('SQLiteWrapper init finished')

    def connect_to_db(self, db_name: str) -> sqlite3.Connection:
        """
        Connect to a database.

        :param      db_name:  The database name
        :type       db_name:  str

        :returns:   SQLite3 connection
        :rtype:     SQLite3 connection object
        """
        return sqlite3.connect(db_name)

    def create_db(self,
                  db_name: str,
                  in_memory: bool) -> sqlite3.Connection:
        """
        Create a new database.

        :param      db_name:    The database name
        :type       db_name:    str
        :param      in_memory:  Flag to create database in memory only
        :type       in_memory:  bool

        :returns:   SQLite3 connection
        :rtype:     SQLite3 connection object
        """
        if in_memory:
            db_name = ':memory:'
            self.logger.debug('Create database "{}" in memory'.format(db_name))
        else:
            name = self.format_timestamp(timestamp=self.get_unix_timestamp(),
                                         format="%m-%d-%Y-%H%M%S")
            db_name = '{}-{}.sqlite3'.format(db_name, name)

            if Path(db_name).exists():
                self.logger.info('Database "{}" already exists, use it'.
                                 format(db_name))
            else:
                self.logger.debug('No database named "{}" exists, create it'.
                                  format(db_name))

        return self.connect_to_db(db_name=db_name)

    def create_table(self,
                     db: sqlite3.Connection,
                     table_name: str,
                     column_dict: dict) -> None:
        """
        Create a table.

        :param      db:           The database to create the table in
        :type       db:           SQLite3 connection object
        :param      table_name:   The table name
        :type       table_name:   str
        :param      column_dict:  The column dictionary
        :type       column_dict:  dict
        """
        # cur.execute('''CREATE TABLE MyTableName
        #                (ColumnName ColumType, ColumnName ColumType)''',
        #             column_dict)
        # create string from all key value pairs of the dict
        columns = ', '.join('{} {}'.format(key, val)
                            for key, val in column_dict.items())
        sql = '''CREATE TABLE {name} ({columns})'''.format(name=table_name,
                                                           columns=columns)

        self.logger.debug('Create table with: {}'.format(sql))
        self.execute_sql_query(db=db, sql_query=sql)

    def execute_sql_query(self,
                          db: sqlite3.Connection,
                          sql_query: str,
                          data: str = None) -> None:
        """
        Perform a sql operation/query on a database

        :param      db:         The database to perform the operation on
        :type       db:         SQLite3 connection object
        :param      sql_query:  The SQL query
        :type       sql_query:  str
        :param      data:       Additional data for the call
        :type       data:       str
        """
        cur = db.cursor()

        self.logger.debug('Execute SQL query: {} with {}'.format(sql_query,
                                                                 data))

        # execute the query
        if data:
            cur.execute(sql_query, data)
        else:
            cur.execute(sql_query)

        # Save (commit) the changes
        db.commit()

    def insert_content_into_table(self,
                                  db: sqlite3.Connection,
                                  content_dict: dict,
                                  table_name: str) -> None:
        """
        Insert data into table

        :param      db:            The database to perform the operation on
        :type       db:            SQLite3 connection object
        :param      content_dict:  The content dictionary
        :type       content_dict:  dict
        :param      table_name:    The table name
        :type       table_name:    str
        """
        # cur.execute('''INSERT INTO stocks VALUES
        #                 ('2006-01-05','BUY','RHAT',100,35.14)''')
        # cur.execute('''INSERT INTO 'stocks' VALUES
        #                 (:time_val,'BUY','RHAT',:qty_val, :price_val)''',
        #             content_dict)

        data = ','.join(':{}'.format(key) for key, val in content_dict.items())
        sql = '''INSERT INTO {table_name} VALUES
                 ({data})'''.format(table_name=table_name, data=data)

        self.execute_sql_query(db=db, sql_query=sql, data=content_dict)

    def read_table_completly(self,
                             db: sqlite3.Connection,
                             table_name: str,
                             additional_sql: str = None) -> List[tuple]:
        """
        Read the complete content of a table.

        :param      db:              The database to perform the operation on
        :type       db:              SQLite3 connection object
        :param      table_name:      The table name
        :type       table_name:      str
        :param      additional_sql:  The additional sql
        :type       additional_sql:  str

        :returns:   Read content of table
        :rtype:     list
        """
        cur = db.cursor()

        sql = 'SELECT * FROM {table_name}'.format(table_name=table_name)
        if additional_sql:
            sql += ' {}'.format(additional_sql)
        self.logger.debug('Read DB SQL query: {}'.format(sql))

        content = list()
        for row in cur.execute(sql):
            content.append(row)

        return content

    def close_connection(self, db: sqlite3.Connection) -> None:
        """
        Close connection to database.

        Ensure any changes have been committed or they will be lost.

        :param      db:              The database to close
        :type       db:              SQLite3 connection object
        """
        db.close()

    def backup_db_to_file(self,
                          db: sqlite3.Connection,
                          backup_name: str) -> None:
        """
        Backup database in file.

        :param      db:           The database to backup
        :type       db:           SQLite3 connection object
        :param      backup_name:  The backup name
        :type       backup_name:  str
        """
        # create a new database to backup the others database content to
        backup_db = self.connect_to_db(db_name='{}.sqlite3'.
                                       format(backup_name))

        # backup old database to new created one
        db.backup(backup_db)

        self.close_connection(db=db)
        self.close_connection(db=backup_db)

    def get_random_content(self, column_dict: dict) -> dict:
        """
        Generate random content for all columns of a table

        :param      column_dict:  The column dictionary
        :type       column_dict:  dict

        :returns:   The random content.
        :rtype:     dict
        """
        content_dict = dict()
        for key, val in column_dict.items():
            val = val.upper()
            if val == 'TEXT':
                # use a string
                content = self.get_random_string(length=random.randint(1, 10))
            elif val == 'REAL':
                # use a float
                content = round(random.uniform(1, 100), 2)
            elif val == 'INTEGER':
                # use a signed integer
                content = random.randint(1, 100)
            elif val == 'DATETIME':
                # use current timestamp
                now = self.get_unix_timestamp()
                content = self.format_timestamp(timestamp=now,
                                                format="%m-%d-%Y %H:%M:%S")
            elif val == 'BOOLEAN':
                # use bool
                content = bool(random.getrandbits(1))
            elif val == 'NUMERIC':
                # pass
                self.logger.warning('Numeric random content not supported')
            elif val == 'BLOB':
                self.logger.warning('Blob random content not supported')
            else:
                self.logger.error('{} random content not supported'.
                                  format(val))

            content_dict[key] = content

        self.logger.debug('Generated random content: {}'.format(content_dict))

        return content_dict
