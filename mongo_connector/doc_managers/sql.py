# coding: utf8

import logging
import re
import unicodedata

from psycopg2._psycopg import AsIs

from mongo_connector.doc_managers.mappings import (
    get_mapped_document,
    get_transformed_value,
    get_transformed_document
)

from mongo_connector.doc_managers.utils import (
    extract_creation_date,
    get_array_fields,
    db_and_collection,
    get_array_of_scalar_fields,
    ARRAY_OF_SCALARS_TYPE,
    ARRAY_TYPE,
    get_nested_field_from_document
)


LOG = logging.getLogger(__name__)


all_chars = (unichr(i) for i in xrange(0x10000))
control_chars = ''.join(c for c in all_chars if unicodedata.category(c) == 'Cc')
control_char_re = re.compile('[%s]' % re.escape(control_chars))


def to_sql_list(items):
    return ' ({0}) '.format(','.join(items))


def sql_table_exists(cursor, table):
    cursor.execute(""
                   "SELECT EXISTS ("
                   "        SELECT 1 "
                   "FROM   information_schema.tables "
                   "WHERE  table_schema = 'public' "
                   "AND    table_name = '" + table.lower() + "' );")
    return cursor.fetchone()[0]


def sql_delete_rows(cursor, table):
    cursor.execute(u"DELETE FROM {0}".format(table.lower()))


def sql_delete_rows_where(cursor, table, where_clause):
    cursor.execute(u"DELETE FROM {0} WHERE {1}".format(table.lower(), where_clause))


def sql_drop_table(cursor, tableName):
    sql = u"DROP TABLE {0}".format(tableName.lower())
    cursor.execute(sql)

def sql_create_table(cursor, tableName, columns):
    sql = u"CREATE TABLE {0} {1}".format(tableName.lower(), to_sql_list(columns))
    cursor.execute(sql)


def sql_bulk_insert(cursor, mappings, namespace, documents):
    if not documents:
        return

    db, collection = db_and_collection(namespace)

    primary_key = mappings[db][collection]['pk']
    mapped_fields = {}
    keys = []
    values = []

    for _, mapping in mappings[db][collection].iteritems():

        if 'dest' in mapping and mapping['type'] not in (
            ARRAY_TYPE,
            ARRAY_OF_SCALARS_TYPE
        ):
            mapped_fields[mapping['dest']] = mapping
            keys.append(mapping['dest'])

    for document in documents:
        mapped_document = get_mapped_document(mappings, document, namespace)
        document_values = [
            to_sql_value(
                extract_creation_date(
                    mapped_document,
                    mappings[db][collection]['pk']
                )
            )
        ]

        if not mapped_document:
            break

        for key in keys:
            if key in mapped_document:
                val = get_transformed_value(
                    mapped_fields[key],
                    mapped_document, key
                )
                document_values.append(to_sql_value(val))

            else:
                document_values.append(to_sql_value(None))
        values.append(u"({0})".format(u','.join(document_values)))

        insert_document_arrays(collection, cursor, db, document, mapped_document, mappings, primary_key)
        insert_scalar_arrays(collection, cursor, db, document, mapped_document, mappings, primary_key)

    if values:
        sql = u"INSERT INTO {0} ({1}) VALUES {2}".format(
            collection,
            u','.join(['_creationDate'] + keys),
            u",".join(values)
        )
        cursor.execute(sql)


def insert_scalar_arrays(collection, cursor, db, document, mapped_document, mappings, primary_key):
    for arrayField in get_array_of_scalar_fields(mappings, db, collection, document):
        dest = mappings[db][collection][arrayField]['dest']
        fk = mappings[db][collection][arrayField]['fk']
        value_field = mappings[db][collection][arrayField]['valueField']
        scalar_values = get_nested_field_from_document(document, arrayField)

        linked_documents = []
        for value in scalar_values:
            linked_documents.append({fk: mapped_document[primary_key], value_field: value})

        sql_bulk_insert(cursor, mappings, "{0}.{1}".format(db, dest), linked_documents)


def insert_document_arrays(collection, cursor, db, document, mapped_document, mappings, primary_key):
    for arrayField in get_array_fields(mappings, db, collection, document):
        dest = mappings[db][collection][arrayField]['dest']
        fk = mappings[db][collection][arrayField]['fk']
        linked_documents = get_nested_field_from_document(document, arrayField)

        for linked_document in linked_documents:
            linked_document[fk] = mapped_document[primary_key]

        sql_bulk_insert(cursor, mappings, "{0}.{1}".format(db, dest), linked_documents)


def sql_insert(cursor, tableName, document, mappings, db, collection):
    primary_key = mappings[db][collection]['pk']
    creationDate = extract_creation_date(document, primary_key)
    if creationDate is not None:
        document['_creationDate'] = creationDate

    keys = document.keys()
    valuesPlaceholder = ("%(" + column_name + ")s" for column_name in keys)

    if primary_key in document:
        sql = u"INSERT INTO {0} {1} VALUES {2} ON CONFLICT ({3}) DO UPDATE SET {1} = {2}".format(
            tableName,
            to_sql_list(keys),
            to_sql_list(valuesPlaceholder),
            primary_key
        )
    else:
        sql = u"INSERT INTO {0} {1} VALUES {2}".format(
            tableName,
            to_sql_list(keys),
            to_sql_list(valuesPlaceholder),
            primary_key
        )

    try:
        cursor.execute(
            sql,
            get_transformed_document(mappings, db, collection, document)
        )
    except Exception as e:
        LOG.error(u"Impossible to upsert the following document %s : %s", document, e)


def remove_control_chars(s):
    return control_char_re.sub('', s)


def to_sql_value(value):
    if value is None:
        return 'NULL'

    if isinstance(value, (int, long, float, complex)):
        return str(value)

    if isinstance(value, bool):
        return str(value).upper()

    if isinstance(value, basestring):
        return u"'{0}'".format(remove_control_chars(value).replace("'", "''"))

    return u"'{0}'".format(str(value))


def object_id_adapter(object_id):
    return AsIs(to_sql_value(object_id))
