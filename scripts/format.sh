#!/bin/sh

autoflake -r ./crash_analyzer --remove-all-unused-imports -i
isort -q ./crash_analyzer
black -q ./crash_analyzer
