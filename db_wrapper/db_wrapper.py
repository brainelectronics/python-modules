#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
Database wrapper

Collection of database related functions
"""

# from .mysql_wrapper import MySQLWrapper
# from .sqlite_wrapper import SQLiteWrapper


# class DBWrapper(MySQLWrapper, SQLiteWrapper):
class DBWrapper(object):
    """docstring for DBWrapper"""
    def __init__(self):
        pass

    @staticmethod
    def generate_columns_names(registers: dict,
                               keys_req: list = ['register', 'len', 'description'],
                               field_type: str = 'text',
                               result_dict: dict = dict()) -> dict():
        """
        Generate table columns based on dictionary

        :param      registers:    The registers to create columns of
        :type       registers:    dict
        :param      keys_req:     Required keys of an element to be added to result
        :type       keys_req:     list, optional
        :param      field_type:   The field type
        :type       field_type:   str, optional
        :param      result_dict:  The result dictionary
        :type       result_dict:  dict, optional

        :returns:   Dictionary with registers keys as key and 'text' as value
        :rtype:     dict
        """
        for key, val in registers.items():
            if key not in ['META', 'CONNECTION']:
                # try to identify best fitting field type, use given on error
                if key == 'COILS':
                    field_type = 'BOOLEAN'
                elif key == 'HREGS':
                    field_type = 'INT UNSIGNED'
                elif key == 'ISTS':
                    field_type = 'BOOLEAN'
                elif key == 'IREGS':
                    field_type = 'INT UNSIGNED'
                else:
                    pass

                if isinstance(val, dict):
                    if all(x in val for x in keys_req):
                        result_dict[key] = field_type
                    else:
                        result = DBWrapper.generate_columns_names(
                            registers=val,
                            field_type=field_type,
                            keys_req=keys_req,
                            result_dict=result_dict)
                        result_dict.update(result)
            else:
                # skip meta or connection content
                pass

        return result_dict
