# -*- coding: utf-8 -*-

from unittest import TestCase, main
from mock import MagicMock, patch, mock_open, call
from time import time
import json

from mongo_connector.doc_managers import postgresql_manager


MAPPING_RAW = '''{
    "db": {
        "col": {
            "pk": "_id",
            "_id": {
                "type": "INT"
            },
            "field1": {
                "type": "TEXT"
            },
            "field2": {
                "type": "_ARRAY",
                "dest": "col_field2",
                "fk": "id_col"
            }
        },
        "col_field2": {
            "pk": "_id",
            "_id": {
                "type": "INT"
            },
            "id_col": {
                "type": "INT"
            },
            "subfield1": {
                "type": "TEXT"
            },
            "subfield2": {
                "type": "_ARRAY_OF_SCALARS",
                "dest": "col_field2_subfield2",
                "fk": "id_col_field2",
                "valueField": "scalar"
            }
        },
        "col_field2_subfield2": {
            "pk": "_id",
            "_id": {
                "type": "INT"
            },
            "id_col_field2": {
                "type": "INT"
            },
            "scalar": {
                "type": "INT"
            }
        }
    }
}'''

MAPPING = {
    'db': {
        'col': {
            'pk': '_id',
            '_id': {
                'dest': '_id',
                'type': 'INT'
            },
            'field1': {
                'dest': 'field1',
                'type': 'TEXT'
            },
            'field2': {
                'dest': 'col_field2',
                'type': '_ARRAY',
                'fk': 'id_col'
            }
        },
        'col_field2': {
            'pk': '_id',
            '_id': {
                'dest': '_id',
                'type': 'INT'
            },
            'id_col': {
                'dest': 'id_col',
                'type': 'INT'
            },
            'subfield1': {
                'dest': 'subfield1',
                'type': 'TEXT'
            },
            'subfield2': {
                'dest': 'col_field2_subfield2',
                'type': '_ARRAY_OF_SCALARS',
                'fk': 'id_col_field2',
                'valueField': 'scalar'
            }
        },
        'col_field2_subfield2': {
            'pk': '_id',
            '_id': {
                'dest': '_id',
                'type': 'INT'
            },
            'id_col_field2': {
                'dest': 'id_col_field2',
                'type': 'INT'
            },
            'scalar': {
                'dest': 'scalar',
                'type': 'INT'
            }
        }
    }
}


class TestPostgreSQLManager(TestCase):
    def setUp(self):
        self.psql_module_patcher = patch(
            'mongo_connector.doc_managers.postgresql_manager.psycopg2'
        )
        self.mongoclient_patcher = patch(
            'mongo_connector.doc_managers.postgresql_manager.MongoClient'
        )
        self.builtin_open_patcher = patch(
            'mongo_connector.doc_managers.postgresql_manager.open',
            mock_open(read_data=MAPPING_RAW),
            create=True
        )
        self.ospath_patcher = patch(
            'mongo_connector.doc_managers.postgresql_manager.os.path'
        )
        self.logging_patcher = patch(
            'mongo_connector.doc_managers.postgresql_manager.logging'
        )
        self.validate_mapping_patcher = patch(
            'mongo_connector.doc_managers.postgresql_manager.validate_mapping'
        )

        self.psql_module = self.psql_module_patcher.start()
        self.mongoclient = self.mongoclient_patcher.start()
        self.builtin_open = self.builtin_open_patcher.start()
        self.ospath = self.ospath_patcher.start()
        self.logging = self.logging_patcher.start()
        self.validate_mapping = self.validate_mapping_patcher.start()

    def tearDown(self):
        self.psql_module_patcher.stop()
        self.mongoclient_patcher.stop()
        self.builtin_open_patcher.stop()
        self.ospath_patcher.stop()
        self.logging_patcher.stop()
        self.validate_mapping_patcher.stop()


class TestManagerInitialization(TestPostgreSQLManager):
    def test_invalid_configuration(self):
        with self.assertRaises(postgresql_manager.InvalidConfiguration):
            postgresql_manager.DocManager('url')

        self.ospath.isfile.return_value = False

        with self.assertRaises(postgresql_manager.InvalidConfiguration):
            postgresql_manager.DocManager('url', mongoUrl='murl')

        self.psql_module.connect.assert_called_with('url')
        self.mongoclient.assert_called_with('murl')
        self.ospath.isfile.assert_called_with('mappings.json')
        self.validate_mapping.assert_not_called()

    def test_valid_configuration(self):
        pconn = MagicMock()
        self.psql_module.connect.return_value = pconn
        cursor = MagicMock()
        pconn.cursor.return_value.__enter__.return_value = cursor

        self.ospath.isfile.return_value = True

        docmgr = postgresql_manager.DocManager('url', mongoUrl='murl')

        self.psql_module.connect.assert_called_with('url')
        self.mongoclient.assert_called_with('murl')
        self.ospath.isfile.assert_called_with('mappings.json')
        self.validate_mapping.assert_called_with(MAPPING)

        self.assertEqual(
            docmgr.mappings,
            MAPPING
        )

        cursor.execute.assert_has_calls([
            call('DROP TABLE col'),
            call(
                'CREATE TABLE col  (_creationdate TIMESTAMP,_id INT CONSTRAINT COL_PK PRIMARY KEY,field1 TEXT ) '
            ),
            call(
                'CREATE TABLE col_field2  (_creationdate TIMESTAMP,_id INT CONSTRAINT COL_FIELD2_PK PRIMARY KEY,id_col INT ,subfield1 TEXT ) '
            ),
            call(
                'CREATE INDEX idx_col__creation_date ON col (_creationdate DESC)'
            )
        ], any_order=True)

        pconn.commit.assert_called()


