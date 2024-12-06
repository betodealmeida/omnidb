# OmniDB

A one-stop shop for all your Apache Superset database troubleshooting needs.

```
         O_      __)(
       ,'  `.   (_".`.
      :      :    /|`
      |      |   ((|_  ,-.
      ; -   /:  ,'  `:(( -\
     /    -'  `: ____ \\\-:
    _\__   ____|___  \____|_
   ;    |:|        '-`      :
  :_____|:|__________________:
  ;     |:|                  :
 :      |:|                   :
 ;______ `'___________________:
:                              :
|______________________________|
 `---.--------------------.---'
     |____________________|
     |                    |
     |____________________|
     |                    |
   _\|_\|_\/(__\__)\__\//_|(_
```

## What?

OmniDB has two parts:

1. A service that exposes a SQLite database so it can be queried using different SQL dialects. The dialects are then transpiled to SQLite using `sqlglot`.
2. A SQLAlchemy dialect that patches existing dialects, replacing the DB API driver and reflection methods with custom ones that can talk to the service.

So basically, you can replace this:

```python
engine = create_engine("postgresql://user:password@db-host:port/database")
```

With this:

```python
engine = create_engine("postgresql+omni://omni-host:port/")
```

# Why?

Imagine you developed a feature for Superset and you want to make sure it works with Oracle. But you don't have an Oracle DB. So you can spin up OmniDB and connect Superset to it. Superset will generate SQL in the Oracle dialect, and OmniDB will translate those calls to SQLite. Now you can test the SQL generation without having access to an actual Oracle database!
