from typing import Any, TypedDict
from urllib.parse import quote

import requests
from sqlalchemy.dialects.mssql.base import MSDialect
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.engine.base import Connection as SqlaConnection
from sqlalchemy.engine.url import URL
from sqlalchemy.sql.type_api import TypeEngine
from sqlglot.dialects.dialect import Dialects

from omnidb import dbapi
from omnidb.dbapi.connection import Connection

__all__ = ["OmniPGDialect"]


# map between SQLAlchemy backend and sqlglot/SQLAlchemy dialect
DIALECT_MAP = {
    "postgresql": Dialects.POSTGRES,
}


class SQLAlchemyColumn(TypedDict):
    """
    A custom type for a SQLAlchemy column.
    """

    name: str
    type: TypeEngine
    nullable: bool
    default: str | None


class DialectOverride:
    """
    An override class that replaces reflection methods.
    """

    driver = "omni"

    supports_statement_cache = True

    @classmethod
    def dbapi(cls):
        """
        Return our DB API module.
        """
        return dbapi

    import_dbapi = dbapi

    def initialize(self, connection: SqlaConnection) -> None:
        pass

    def create_connect_args(
        self,
        url: URL,
    ) -> tuple[tuple[(str, str)], dict[str, Any]]:
        """
        Create connection arguments.
        """
        backend = url.get_backend_name()
        dialect = DIALECT_MAP.get(backend, Dialects.DIALECT)
        service_url = f"http://{url.host}:{url.port}/{url.database}"

        return (service_url, dialect), {}

    def do_ping(self, dbapi_connection: Connection) -> bool:
        """
        Is the service up?
        """
        url = dbapi_connection.base_url / "ping"
        response = requests.head(url)
        return response.status_code == 200

    def has_table(
        self,
        connection: SqlaConnection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> bool:
        """
        Check if a table exists.
        """
        dbapi_connection = connection.engine.raw_connection()
        url = dbapi_connection.base_url / "reflection" / quote(table_name, safe="")
        response = requests.head(url)
        return response.status_code == 200

    def get_table_names(
        self,
        connection: SqlaConnection,
        schema: str | None = None,
        **kw: Any,
    ) -> list[str]:
        """
        Get all table names.
        """
        dbapi_connection = connection.engine.raw_connection()
        url = dbapi_connection.base_url / "reflection"
        response = requests.get(url)
        response.raise_for_status()
        payload = response.json()

        return payload["results"]

    def get_columns(
        self,
        connection: SqlaConnection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> list[SQLAlchemyColumn]:
        """
        Return information about columns.
        """
        dbapi_connection = connection.engine.raw_connection()
        url = dbapi_connection.base_url / "reflection" / quote(table_name, safe="")
        response = requests.get(url)
        response.raise_for_status()
        payload = response.json()

        return [
            {
                "name": column["name"],
                "type": column["type"],
                "nullable": column["nullable"],
                "default": column["default"],
            }
            for column in payload["results"]["columns"]
        ]

    def do_rollback(self, dbapi_connection: Connection) -> None:
        """
        Not really.
        """

    def get_schema_names(self, connection: SqlaConnection, **kw: Any):
        """
        Return the list of schemas.
        """
        return ["main"]

    def get_pk_constraint(
        self,
        connection: SqlaConnection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ):
        return {"constrained_columns": [], "name": None}

    def get_foreign_keys(
        self,
        connection: SqlaConnection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ):
        return []

    get_check_constraints = get_foreign_keys
    get_indexes = get_foreign_keys
    get_unique_constraints = get_foreign_keys

    def get_table_comment(self, connection, table_name, schema=None, **kwargs):
        return {"text": ""}


class OmniPGDialect(DialectOverride, PGDialect):
    """
    PostgreSQL dialect with overrides.
    """

    database_name = "PostgreSQL"


class OmniMSDialect(DialectOverride, MSDialect):
    """
    Microsoft SQL Server dialect with overrides.
    """

    database_name = "Microsoft SQL Server"
