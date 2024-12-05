"""
An implementation of a DB API 2.0 connection.
"""

# pylint: disable=invalid-name, unused-import, no-self-use

from typing import Any

from sqlglot.dialects.dialect import Dialects
from yarl import URL

from omnidb.dbapi.cursor import Cursor
from omnidb.dbapi.decorators import check_closed
from omnidb.dbapi.exceptions import NotSupportedError


class Connection:
    """
    Connection.
    """

    def __init__(self, base_url: URL, dialect: Dialects):
        self.base_url = base_url
        self.dialect = dialect

        self.closed = False
        self.cursors: list[Cursor] = []

    @check_closed
    def close(self) -> None:
        """Close the connection now."""
        self.closed = True
        for cursor in self.cursors:
            if not cursor.closed:
                cursor.close()

    @check_closed
    def commit(self) -> None:
        """Commit any pending transaction to the database."""
        raise NotSupportedError("Commits are not supported")

    @check_closed
    def rollback(self) -> None:
        """Rollback any transactions."""
        raise NotSupportedError("Rollbacks are not supported")

    @check_closed
    def cursor(self) -> Cursor:
        """Return a new Cursor Object using the connection."""
        cursor = Cursor(self.base_url, self.dialect)
        self.cursors.append(cursor)

        return cursor

    @check_closed
    def execute(
        self,
        operation: str,
        parameters: dict[str, Any] | None = None,
    ) -> Cursor:
        """
        Execute a query on a cursor.
        """
        cursor = self.cursor()
        return cursor.execute(operation, parameters)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def connect(url: str | URL, dialect: Dialects) -> Connection:
    """
    Create a connection to the database.
    """
    if not isinstance(url, URL):
        url = URL(url)

    return Connection(url, dialect)
