#!/bin/bash

rm db.sqlite3
fd -t d migrations -X rm -r
fd -t d -HI __pycache__ -X rm -r
fd -t d -HI .mypy_cache -X rm -r
mkdir -p main/migrations
touch main/migrations/__init__.py
