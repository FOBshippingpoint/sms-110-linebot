import sqlite3

DB_PATH = 'my_data.db'


# init db of sqlite and create a table 'users' if not exist
def init():
    print('init db')
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id TEXT NOT NULL,
                 twsms_username TEXT NOT NULL,
                 twsms_password TEXT NOT NULL,
                 UNIQUE(user_id))''')
    cur.execute('''CREATE TABLE IF NOT EXISTS numbers
                (police_department TEXT NOT NULL,
                sms_number TEXT NOT NULL,
                UNIQUE(police_department, sms_number))''')
    con.commit()
    con.close()


# insert a new user with user_id twsms_username and twsms_password
def insert_user(user_id, twsms_username, twsms_password):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''INSERT INTO users (user_id, twsms_username, twsms_password)
                 VALUES (?, ?, ?)''', (user_id, twsms_username, twsms_password))
    con.commit()
    con.close()


# select user from users with user_id
def find_user_by_user_id(user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''SELECT * FROM users WHERE user_id=?''', (user_id,))
    user = cur.fetchone()
    con.close()
    return user


# delete user from users with user_id
def delete_user_by_user_id(user_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''DELETE FROM users WHERE user_id=?''', (user_id,))
    con.commit()
    con.close()


# insert a new number with police_department and sms_number
def insert_number(police_department, sms_number):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''INSERT INTO numbers (police_department, sms_number)
                 VALUES (?, ?)''', (police_department, sms_number))
    con.commit()
    con.close()


# insert many numbers with numbers tuple list(police_department, sms_number)
def insert_numbers(numbers):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executemany('''INSERT INTO numbers (police_department, sms_number)
                 VALUES (?, ?)''', numbers)
    con.commit()
    con.close()


# find all numbers
def find_numbers():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('''SELECT * FROM numbers''')
    numbers = cur.fetchall()
    con.close()
    return numbers
