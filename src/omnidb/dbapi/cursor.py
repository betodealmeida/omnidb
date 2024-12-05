"""
An implementation of a DB API 2.0 cursor.
"""

# pylint: disable=invalid-name, unused-import, no-self-use, redefined-builtin

import itertools
from typing import Any
from collections.abc import Iterator

import requests
import sqlglot
from sqlglot import exp
from sqlglot.dialects.dialect import Dialects
from yarl import URL

from omnidb.dbapi.decorators import check_closed, check_result
from omnidb.dbapi.exceptions import NotSupportedError
from omnidb.dbapi.types import ColumnType, Description, Row


def quote(value: str | bool | int | float, dialect: str) -> str:
    """
    Quotes a value based on the SQL dialect.
    """
    if isinstance(value, str):
        return exp.Literal.string(value).sql(dialect=dialect)

    if isinstance(value, bool):
        return exp.Literal.boolean(value).sql(dialect=dialect)

    if isinstance(value, (int, float)):
        return exp.Literal.number(value).sql(dialect=dialect)

    raise ValueError(f"Unsupported type: {type(value)}")


class Cursor:
    """
    Connection cursor.
    """

    def __init__(self, base_url: URL, dialect: Dialects):
        self.base_url = base_url
        self.dialect = dialect

        self.arraysize = 1
        self.closed = False
        self.description: Description = None

        self._results: Iterator[tuple[Any, ...]] | None = None
        self._rowcount = -1

    @property  # type: ignore
    @check_closed
    def rowcount(self) -> int:
        """
        Return the number of rows after a query.
        """
        try:
            results = list(self._results)  # type: ignore
        except TypeError:
            return -1

        n = len(results)
        self._results = iter(results)
        return max(0, self._rowcount) + n

    @check_closed
    def close(self) -> None:
        """
        Close the cursor.
        """
        self.closed = True

    @check_closed
    def execute(
        self,
        operation: str,
        parameters: dict[str, Any] | None = None,
    ) -> "Cursor":
        """
        Execute a query using the cursor.
        """
        self.description = None
        self._rowcount = -1

        # apply parameters
        if parameters:
            quoted_parameters = {key: quote(value) for key, value in parameters.items()}
            operation %= quoted_parameters

        parsed = sqlglot.parse(operation, dialect=self.dialect)
        if len(parsed) > 1:
            raise Warning("You can only execute one statement at a time")

        rows, description = self.run_query(operation)
        self._results = rows
        self.description = description

        return self

    def run_query(self, operation: str) -> tuple[Iterator[Row], Description]:
        """
        Run the query.

        This is the only backend-specific method. All other methods in the cursor should
        work with any database backend.
        """

        response = requests.post(
            self.base_url / "queries",
            json={
                "dialect": self.dialect,
                "submitted_sql": operation,
            },
            headers={
                "User-Agent": "OmniDB",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()

        payload = response.json()
        results = payload["results"][0]

        rows = (tuple(row) for row in results["rows"])
        description = [
            (
                column["name"],
                ColumnType(column["type"]) if column["type"] else None,
                None,
                None,
                None,
                None,
                True,
            )
            for column in results["columns"]
        ]

        return rows, description

    @check_closed
    def executemany(
        self,
        operation: str,
        seq_of_parameters: list[dict[str, Any]] | None = None,
    ) -> "Cursor":
        """
        Execute multiple statements.

        Currently not supported.
        """
        raise NotSupportedError(
            "``executemany`` is not supported, use ``execute`` instead",
        )

    @check_result
    @check_closed
    def fetchone(self) -> tuple[Any, ...] | None:
        """
        Fetch the next row of a query result set, returning a single sequence,
        or ``None`` when no more data is available.
        """
        try:
            row = self.next()
        except StopIteration:
            return None

        self._rowcount = max(0, self._rowcount) + 1

        return row

    @check_result
    @check_closed
    def fetchmany(self, size=None) -> list[tuple[Any, ...]]:
        """
        Fetch the next set of rows of a query result, returning a sequence of
        sequences (e.g. a list of tuples). An empty sequence is returned when
        no more rows are available.
        """
        size = size or self.arraysize
        results = list(itertools.islice(self, size))

        return results

    @check_result
    @check_closed
    def fetchall(self) -> list[tuple[Any, ...]]:
        """
        Fetch all (remaining) rows of a query result, returning them as a
        sequence of sequences (e.g. a list of tuples). Note that the cursor's
        arraysize attribute can affect the performance of this operation.
        """
        results = list(self)

        return results

    @check_closed
    def setinputsizes(self, sizes: int) -> None:
        """
        Used before ``execute`` to predefine memory areas for parameters.

        Currently not supported.
        """

    @check_closed
    def setoutputsizes(self, sizes: int) -> None:
        """
        Set a column buffer size for fetches of large columns.

        Currently not supported.
        """

    @check_result
    @check_closed
    def __iter__(self) -> Iterator[tuple[Any, ...]]:
        for row in self._results:  # type: ignore
            self._rowcount = max(0, self._rowcount) + 1
            yield row

    @check_result
    @check_closed
    def __next__(self) -> tuple[Any, ...]:
        return next(self._results)  # type: ignore

    next = __next__