class TestManager(TestPostgreSQLManager):
    def setUp(self):
        super(TestManager, self).setUp()

        self.mconn = MagicMock()
        self.mdb = MagicMock()
        self.mcol = MagicMock()

        self.mongoclient.return_value = self.mconn
        self.mconn.__getitem__.return_value = self.mdb
        self.mdb.__getitem__.return_value = self.mcol

        self.pconn = MagicMock()
        self.psql_module.connect.return_value = self.pconn
        self.cursor = MagicMock()
        self.cursor.__enter__.return_value = self.cursor
        self.pconn.cursor.return_value = self.cursor

        self.ospath.isfile.return_value = True

        self.docmgr = postgresql_manager.DocManager(
            'url',
            mongoUrl='murl',
            chunk_size=2
        )

    def test_document_by_id(self):
        expected = {'foo': 'bar'}
        self.mcol.find_one.return_value = expected

        got = self.docmgr.get_document_by_id('db', 'col', 1)

        self.mconn.__getitem__.assert_called_with('db')
        self.mdb.__getitem__.assert_called_with('col')
        self.mcol.find_one.assert_called_with({'_id': 1})

        self.assertEqual(got, expected)

    def test_upsert(self):
        doc = {
            '_id': 1,
            'field1': 'val1',
            'field2': [
                {
                    'subfield1': 'subval1'
                }
            ]
        }
        now = time()

        self.docmgr.upsert(doc, 'db.col', now)

        self.cursor.execute.assert_has_calls([
            call(
                'INSERT INTO col_field2  (id_col,subfield1)  VALUES  (%(id_col)s,%(subfield1)s) ',
                {'id_col': 1, 'subfield1': 'subval1'}
            ),
            call(
                'INSERT INTO col  (_id,field1)  VALUES  (%(_id)s,%(field1)s)  ON CONFLICT (_id) DO UPDATE SET  (_id,field1)  =  (%(_id)s,%(field1)s) ',
                {'_id': 1, 'field1': 'val1'}
            )
        ], any_order=True)
        self.pconn.commit.assert_called()

    def test_bulk_upsert(self):
        doc1 = {
            '_id': 1,
            'field1': 'val1',
            'field2': [
                {'subfield1': 'subval1'}
            ]
        }
        doc2 = {
            '_id': 2,
            'field1': 'val2',
            'field2': [
                {'subfield1': 'subval2'}
            ]
        }
        doc3 = {
            '_id': 3,
            'field1': 'val3',
            'field2': [
                {'subfield1': 'subval3'}
            ]
        }
        now = time()

        self.docmgr.bulk_upsert([doc1, doc2, doc3], 'db.col', now)

        self.cursor.execute.assert_has_calls([
            call(
                "INSERT INTO col_field2 (_creationDate,_id,id_col,subfield1) VALUES (NULL,NULL,1,'subval1')"
            ),
            call(
                "INSERT INTO col_field2 (_creationDate,_id,id_col,subfield1) VALUES (NULL,NULL,2,'subval2')"
            ),
            call(
                "INSERT INTO col (_creationDate,_id,field1) VALUES (NULL,1,'val1'),(NULL,2,'val2')"
            ),
            call(
                "INSERT INTO col_field2 (_creationDate,_id,id_col,subfield1) VALUES (NULL,NULL,3,'subval3')"
            ),
            call(
                "INSERT INTO col (_creationDate,_id,field1) VALUES (NULL,3,'val3')"
            )
        ], any_order=True)
        self.pconn.commit.assert_called()

    def test_update(self):
        doc_id = 1
        doc = {
            '_id': doc_id,
            'field1': 'val1',
            'field2': [
                {'subfield1': 'subval1'}
            ]
        }
        now = time()

        self.mcol.find_one.return_value = doc

        self.docmgr.update(doc_id, {}, 'db.col', now)

        self.mconn.__getitem__.assert_called_with('db')
        self.mdb.__getitem__.assert_called_with('col')
        self.mcol.find_one.assert_called_with({'_id': 1})

        self.cursor.execute.assert_has_calls([
            call(
                'DELETE FROM col_field2 WHERE id_col = 1'
            ),
            call(
                'INSERT INTO col_field2  (id_col,subfield1)  VALUES  (%(id_col)s,%(subfield1)s) ',
                {'id_col': 1, 'subfield1': 'subval1'}
            ),
            call(
                'INSERT INTO col  (_id,field1)  VALUES  (%(_id)s,%(field1)s)  ON CONFLICT (_id) DO UPDATE SET  (_id,field1)  =  (%(_id)s,%(field1)s) ',
                {'_id': 1, 'field1': 'val1'}
            )
        ], any_order=True)
        self.pconn.commit.assert_called()

    def test_remove(self):
        now = time()
        self.docmgr.remove(1, 'db.col', now)

        self.cursor.execute.assert_called_with(
            'DELETE from col WHERE _id = \'1\';'
        )
        self.pconn.commit.assert_called()


if __name__ == '__main__':
    main()
