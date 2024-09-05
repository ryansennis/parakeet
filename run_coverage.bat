@echo off

REM Run tests with coverage
python -m coverage run -m unittest discover -s tests

REM Generate a simple coverage report in the terminal
python -m coverage report

REM Generate an HTML coverage report
python -m coverage html

echo Coverage report generated. Open htmlcov/index.html to view the HTML report.