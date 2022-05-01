import sqlite3

DB_PATH = 'my_data.db'


# init db of sqlite and create a table 'users' if not exist
def init():
    print('init db')
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id TEXT NOT NULL,
                 twsms_account TEXT NOT NULL,
                 twsms_password TEXT NOT NULL)''')


# insert a new user with user_id twsms_account and twsms_password
def insert_user(user_id, twsms_account, twsms_password):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''INSERT INTO users (user_id, twsms_account, twsms_password)
                 VALUES (?, ?, ?)''', (user_id, twsms_account, twsms_password))
    con.commit()
    con.close()


# select user from users with user_id
def find_user_with_user_id(user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''SELECT * FROM users WHERE user_id=?''', (user_id,))
    user = cur.fetchone()
    con.close()
    return user
