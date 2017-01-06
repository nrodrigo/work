1 - Create an empty db and credentials

2 - Create schema: mysql -u <user> -h <host> -p <pw> <dbname> < schema.sql

3 - Verify that you have all of the required python modules:
    import dateutil.parser
    import json
    import MySQLdb
    import MySQLdb.cursors
    import re
    import web

4 - Run from command line:
    python tfwebhook.py

5 - Test curl to http://0.0.0.0:8080/tfwebhook with the following command (in the project dir):

curl -vX POST http://0.0.0.0:8080/tfwebhook \
  -d @webhookdata.json --header "Content-Type: application/json"
