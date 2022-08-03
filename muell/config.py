#!/usr/bin/python
import os


def config():
    return {
        "host": os.getenv("POSTGRESQL_HOST"),
        "user": os.getenv("POSTGRESQL_USER", "postgres"),
        "database": os.getenv("POSTGRESQL_DB", "postgres"),
        "password": os.getenv("POSTGRESQL_SECRET"),
        "port": os.getenv("POSTGRESQL_PORT", 5432)
    }
