# -*- coding: utf-8 -*-

from unittest import TestCase, main
from mock import MagicMock, call

from mongo_connector.doc_managers import sql, utils
from bson.objectid import ObjectId

from collections import OrderedDict
from datetime import datetime


class TestPostgreSQL(TestCase):
    def test_to_sql_list(self):
        items = ['1', '2']
        got = sql.to_sql_list(items)
        self.assertEqual(got, ' (1,2) ')

    def test_sql_table_exists(self):
        cursor = MagicMock()
        cursor.fetchone.return_value = [1]
        got = sql.sql_table_exists(cursor, 'table')

        self.assertEqual(len(cursor.execute.call_args[0]), 1)
        self.assertIn('table', cursor.execute.call_args[0][0])
        self.assertEqual(got, 1)

    def test_sql_delete_rows(self):
        cursor = MagicMock()
        sql.sql_delete_rows(cursor, 'table')
        cursor.execute.assert_called_with('DELETE FROM table')

    def test_sql_delete_rows_where(self):
        cursor = MagicMock()
        sql.sql_delete_rows_where(cursor, 'table', 'id = 1')
        cursor.execute.assert_called_with('DELETE FROM table WHERE id = 1')

    def test_sql_drop_table(self):
        cursor = MagicMock()
        sql.sql_drop_table(cursor, 'table')
        cursor.execute.assert_called_with('DROP TABLE table')

    def test_sql_create_table(self):
        cursor = MagicMock()
        columns = [
            'id INTEGER',
            'field TEXT'
        ]
        sql.sql_create_table(cursor, 'table', columns)
        cursor.execute.assert_called_with(
            'CREATE TABLE table  (id INTEGER,field TEXT) '
        )

    def test_sql_bulk_insert(self):
        cursor = MagicMock()

        mapping = {
            'db': {
                'col': OrderedDict([
                    ('pk', '_id'),
                    ('field1', {
                        'type': 'TEXT',
                        'dest': 'field1'
                    }),
                    ('field2.subfield', {
                        'type': 'TEXT',
                        'dest': 'field2_subfield'
                    })
                ])
            }
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col', [])

        cursor.execute.assert_not_called()

        doc = {
            '_id': 'foo',
            'field1': 'val'
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col', [doc])

        cursor.execute.assert_called_with(
            "INSERT INTO col (_creationDate,field1,field2_subfield) VALUES (NULL,'val',NULL)"
        )

        doc = {
            '_id': 'foo',
            'field1': 'val1',
            'field2': {
                'subfield': 'val2'
            }
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col', [doc])
        cursor.execute.assert_called_with(
            "INSERT INTO col (_creationDate,field1,field2_subfield) VALUES (NULL,'val1','val2')"
        )

    def test_sql_bulk_insert_array(self):
        cursor = MagicMock()

        mapping = {
            'db': {
                'col1': {
                    'pk': '_id',
                    '_id': {
                        'type': 'INT'
                    },
                    'field1': {
                        'dest': 'col_array',
                        'type': '_ARRAY',
                        'fk': 'id_col1'
                    },
                    'field2': {
                        'dest': 'col_scalar',
                        'fk': 'id_col1',
                        'valueField': 'scalar',
                        'type': '_ARRAY_OF_SCALARS'
                    }
                },
                'col_array': {
                    'pk': '_id',
                    'field1': {
                        'dest': 'field1',
                        'type': 'TEXT'
                    },
                    'id_col1': {
                        'dest': 'id_col1',
                        'type': 'INT'
                    }
                },
                'col_scalar': {
                    'pk': '_id',
                    'scalar': {
                        'dest': 'scalar',
                        'type': 'INT'
                    },
                    'id_col1': {
                        'dest': 'id_col1',
                        'type': 'INT'
                    }
                }
            }
        }

        doc = {
            '_id': 1,
            'field1': [
                {'field1': 'val'}
            ],
            'field2': [1, 2, 3]
        }

        sql.sql_bulk_insert(cursor, mapping, 'db.col1', [doc, {}])

        cursor.execute.assert_has_calls([
            call('INSERT INTO col_array (_creationDate,id_col1,field1) VALUES (NULL,1,\'val\')'),
            call('INSERT INTO col_scalar (_creationDate,scalar,id_col1) VALUES (NULL,1,1),(NULL,2,1),(NULL,3,1)'),
            call('INSERT INTO col1 (_creationDate) VALUES (NULL)')
        ])

    def test_sql_insert(self):
        mapping = {
            'db': {
                'col': {
                    'pk': '_id',
                    '_id': {
                        'type': 'INT',
                        'dest': '_id'
                    },
                    'field': {
                        'type': 'TEXT',
                        'dest': 'field'
                    }
                }
            }
        }
        cursor = MagicMock()
        now = datetime.now()

        # Use ordereddict to ensure correct order in generated SQL request
        doc = OrderedDict()
        doc['_id'] = ObjectId.from_datetime(now)
        doc['field'] = 'val'

        sql.sql_insert(cursor, 'table', doc, mapping, 'db', 'col')

        doc['_creationDate'] = utils.extract_creation_date(doc, '_id')

        cursor.execute.assert_called_with(
            'INSERT INTO table  (_id,field,_creationDate)  VALUES  (%(_id)s,%(field)s,%(_creationDate)s)  ON CONFLICT (_id) DO UPDATE SET  (_id,field,_creationDate)  =  (%(_id)s,%(field)s,%(_creationDate)s) ',
            doc
        )

        doc = {
            'field': 'val'
        }

        sql.sql_insert(cursor, 'table', doc, mapping, 'db', 'col')

        cursor.execute.assert_called_with(
            'INSERT INTO table  (field)  VALUES  (%(field)s) ',
            doc
        )


if __name__ == '__main__':
    main()
