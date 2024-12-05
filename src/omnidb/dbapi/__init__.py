"""
An implementation of the DB API 2.0.
"""

from omnidb.dbapi.connection import connect
from omnidb.dbapi.exceptions import (
    DatabaseError,
    DataError,
    Error,
    IntegrityError,
    InterfaceError,
    InternalError,
    NotSupportedError,
    OperationalError,
    ProgrammingError,
    Warning,
)
from omnidb.dbapi.types import (
    BINARY,
    DATETIME,
    NUMBER,
    STRING,
    Binary,
    Date,
    DateFromTicks,
    Time,
    TimeFromTicks,
    Timestamp,
    TimestampFromTicks,
)


__all__ = [
    "connect",
    "DatabaseError",
    "DataError",
    "Error",
    "IntegrityError",
    "InterfaceError",
    "InternalError",
    "NotSupportedError",
    "OperationalError",
    "ProgrammingError",
    "Warning",
    "BINARY",
    "DATETIME",
    "NUMBER",
    "STRING",
    "Binary",
    "Date",
    "DateFromTicks",
    "Time",
    "TimeFromTicks",
    "Timestamp",
    "TimestampFromTicks",
    "apilevel",
    "threadsafety",
    "paramstyle",
]

apilevel = "2.0"
threadsafety = 3
paramstyle = "pyformat"
