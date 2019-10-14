import os
import sqlite3
import mysql.connector
import datetime

class Connection:
    __db = 'sqlite'
    __config = None
    __conn = None
    __sqlite_filename = 'data/atstats.db'

    def __init__(self, config):
        self.__db = config['Type']
        self.__config = config
        self._createConnection()
        self.__createCommonTables()
        self.__createBitbucketTables()

    def __checkTableExists(self, table):
        if self.__db == 'sqlite':
            query = 'SELECT name FROM sqlite_master WHERE type="table" AND name = ?'
        elif self.__db == 'mysql':
            query = 'SELECT table_name FROM information_schema.tables WHERE table_name = %s'

        table_exists = False
        cursor = self.__conn.cursor()
        cursor.execute(query, (table,))
        result = cursor.fetchone()
        if result is not None:
            table_exists = True
        cursor.close()

        return table_exists

    def __createCommonTables(self):
        for table in ('account'):
            if self.__checkTableExists(table) == False:
                self.__createCommonTable(table)

    def __createBitbucketTables(self):
        for table in ('account', 'pr_activity', 'pr_reviewer', 'pr_comment'):
            if self.__checkTableExists(table) == False:
                self.__createBitbucketTable(table)

    def __createMySqlDatabase(self):
        config = {
            'user': self.__config['User'],
            'password': self.__config['Password'],
            'host': self.__config['Host'],
            'raise_on_warnings': True
        }
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format('atstats'))
        cursor.close()
        conn.close()

    def __createMysqlConnection(self):
        config = {
            'user': self.__config['User'],
            'password': self.__config['Password'],
            'host': self.__config['Host'],
            'database': self.__config['Database'],
            'raise_on_warnings': True
        }
        try:
            self.__conn = mysql.connector.connect(**config)
        except mysql.connector.Error as err:
            if err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
                self.__createMySqlDatabase()
                self.__conn = mysql.connector.connect(**config)

    def __createSqliteConnection(self):
        new_file = not os.path.exists(self.__sqlite_filename)
        self.__conn = sqlite3.connect(self.__sqlite_filename)
        if new_file == True:
            self.__createBitbucketTables()

    def __executeSql(self, sql, param=None):
        if self.__db == 'sqlite':
            self.__conn.execute(sql, param)
        elif self.__db == 'mysql':
            cursor = self.__conn.cursor()
            cursor.execute(sql, param)
            cursor.close()

    def _createConnection(self):
        if self.__db == 'sqlite':
            self.__createSqliteConnection()
        elif self.__db == 'mysql':
            self.__createMysqlConnection()
        else:
            self.__conn = None

    def __createCommonTable(self, table):
        sql = ''
        if table == 'account':
            if self.__db == 'sqlite':
                params = ('text primary key',)
            elif self.__db == 'mysql':
                params = ('varchar(15) primary key',)

            sql = '''create table account (
                slug    %s,
                name    text,
                email   text,
                display text,
                type    text
                )''' % params

        if sql != '':
            self.__executeSql(sql, None)

    def __createBitbucketTable(self, table):
        sql = ''
        if table == 'pr_activity':
            if self.__db == 'sqlite':
                params = ('integer',) * 3 + ('text',) * 2
            elif self.__db == 'mysql':
                params = ('datetime',) * 3 + ('varchar(15)', 'varchar(128)')

            sql = '''create table pr_activity (
                id          integer,
                title       text,
                description text,
                state       text,
                open        integer,
                closed      integer,
                created_date %s,
                closed_date  %s,
                updated_date %s,
                from_branch  text,
                comments    text,
                author      %s,
                project     %s,
                constraint pr_activity_fk
                foreign key (author) references account (slug),
                constraint pr_activity_pk
                primary key (id, project)
                )''' % params
        elif table == 'pr_reviewer':
            if self.__db == 'sqlite':
                params = ('text', 'integer') 
            elif self.__db == 'mysql':
                params = ('varchar(15)', 'datetime') 

            sql = '''create table pr_reviewer (
                activity_id     integer,
                reviewer        %s,
                created_date    %s,
                action          text,
                constraint pr_reviewer_fk
                foreign key (reviewer) references account (slug),
                constraint pr_reviewer_pk
                primary key (activity_id, reviewer, created_date)
                )''' % params
        elif table == 'pr_comment':
            sql = '''create table pr_comment (
                activity_id     integer,
                commenter       varchar(15),
                comment         text,
                action          text,
                created_date    datetime,
                constraint pr_comment_fk
                foreign key (commenter) references account (slug),
                constraint pr_comment_pk
                primary key (activity_id, commenter)
                )'''

        if sql != '':
            self.__executeSql(sql, None)

    def __generateDbSpecificVar(self, length):
        output = ('?,' * length)[:-1]
        if self.__db == 'mysql':
            output = ('%s,' * length)[:-1]
        return output

    def addUsers(self, users):
        for key in users:
            vars = self.__generateDbSpecificVar(5)
            db_var = self.__generateDbSpecificVar(1)

            upsert = 'on conflict(slug) do update set '
            if self.__db == 'mysql':
                upsert = 'on duplicate key update'

            sql =  '''insert into account
                    (slug, name, email, display, type)
                    values
                    ({vars})
                    {upsert}
                    name = {db_var},
                    email = {db_var},
                    display = {db_var},
                    type = {db_var}'''.format(vars=vars, db_var=db_var, upsert=upsert)

            param = (users[key]['slug'], 
                    users[key]['name'], 
                    '' if not users[key].get('emailAddress') else users[key]['emailAddress'], 
                    users[key]['displayName'], 
                    users[key]['type'],
                    users[key]['name'], 
                    '' if not users[key].get('emailAddress') else users[key]['emailAddress'], 
                    users[key]['displayName'], 
                    users[key]['type'])

            self.__executeSql(sql, param)

    def addActivities(self, activities):
        earliest_date = datetime.datetime.now()
        vars = self.__generateDbSpecificVar(13)

        sql = '''replace into pr_activity
                (id, title, description, state, open, closed, created_date, closed_date, updated_date, from_branch, comments, author, project)
                values
                ({vars})'''.format(vars=vars)

        for activity in activities:
            param = (activity['id'], 
                    activity['title'],
                    activity['description'],
                    activity['state'],
                    activity['open'],
                    activity['closed'],
                    datetime.datetime.fromtimestamp(activity['createdDate'] / 1e3),
                    datetime.datetime.fromtimestamp(activity['closedDate'] / 1e3),
                    datetime.datetime.fromtimestamp(activity['updatedDate'] / 1e3),
                    activity['fromBranch'],
                    activity['comments'],
                    activity['author'],
                    activity['project'])

            self.__executeSql(sql, param)

            updated_date = datetime.datetime.fromtimestamp(activity['updatedDate'] / 1e3)
            if earliest_date > updated_date:
                earliest_date = updated_date

        self.__conn.commit()

        return earliest_date

    def addReviewers(self, reviewers):
        vars = self.__generateDbSpecificVar(4)

        sql = '''replace into pr_reviewer
                (activity_id, reviewer, created_date, action)
                values
                ({vars})'''.format(vars=vars)

        for reviewer in reviewers:
            param = (reviewer['activityId'], 
                    reviewer['user'],
                    datetime.datetime.fromtimestamp(reviewer['createdDate'] / 1e3),
                    reviewer['action'])

            try:
                self.__executeSql(sql, param)
            except mysql.connector.Error as err:
                print(sql, param)

    def addComments(self, comments):
        vars = self.__generateDbSpecificVar(5)

        sql = '''replace into pr_comment
                (activity_id, commenter, comment, action, created_date)
                values
                ({vars})'''.format(vars=vars)

        for comment in comments:
            param = (comment['activityId'], 
                    comment['user'],
                    comment['comment'],
                    comment['commentAction'],
                    datetime.datetime.fromtimestamp(comment['createdDate'] / 1e3))

            try:
                self.__executeSql(sql, param)
            except mysql.connector.Error as err:
                print(sql, param)

    def closeConnection(self):
        self.__conn.close()