#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
MySQL wrapper

Collection of database related functions
"""

import logging
import mysql.connector
# from mysql.connector.constants import ClientFlag
from typing import List

# custom imports
from be_helpers import ModuleHelper


class MySQLWrapper(ModuleHelper):
    """docstring for MySQLWrapper"""
    def __init__(self,
                 user: str,
                 password: str,
                 host: str,
                 ssl: dict = None,
                 logger: logging.Logger = None,
                 quiet: bool = False):
        super(MySQLWrapper, self).__init__()
        if logger is None:
            logger = self.create_logger()
        self.logger = logger
        self.logger.disabled = quiet

        self._config = {
            'user': user,
            'password': password,
            'host': host
        }
        if ssl:
            self._config.update(ssl)

        self._connection = None

        self.logger.debug('MySQLWrapper init finished')

    def setup_connection(self, db_name: str) -> None:
        """
        Setup a connection to a database of MySQL instance

        :param      db_name:  The database name
        :type       db_name:  str, optional
        """
        self._config['database'] = db_name

    def connect_to_db(self, db_name: str) -> bool:
        """
        Connect to a database.

        :param      db_name:  The database name
        :type       db_name:  str

        :returns:   Result of connection
        :rtype:     bool
        """
        config = self._config
        config['database'] = db_name

        cnx = mysql.connector.connect(**config)

        if cnx:
            self.connection = cnx
            result = True

        return result

    @property
    def connection(self) -> mysql.connector.connection.MySQLConnection:
        """
        Get currently active connection

        :returns:   MySQL connection
        :rtype:     MySQL connection object
        """
        return self._connection

    @connection.setter
    def connection(self,
                   value: mysql.connector.connection.MySQLConnection) -> None:
        """
        Set connection status

        :param      value:  The connection
        :type       value:  MySQL connection object
        """
        self._connection = value

    @connection.setter
    def connect(self, value: bool) -> None:
        """
        Open or close connection to MySQL

        :param      value:  The value
        :type       value:  bool
        """
        if value:
            config = self._config
            self.connection = mysql.connector.connect(**config)
        else:
            self.disconnect()

    def disconnect(self) -> None:
        """Disconnect from MySQL, wrapper around @see connect."""
        self.close_connection()

    def create_db(self, db_name: str) -> None:
        """
        Create a database.

        :param      db_name:  The database name
        :type       db_name:  str
        """
        sql = '''CREATE DATABASE IF NOT EXISTS {}'''.format(db_name)

        self.logger.debug('Create database with: {}'.format(sql))
        self.execute_sql_query(sql_query=sql)

    def create_table(self,
                     table_name: str,
                     column_dict: dict,
                     db_name: str = None) -> None:
        """
        Create a table.

        :param      table_name:   The table name
        :type       table_name:   str
        :param      column_dict:  The column dictionary
        :type       column_dict:  dict
        :param      db_name:      The database to create the table in
        :type       db_name:      str, optional
        """
        columns = ', '.join('{} {}'.format(key, val)
                            for key, val in column_dict.items())

        if db_name:
            table = '{db_name}.{table_name}'.format(db_name=db_name,
                                                    table_name=table_name)
        else:
            table = '{table_name}'.format(table_name=table_name)

        sql = '''CREATE TABLE IF NOT EXISTS {table} ({columns})'''.format(
            table=table,
            columns=columns)

        self.logger.debug('Create table with: {}'.format(sql))
        self.execute_sql_query(sql_query=sql)

    def insert_content_into_table(self,
                                  table_name: str,
                                  content_dict: dict,
                                  db_name: str = None) -> None:
        """
        Insert data into table

        :param      table_name:    The table name
        :type       table_name:    str
        :param      content_dict:  The content dictionary
        :type       content_dict:  dict
        :param      db_name:       The database of the table
        :type       db_name:       str, optional
        """
        columns_names = ""
        columns_data = ""
        for key, val in content_dict.items():
            if not key.endswith('_HUMAN'):
                if columns_names:
                    columns_names += ','
                columns_names += key

                if isinstance(val, bool):
                    data = int(val)
                else:
                    data = val

                if columns_data:
                    columns_data += ','
                columns_data += "'{}'".format(data)

        if db_name:
            table = '{db_name}.{table_name}'.format(db_name=db_name,
                                                    table_name=table_name)
        else:
            table = '{table_name}'.format(table_name=table_name)

        sql = '''INSERT INTO {table} ({columns}) VALUES ({data})'''.format(
            table=table,
            columns=columns_names,
            data=columns_data)

        self.logger.debug('Insert data into table with: {}'.format(sql))
        self.execute_sql_query(sql_query=sql)

    def read_table_completly(self,
                             table_name: str,
                             additional_sql: str = None,
                             db_name: str = None) -> List[tuple]:
        """
        Read the complete content of a table.

        :param      table_name:      The table name
        :type       table_name:      str
        :param      additional_sql:  The additional SQL statement
        :type       additional_sql:  str
        :param      db_name:      The database of the table
        :type       db_name:      str, optional

        :returns:   Read content of table
        :rtype:     list
        """
        if db_name:
            table = '{db_name}.{table_name}'.format(db_name=db_name,
                                                    table_name=table_name)
        else:
            table = '{table_name}'.format(table_name=table_name)

        sql = '''SELECT * FROM {table}'''.format(table=table)
        if additional_sql:
            sql += ' {}'.format(additional_sql)

        self.logger.debug('Read complete table with: {}'.format(sql))
        content = self.execute_sql_query(sql_query=sql)
        return content

    def get_table_size(self, table_name: str, db_name: str = None) -> int:
        """
        Get the table size.

        :param      table_name:   The table name
        :type       table_name:   str
        :param      db_name:      The database of the table
        :type       db_name:      str, optional

        :returns:   The table size.
        :rtype:     int
        """
        if db_name:
            table = '{db_name}.{table_name}'.format(db_name=db_name,
                                                    table_name=table_name)
        else:
            table = '{table_name}'.format(table_name=table_name)

        sql = '''SELECT COUNT(*) FROM {table}'''.format(table=table)

        self.logger.debug('Get table size with: {}'.format(sql))
        result = self.execute_sql_query(sql_query=sql)

        if len(result) and isinstance(result[0], tuple):
            result = result[0][0]
        else:
            result = -1

        self.logger.debug('Table size is: {}'.format(result))

        return result

    def execute_sql_query(self, sql_query: str, data: str = None) -> list:
        """
        Perform a sql operation/query on a database

        :param      sql_query:  The SQL query
        :type       sql_query:  str
        :param      data:       Additional data for the call
        :type       data:       str, optional

        :returns:   Result of SQL query execution
        :rtype:     list
        """
        result = list()

        cursor = self.connection.cursor()

        try:
            if data:
                cursor.execute(sql_query, data)
            else:
                cursor.execute(sql_query)

            if sql_query.startswith("INSERT"):
                self.connection.commit()
            elif sql_query.startswith("SELECT"):
                result = cursor.fetchall()
                self.logger.debug("Operation result: {}".format(result))
        except mysql.connector.Error as e:
            self.logger.warning("Error on SQL query: {}".format(e))

        cursor.close()

        return result

    def close_connection(self) -> None:
        """Close connection to database or MySQL."""
        if self.connection:
            self.connection.close()
        else:
            self.logger.error('No active connection, call "connect" or '
                              '"connect_to_db" first')
