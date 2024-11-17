from tinydb import TinyDB, Query, where

'''
    Advanced Queries
'''

# Create a TinyDB instance for more advanced insertions
# This will create or open a database file named 'people.json'
people_db = TinyDB('people.json')

# Define the data to be inserted
people = [
    {'name': 'John', 'birthday': {'year': 1985, 'month': 3, 'day': 15}},
    {'name': 'Alice', 'birthday': {'year': 1990, 'month': 5, 'day': 10}},
    {'name': 'Bob', 'birthday': {'year': 1987, 'month': 9, 'day': 20}},
    {'name': 'Carol', 'birthday': {'year': 1992, 'month': 12, 'day': 5}},
    {'name': 'Eve', 'birthday': {'year': 1989, 'month': 7, 'day': 25}},
]

# Insert the data into the database
people_db.insert_multiple(people)

# Print the contents of the database
print(people_db.all())

# Query the database using the Query object
User = Query()
print(people_db.search(User.name == 'John'))
print(people_db.search(User.birthday.year == 1990))

# Query the database using the where function
print(people_db.search(where('birthday').year == 1900))
print(people_db.search(~ (User.name == 'John')))

'''
    Query Modifiers
'''

# Negate a query, returns all people that are not John
negated_query = ~ (User.name == 'John')
print(people_db.search(negated_query))

# Logical AND, returns all people that are John and born before 1995
and_query = (User.name == 'John') & (User.birthday.year <= 1995)
print(people_db.search(and_query))

# Logical OR, returns all people that are Alex or Bob
or_query = (User.name == 'Alex') | (User.name == 'Bob')
print(people_db.search(or_query))

# Truncate the database, comment if you want to keep the data
people_db.truncate()
