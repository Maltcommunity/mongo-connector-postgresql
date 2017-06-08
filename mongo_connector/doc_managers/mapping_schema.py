MAPPING_SCHEMA = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "title": "Mongo Connector PostgreSQL Mapping",
    "description": "Describe the content of a mapping",
    "definitions": {
        "database": {
            "type": "object",
            "patternProperties": {
                "^(.*)$": {
                    "$ref": "#/definitions/collection"
                }
            }
        },
        "collection": {
            "type": "object",
            "properties": {
                "pk": {"type": "string"}
            },
            "patternProperties": {
                "^(?!pk$)(.*)$": {
                    "type": "object",
                    "oneOf": [
                        {"$ref": "#/definitions/basic-field"},
                        {"$ref": "#/definitions/array-field"},
                        {"$ref": "#/definitions/scalar-array-field"}
                    ]
                }
            },
            "required": ["pk"]
        },
        "basic-field": {
            "properties": {
                "type": {
                    "enum": [
                        # Numeric types
                        "SMALLINT",
                        "INTEGER",
                        "INT",
                        "BIGINT",
                        "DECIMAL",
                        "NUMERIC",
                        "REAL",
                        "DOUBLE PRECISION",
                        "SERIAL",
                        "BIGSERIAL",
                        # Monetary types
                        "MONEY",
                        # Character types
                        "CHARACTER VARYING",
                        "VARCHAR",
                        "CHARACTER",
                        "CHAR",
                        "TEXT",
                        # Binary types
                        "BYTEA",
                        # Date/Time types
                        "TIMESTAMP",
                        "DATE",
                        "TIME",
                        "INTERVAL",
                        # Boolean types
                        "BOOLEAN",
                        # Enum types (not implemented)
                        # Geometric types
                        "POINT",
                        "LINE",
                        "LSEG",
                        "BOX",
                        "PATH",
                        "POLYGON",
                        "CIRCLE",
                        # Network address types
                        "CIDR",
                        "INET",
                        "MACADDR",
                        # Bit string types
                        "BIT",
                        "BIT VARYING",
                        # Text search types
                        "TSVECTOR",
                        "TSQUERY",
                        # UUID types
                        "UUID",
                        # XML types
                        "XML",
                        # JSON types
                        "JSON",
                        # Range types
                        "INT4RANGE",
                        "INT8RANGE",
                        "NUMRANGE",
                        "TSRANGE",
                        "TSTZRANGE",
                        "DATERANGE",
                        # Object identifier types
                        "OID",
                        "REGPROC",
                        "REGPROCEDURE",
                        "REGOPER",
                        "REGCLASS",
                        "REGTYPE",
                        "REGCONFIG",
                        "REGDICTIONARY",
                        # pg_lsn types
                        "PG_LSN",
                        # Pseudo types
                        "ANY",
                        "ANYELEMENT",
                        "ANYARRAY",
                        "ANYNONARRAY",
                        "ANYENUM",
                        "ANYRANGE",
                        "CSTRING",
                        "INTERNAL",
                        "LANGUAGE_HANDLER",
                        "FDW_HANDLER",
                        "RECORD",
                        "TRIGGER",
                        "EVENT_TRIGGER",
                        "VOID",
                        "OPAQUE"
                    ]
                },
                "dest": {
                    "type": "string"
                }
            },
            "required": ["type"]
        },
        "array-field": {
            "properties": {
                "type": {"enum": ["_ARRAY"]},
                "dest": {"type": "string"},
                "fk": {"type": "string"}
            },
            "required": ["type", "dest", "fk"]
        },
        "scalar-array-field": {
            "properties": {
                "type": {"enum": ["_ARRAY_OF_SCALARS"]},
                "dest": {"type": "string"},
                "fk": {"type": "string"},
                "valueField": {"type": "string"}
            },
            "required": ["type", "dest", "fk", "valueField"]
        }
    },
    "type": "object",
    "patternProperties": {
        "^(.*)$": {
            "$ref": "#/definitions/database"
        }
    }
}
