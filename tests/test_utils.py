# -*- coding: utf-8 -*-

from mongo_connector.doc_managers import utils

from bson.objectid import ObjectId
from bson.tz_util import utc

from datetime import datetime
from calendar import timegm

from unittest import TestCase, main


class TestPostgreSQLUtils(TestCase):
    def test_extract_creation_date(self):
        now = datetime.now()

        doc = {
            '_id': ObjectId.from_datetime(now)
        }

        got = utils.extract_creation_date(doc, '_id')
        expected = now

        if expected.utcoffset() is not None:
            expected -= expected.utcoffset()

        expected = timegm(expected.timetuple())
        expected = datetime.fromtimestamp(expected, utc)

        self.assertEqual(expected, got)

        got = utils.extract_creation_date({}, '_id')
        self.assertIsNone(got)

    def test_is_collection_mapped(self):
        doc = {
            'db': {
                'col': {
                    'field': 'val'
                }
            }
        }

        got = utils.is_collection_mapped(doc, 'db.col.field')
        self.assertTrue(got)

        doc = {
            'db': {
                'col': {}
            }
        }

        got = utils.is_collection_mapped(doc, 'db.col.field')
        self.assertFalse(got)

    def test_is_field_mapped(self):
        mapping = {
            'db': {
                'col': {
                    'field': 'val'
                }
            }
        }

        got = utils.is_field_mapped(mapping, 'db', 'col', 'field')
        self.assertTrue(got)

        mapping = {
            'db': {
                'col': {}
            }
        }

        got = utils.is_field_mapped(mapping, 'db', 'col', 'field')
        self.assertFalse(got)

    def test_get_nested_field_from_document(self):
        got = utils.get_nested_field_from_document(None, None)
        self.assertIsNone(got)

        doc = {}
        got = utils.get_nested_field_from_document(doc, 'foo')
        self.assertIsNone(got)

        doc = {'foo': 'bar'}
        got = utils.get_nested_field_from_document(doc, 'foo')
        self.assertEqual(got, 'bar')

        doc = {
            'foo': {}
        }
        got = utils.get_nested_field_from_document(doc, 'foo.bar.baz')
        self.assertIsNone(got)

        doc = {
            'foo': {
                'bar': 'baz'
            }
        }
        got = utils.get_nested_field_from_document(doc, 'foo.bar')
        self.assertEqual(got, 'baz')

    def test_get_fields_of_type(self):
        mapping = {}
        got = utils.get_fields_of_type(mapping, 'db', 'col', {}, 'TEXT')
        self.assertEqual(got, [])

        mapping = {'db': {}}
        got = utils.get_fields_of_type(mapping, 'db', 'col', {}, 'TEXT')
        self.assertEqual(got, [])

        mapping = {
            'db': {
                'col': {}
            }
        }
        got = utils.get_fields_of_type(mapping, 'db', 'col', {}, 'TEXT')
        self.assertEqual(got, [])

        mapping = {
            'db': {
                'col': {
                    'field1': {'field2': {}},
                    'field1.field2': {'type': 'TEXT'}
                }
            }
        }
        got = utils.get_fields_of_type(mapping, 'db', 'col', {}, 'TEXT')
        self.assertEqual(got, [])

        doc = {'field1': {'field2': 'val'}}
        got = utils.get_fields_of_type(mapping, 'db', 'col', doc, 'TEXT')
        self.assertEqual(got, ['field1.field2'])

    def test_get_array_fields(self):
        mapping = {
            'db': {
                'col': {
                    'field1': {'type': '_ARRAY'}
                }
            }
        }
        got = utils.get_array_fields(mapping, 'db', 'col', {})
        self.assertEqual(got, [])

        doc = {'field1': [{}]}
        got = utils.get_array_fields(mapping, 'db', 'col', doc)
        self.assertEqual(got, ['field1'])

    def test_get_array_of_scalar_fields(self):
        mapping = {
            'db': {
                'col': {
                    'field': {'type': '_ARRAY_OF_SCALARS'}
                }
            }
        }
        got = utils.get_array_of_scalar_fields(mapping, 'db', 'col', {})
        self.assertEqual(got, [])

        doc = {'field': [1, 2, 3]}
        got = utils.get_array_of_scalar_fields(mapping, 'db', 'col', doc)
        self.assertEqual(got, ['field'])

    def test_get_any_array_fields(self):
        mapping = {
            'db': {
                'col': {
                    'field1': {'type': '_ARRAY'},
                    'field2': {'type': '_ARRAY_OF_SCALARS'}
                }
            }
        }
        got = utils.get_any_array_fields(mapping, 'db', 'col', {})
        self.assertEqual(got, [])

        doc = {'field1': [{}]}
        got = utils.get_any_array_fields(mapping, 'db', 'col', doc)
        self.assertEqual(got, ['field1'])

        doc = {'field2': [1, 2, 3]}
        got = utils.get_any_array_fields(mapping, 'db', 'col', doc)
        self.assertEqual(got, ['field2'])

        doc = {
            'field1': [{}],
            'field2': [1, 2, 3]
        }
        got = utils.get_any_array_fields(mapping, 'db', 'col', doc)
        self.assertIn('field1', got)
        self.assertIn('field2', got)

    def test_is_array_field(self):
        mapping = {
            'db': {
                'col': {
                    'field': {
                        'subfield1': {},
                        'subfield2': {}
                    },
                    'field.subfield1': {'type': '_ARRAY'},
                    'field.subfield2': {'type': 'TEXT'}
                }
            }
        }

        got = utils.is_array_field(mapping, 'db', 'col', 'field.subfield1')
        self.assertTrue(got)

        got = utils.is_array_field(mapping, 'db', 'col', 'field.subfield2')
        self.assertFalse(got)

        got = utils.is_array_field(mapping, 'db', 'col', 'field.subfield3')
        self.assertFalse(got)

    def test_map_value_to_pgsql(self):
        _id = ObjectId('507f1f77bcf86cd799439011')
        got = utils.map_value_to_pgsql(_id)
        self.assertTrue(isinstance(got, str))

        _id = '507f1f77bcf86cd799439011'
        got = utils.map_value_to_pgsql(_id)
        self.assertTrue(isinstance(got, str))

    def test_db_and_collection(self):
        ns = 'db.col'
        got = utils.db_and_collection(ns)

        self.assertEqual(len(got), 2)
        self.assertEqual(got, ['db', 'col'])

    def test_get_array_field_collection(self):
        mapping = {
            'db': {
                'col': {
                    'field': {
                        'dest': 'column'
                    }
                }
            }
        }
        got = utils.get_array_field_collection(mapping, 'db', 'col', 'field')
        self.assertEqual(got, 'column')

    def test_get_foreign_key(self):
        mapping = {
            'db': {
                'col': {
                    'field1': {
                        'fk': 'field2'
                    }
                }
            }
        }
        got = utils.get_foreign_key(mapping, 'db', 'col', 'field1')
        self.assertEqual(got, 'field2')


if __name__ == '__main__':
    main()
