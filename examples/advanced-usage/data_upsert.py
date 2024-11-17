from tinydb import TinyDB, Query

# Creating a database
db = TinyDB('db.json')

# Insert data from people with name and logged-in status
people = [
    {'name': 'John', 'logged-in': False},
    {'name': 'Alice', 'logged-in': False},
    {'name': 'Bob', 'logged-in': True},
    {'name': 'Carol', 'logged-in': False},
    {'name': 'Eve', 'logged-in': True},
]
db.insert_multiple(people)
print(db.all())

# Uperting data, all Johns will be changed to logged-in
User = Query()
db.upsert({'name': 'John', 'logged-in': True}, User.name == 'John')
print(db.all())

# Truncate the database, comment if you want to keep the data
people_db.truncate()
