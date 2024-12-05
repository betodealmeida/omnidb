"""
Types for the DB API 2.0 implementation.
"""

import datetime
import time
from enum import Enum
from typing import Any


class ColumnType(str, Enum):
    """
    Types for columns.

    These represent the values from the ``python_type`` attribute in SQLAlchemy columns.
    """

    BYTES = "BYTES"
    STR = "STR"
    FLOAT = "FLOAT"
    INT = "INT"
    DECIMAL = "DECIMAL"
    BOOL = "BOOL"
    DATETIME = "DATETIME"
    DATE = "DATE"
    TIME = "TIME"
    TIMEDELTA = "TIMEDELTA"
    LIST = "LIST"
    DICT = "DICT"


Row = tuple[Any, ...]


# Cursor description
Description = (
    list[
        tuple[
            str,
            ColumnType,
            str | None,
            str | None,
            str | None,
            str | None,
            bool | None,
        ]
    ]
    | None
)


class DBAPIType:  # pylint: disable=too-few-public-methods
    """
    Constructor for the required DB API 2.0 types.
    """

    def __init__(self, *column_types: ColumnType):
        self.column_types = column_types

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, ColumnType):
            return other in self.column_types

        return NotImplemented


STRING = DBAPIType(ColumnType.STR)
BINARY = DBAPIType(ColumnType.BYTES)
NUMBER = DBAPIType(
    ColumnType.FLOAT,
    ColumnType.INT,
    ColumnType.DECIMAL,
    ColumnType.BOOL,
)
DATETIME = DBAPIType(
    ColumnType.DATETIME,
    ColumnType.DATE,
    ColumnType.TIME,
    ColumnType.TIMEDELTA,
)


def Date(  # pylint: disable=invalid-name
    year: int,
    month: int,
    day: int,
) -> datetime.date:
    """Constructs an object holding a date value."""
    return datetime.date(year, month, day)


def Time(  # pylint: disable=invalid-name
    hour: int,
    minute: int,
    second: int,
) -> datetime.time:
    """Constructs an object holding a time value."""
    return datetime.time(hour, minute, second, tzinfo=datetime.UTC)


def Timestamp(  # pylint: disable=invalid-name, too-many-arguments
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
) -> datetime.datetime:
    """Constructs an object holding a timestamp value."""
    return datetime.datetime(
        year,
        month,
        day,
        hour,
        minute,
        second,
        tzinfo=datetime.UTC,
    )


def DateFromTicks(ticks: int) -> datetime.date:  # pylint: disable=invalid-name
    """
    Constructs an object holding a date value from the given ticks value.

    Ticks should be in number of seconds since the epoch.
    """
    return Date(*time.gmtime(ticks)[:3])


def TimeFromTicks(ticks: int) -> datetime.time:  # pylint: disable=invalid-name
    """
    Constructs an object holding a time value from the given ticks value.

    Ticks should be in number of seconds since the epoch.
    """
    return Time(*time.gmtime(ticks)[3:6])


def TimestampFromTicks(ticks: int) -> datetime.datetime:  # pylint: disable=invalid-name
    """
    Constructs an object holding a timestamp value from the given ticks value.

    Ticks should be in number of seconds since the epoch.
    """
    return Timestamp(*time.gmtime(ticks)[:6])


def Binary(string: str) -> bytes:  # pylint: disable=invalid-name
    """constructs an object capable of holding a binary (long) string value."""
    return string.encode()
