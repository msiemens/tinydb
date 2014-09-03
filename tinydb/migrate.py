import argparse
import sys

from tinydb.storages import JSONStorage


def migrate(*args, **kwargs):
    """
    Migrate a database to the scheme used in v2.0.

    To migrate a db that uses a custom storage, use

    >>> from tinydb.migrate import migrate
    >>> args = [...]  # args for your storage class
    >>> kwargs = {...}  # kwargs for your storage class
    >>> migrate(*args, **kwargs, storage=YourStorageClass)
    True

    :param storage: The class of the storage to use. Will be initialized
                    with ``args`` and ``kwargs``. Default:
                    :class:`~tinydb.storages.JSONStorage`
    :returns: ``True`` if the db has been migrated, ``False`` if the db
              didn't need a migration.
    """
    storage_cls = kwargs.pop('storage', JSONStorage)
    storage = storage_cls(*args, **kwargs)

    new_data = {}
    data = storage.read()

    if isinstance(data['_default'], dict):
        return False

    # Tables stay the same
    for table in data:
        # Data in tables is a dict with id -> value
        new_data[table] = {}

        for item in data[table]:
            new_data[table][item.pop('_id')] = item

    storage.write(new_data)
    return True


def main():
    parser = argparse.ArgumentParser(
        prog='python -m tinydb.migration',
        description='''In v2.0 TinyDB changed the way tables are stored.
        To open a file from v1.4 or prior, migrate it to the recent db scheme
        with this script.'''
    )
    parser.add_argument('file', nargs='+', help='database file to migrate')

    arguments = parser.parse_args()

    for f in arguments.file:
        sys.stdout.write('Processing {} ...'.format(f))
        if migrate(f):
            sys.stdout.write(' Done\n')
        else:
            sys.stdout.write(' No migration needed\n')


if __name__ == '__main__':
    main()
