from typing import Any, TypedDict
from urllib.parse import quote

import requests
import sqlalchemy.types
from firebolt_db.firebolt_dialect import FireboltDialect
from pydruid.db.sqlalchemy import DruidHTTPSDialect
from sqlalchemy.dialects.mssql.base import MSDialect
from sqlalchemy.dialects.mysql.base import MySQLDialect
from sqlalchemy.dialects.oracle.base import OracleDialect
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.dialects.sqlite.base import SQLiteDialect
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
    "mssql": Dialects.TSQL,
    "mysql": Dialects.MYSQL,
    "oracle": Dialects.ORACLE,
    "sqlite": Dialects.SQLITE,
    # "druid": Dialects.DRUID,
}


class SQLAlchemyColumn(TypedDict):
    """
    A custom type for a SQLAlchemy column.
    """

    name: str
    type: TypeEngine
    nullable: bool
    default: str | None


class Constraint(TypedDict):
    """
    Type for `get_pk_constraint`.
    """

    constrained_columns: list[str]
    name: str | None


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

    def get_view_names(
        self,
        connection: SqlaConnection,
        schema: str | None = None,
        **kw: Any,
    ) -> list[str]:
        """
        Get all view names.
        """
        return []

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
                "type": getattr(sqlalchemy.types, column["type"]),
                "nullable": column["nullable"],
                "default": column["default"],
            }
            for column in payload["results"]["columns"]
        ]

    def do_rollback(self, dbapi_connection: Connection) -> None:
        """
        Not really.
        """

    def get_schema_names(self, connection: SqlaConnection, **kw: Any) -> list[str]:
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
    ) -> Constraint:
        return {"constrained_columns": [], "name": None}

    def get_foreign_keys(
        self,
        connection: SqlaConnection,
        table_name: str,
        schema: str | None = None,
        **kw: Any,
    ) -> list[str]:
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


class OmniMySQLDialect(DialectOverride, MySQLDialect):
    """
    MySQL dialect with overrides.
    """

    database_name = "MySQL"


class OmniOracleDialect(DialectOverride, OracleDialect):
    """
    Oracle dialect with overrides.
    """

    database_name = "Oracle"


class OmniSQLiteDialect(DialectOverride, SQLiteDialect):
    """
    SQLite dialect with overrides.
    """

    database_name = "SQLite"


class OmniDruidDialect(DialectOverride, DruidHTTPSDialect):
    """
    Druid dialect with overrides.
    """

    database_name = "Druid"


class OmniFireboltDialect(DialectOverride, FireboltDialect):
    """
    Firebolt dialect with overrides.
    """

    database_name = "Firebolt"
