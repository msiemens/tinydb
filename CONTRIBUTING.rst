Contribution Guidelines
#######################

Whether reporting bugs, discussing improvements and new ideas or writing
extensions: Contributions to TinyDB are welcome! Here's how to get started:

1. Check for open issues or open a fresh issue to start a discussion around
   a feature idea or a bug
2. Fork `the repository <https://github.com/msiemens/tinydb/>`_ on Github,
   create a new branch off the `master` branch and start making your changes
   (known as `GitHub Flow <https://guides.github.com/introduction/flow/index.html>`_)
3. Write a test which shows that the bug was fixed or that the feature works
   as expected
4. Send a pull request and bug the maintainer until it gets merged and
   published ☺

Philosophy of TinyDB
********************

TinyDB aims to be simple and fun to use. Therefore two key values in
development are simplicity and elegance. Sometimes these values
contradict each other. In this case, try using as little magic as possible.
In any case don't forget commenting code that isn't clear at first glance.

Code Conventions
****************

In general the TinyDB source should always follow `PEP 8 <http://legacy.python.org/dev/peps/pep-0008/>`_.
Exceptions are allowed in well justified and documented cases. However we make
a small exception concerning docstrings:

When using multiline docstrings, keep the opening and closing triple quotes
on their own lines and add an empty line after it.

.. code-block:: python

    def some_function():
        """
        Documentation ...
        """

        # implementation ...

Version Numbers
***************

TinyDB follows the `SemVer versioning guidelines <http://semver.org/>`_.
This implies that backwards incompatible changes in the API will increment
the major version. So think twice before making such changes.
