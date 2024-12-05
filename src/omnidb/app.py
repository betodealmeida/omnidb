from dataclasses import dataclass
from inspect import getmembers, isclass
from typing import Any
from urllib.parse import unquote

import aiosqlite
import click
import sqlglot
from quart import Quart, Response, jsonify, render_template, url_for
from quart_schema import QuartSchema, validate_request, validate_response
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import NoSuchTableError
from sqlglot.dialects.dialect import Dialects
from uvicorn import run
from yarl import URL

from omnidb import dialects

app = Quart(__name__)
QuartSchema(app)


@dataclass
class Query:
    dialect: Dialects
    submitted_sql: str


@dataclass
class Column:
    name: str
    type: str | None


@dataclass
class Results:
    statement: str
    columns: list[Column]
    rows: list[tuple[Any, ...]]


@dataclass
class QueryWithResults(Query):
    executed_sql: str
    results: list[Results]


async def execute_sql(statements: list[str]) -> list[Results]:
    """
    Execute the SQL query and return the results.
    """
    results = []
    database = app.config["DATABASE"]
    async with aiosqlite.connect(database) as db:
        for statement in statements:
            async with db.execute(statement) as cursor:
                results.append(
                    Results(
                        statement=statement,
                        columns=[Column(*column[:2]) for column in cursor.description],
                        rows=await cursor.fetchall(),
                    )
                )

    return results


@app.route("/", methods=["GET"])
async def home() -> str:
    """
    Home page.
    """
    sqlalchemy_dialects = dict(
        getmembers(
            dialects,
            lambda attribute: isclass(attribute)
            and issubclass(attribute, dialects.DialectOverride)
            and not attribute == dialects.DialectOverride,
        )
    )
    base_url = URL(url_for("home", _external=True))
    uris = {
        dialect.database_name: str(
            base_url.with_scheme(f"{dialect.name}+{dialect.driver}")
        )
        for dialect in sqlalchemy_dialects.values()
    }

    return await render_template("dialects.html", uris=uris)


@app.route("/ping", methods=["GET", "HEAD"])
async def ping() -> str:
    """
    Health check endpoint.
    """
    return "pong"


@app.route("/reflection", methods=["GET"])
async def get_tables() -> Response:
    """
    Reflection endpoint for listing all tables.
    """
    engine = create_engine(f"sqlite:///{app.config['DATABASE']}")
    inspector = inspect(engine)
    return jsonify({"results": inspector.get_table_names()})


@app.route("/reflection/<table>", methods=["GET", "HEAD"])
async def get_table(table: str) -> Response:
    """
    Reflection endpoint for listing all columns in a table.
    """
    engine = create_engine(f"sqlite:///{app.config['DATABASE']}")
    inspector = inspect(engine)
    try:
        columns = [
            {
                "name": column["name"],
                "type": column["type"].__visit_name__ if column["type"] else None,
                "nullable": column["nullable"],
                "default": column["default"],
            }
            for column in inspector.get_columns(unquote(table))
        ]
    except NoSuchTableError:
        return Response(status=404)

    return jsonify({"results": {"columns": columns}})


@app.route("/queries", methods=["POST"])
@validate_request(Query)
@validate_response(QueryWithResults)
async def queries(data: Query) -> QueryWithResults:
    """
    Run a query.
    """
    statements = sqlglot.transpile(
        data.submitted_sql,
        read=data.dialect,
        write="sqlite",
    )
    results = await execute_sql(statements)

    return QueryWithResults(
        dialect=data.dialect,
        submitted_sql=data.submitted_sql,
        executed_sql=";\n".join(statements),
        results=results,
    )


def create_app(database: str) -> Quart:
    """
    Factory to create and configure the Quart app.
    """
    app.config["DATABASE"] = database
    return app


@click.command()
@click.option("-p", "--port", default=4411, help="Port to bind.")
@click.option("-h", "--host", default="127.0.0.1", help="Host to bind.")
@click.argument("database")
def main(port: int, host: str, database: str):
    """Run the Quart application."""
    app = create_app(database)
    run(app, host=host, port=port, lifespan="on")
