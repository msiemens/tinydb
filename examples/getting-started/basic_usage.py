from tinydb import TinyDB, Query

# Creating a database
db = TinyDB('db.json')

# Inserting data
db.insert({'type': 'apple', 'count': 7})
db.insert({'type': 'peach', 'count': 3})

# Get and print all documents
print(db.all())

# Itering the database
for item in db:
    print(item)

# Searching for specific documents with Query object
Fruit = Query()
db.search(Fruit.type == 'peach')
db.search(Fruit.count > 5)

# Updating documents
db.update({'count': 10}, Fruit.type == 'apple')
print(db.all())

# Removing documents
db.remove(Fruit.count < 5)
print(db.all())

# Deleting all documents, comment if you want to keep the data
db.truncate()
