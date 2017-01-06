# uses web.py:
#  pip install web.py
import dateutil.parser
import json
import MySQLdb
import MySQLdb.cursors
import re
import web

# test curl
# curl -vX POST http://0.0.0.0:8080/ -d @webhookdata.json --header "Content-Type: application/json"

# db config
dbc = {
    'username': 'root',
    'database': 'tfwebhook',
    'server': 'localhost',
    #'password': ''
    }

urls = ('/tfwebhook', 'hooks')
app = web.application(urls, globals())

class hooks:

    def POST(self):
        data = web.data()
        print
        print 'DATA RECEIVED:'
        jsondata = json.loads(data)
        data_handler(jsondata)
        return 'OK'

    def GET(self):
        return 'OK'

if __name__ == '__main__':
    app.run()

class data_handler:
    def __init__(self, json):
        self.db = MySQLdb.connect(
            host = dbc['server']
            , user = dbc['username']
            , db = dbc['database']
            , cursorclass = MySQLdb.cursors.DictCursor)
        #self.db = MySQLdb.connect(
        #    host = dbc['server']
        #    , user = dbc['username']
        #    , db = dbc['database']
        #    , password = dbc['password']
        #    , cursorclass = MySQLdb.cursors.DictCursor)
        self.db.autocommit(True)
        self.cursor = self.db.cursor()
        self.data = json
        self.insert_data()

    def insert_data(self):
        # local vars
        form_id = self.data['form_response']['form_id']
        event_id = self.data['event_id']

        # first, let's check to see that we have the questions that appear on this form
        # in the db
        self.cursor.execute("select count(1) cnt from form_questions")
        res = self.cursor.fetchone()
        if res['cnt'] == 0: # should only ever be one row
            self.cursor.execute("insert into form_questions values (1)")

        qcolumns = dict()
        for q in self.data['form_response']['definition']['fields']:
            if int(q['id']) == 39815879:
                q['title'] =  'is this correct?'
            qcolumns['field_'+q['id']] = q['title']

        self.cursor.execute("select * from form_questions")
        res = self.cursor.fetchone()
        updateq = list()
        for colname in qcolumns:
            if colname not in res:
                sql = "alter table form_questions add column %s tinytext" % (colname)
                self.cursor.execute(sql)
                updateq.append("%s='%s'" % (colname, qcolumns[colname]))
        if len(updateq) > 0:
            sql = "update form_questions set %s" % (', '.join(updateq), )
            self.cursor.execute(sql)

        # we might as well do the same for form_answers while we're at it
        self.cursor.execute("select column_name from information_schema.columns where table_name='form_answers'")
        res = self.cursor.fetchall()
        acolumnsdb = dict()
        validemail = 0
        for r in res:
            acolumnsdb[r['column_name']] = 1
        for colname in qcolumns:
            if colname not in acolumnsdb:
                sql = "alter table form_answers add column %s tinytext" % (colname)
                self.cursor.execute(sql)

        # Let's insert the answers later
        # Before we proceed, we need to check if a valid email was submitted
        for a in self.data['form_response']['answers']:
            if a['type'] == 'email' and not re.match(r"[^@]+@[^@]+\.[^@]+", a['email']):
                # Invalid email address, let's not insert bad data
                return
            
        # Specification: All forms will have the exact same format, so no need to keep track of separate forms
        # with possibly different questions

        # have we inserted this event before
        self.cursor.execute("select count(1) cnt from form_event where event_id = %s", (event_id,))
        res = self.cursor.fetchone()
        if res['cnt']>0:
            # event already exists, don't double insert?  Are updates possible?
            return

        self.cursor.execute("""insert into form_event (
            event_id
            , form_id
            , submitted_at
            , token
            ) values (
            %s
            , %s
            , %s
            , %s
            )""", (
            event_id,
            form_id,
            dateutil.parser.parse(self.data['form_response']['submitted_at']).strftime('%Y-%m-%d %H:%M:%S'),
            self.data['form_response']['token']
            ))

        form_event_id = self.cursor.lastrowid

        # since we haven't inserted this event, we'll assume no answers for this event exist in the db
        field_names = list()
        interp = list()
        answers = list()
        for a in self.data['form_response']['answers']:
            field_names.append('field_'+a['field']['id'])
            interp.append('%s')
            answers.append(str(a[a['type']]))
        sql = "insert into form_answers (form_event_id, %s) values (%s, %s)" % (', '.join(field_names), form_event_id, ', '.join(interp))
        self.cursor.execute(sql, tuple(answers))
        self.cursor.close()
        return
