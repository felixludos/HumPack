
.. role:: py(code)
   :language: python



.. raw:: html

    <img align="left" width="120" height="120" src="docs/_static/img/logo_border.png" alt="HumPack">

-------
HumPack
-------

.. image:: https://readthedocs.org/projects/humpack/badge/?version=latest
    :target: https://humpack.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.com/fleeb24/HumPack.svg?branch=master
    :target: https://travis-ci.com/fleeb24/HumPack


This package contains several high level utilities for python development, including:

- Packing: Human Readable Serialization of Python Objects
- Transactions: Grouping multiple python statements into an atomic operation that can be committed or aborted
- Containers: dropin replacements for several common python types (including :py:`dict`, :py:`list`, :py:`set`, etc.)
- Cryptography: simple utilities for common cryptography functionality (very high-level on top of standard python libraries)


Install
=======

.. install-marker-do-not-remove

Everything is tested with Python 3.7 on Ubuntu 18.04, but there is no reason it shouldn't also work for Windows.

[TODO]
.. You can install this package through pip:
.. .. code-block:: bash
..     pip install humpack

This is not on pip yet, but you can clone this repo and install the local version for development:

.. Alternatively, you can clone this repo and install the local version for development:

.. code-block:: bash

    git clone https://github.com/fleeb24/HumPack
    pip install -e ./HumPack

.. end-install-marker-do-not-remove


Quick Start
===========

.. quickstart-marker-do-not-remove



Containers
----------

[TODO]

- entries where the keys are valid attribute names can be treated like (get/set/del)
- containerify
- show heaps


Packing (serialization)
-----------------------

[TODO]

Transactions
------------

For examples of how :code:`Transactionable` objects behave see the "Containers" section above.

To enable transactions for a class, it must be a subclass of :code:`Transactionable` and implement the four required functions: :code:`begin`, :code:`in_transaction`, :code:`commit`, and :code:`abort`. Assuming these functions are implemented as specified (see documentation), you can manipulate instances of these classes in a transaction and then roll back all the changes by aborting the transaction.

One important thing to note with subclassing :code:`Transactionable`: any members of instances of :code:`Transactionable` subclasses should be checked for if they are also :code:`Transactionable`, and if so, they the call should be delegated. In the example below, :code:`Account` has to take into account that its attribute :code:`user` could be :code:`Transactionable`.

.. code-block:: python

    from humpack import Transactionable

    class Account(Transactionable):
        def __init__(self, user, balance=0.):
            super().__init__()
            self._in_transaction = False
            self._shadow_user = None

            self.user = user
            self.balance = balance

        def change(self, delta):

            if self.balance + delta < 0.:
                raise ValueError
            self.balance += delta

        def begin(self):
            # FIRST: begin the transaction in self
            self._shadow_user = self.user.copy(), self.balance # Assuming `user` can be shallow copied with `copy()`
            self._in_transaction = True

            # THEN: begin transactions in any members that are Transactionable
            if isinstance(self.user, Transactionable):
                self.user.begin()

            # To be extra safe, you could also check `self.balance`, but we'll assume it's always a primitive (eg. float)

        def in_transaction(self):
            return self._in_transaction

        def commit(self):
            # FIRST: commit the transaction in self
            self._in_transaction = False
            self._shadow_user = None

            # THEN: commit transactions in any members that are Transactionable
            if isinstance(self.user, Transactionable):
                self.user.commit()

        def abort(self):
            # FIRST: abort the transaction in self
            if self.in_transaction(): # Note that this call only has an effect if self was in a transaction.
                self.user, self.balance = self._shadow_user

            self._in_transaction = False
            self._shadow_user = None

            # THEN: abort transactions in any members that are Transactionable
            if isinstance(self.user, Transactionable):
                self.user.abort()


Optionally, for a more pythonic implementation, you can use :py:`try`/:py:`except` statements instead of type checking with :py:`isinstance`.

Security
--------

There are a few high-level cryptography routines. Nothing special, just meant to make integration in larger projects simple and smooth.

.. end-quickstart-marker-do-not-remove

TODO
====

Features that could be added/improved:

- Enable simple conversion from containers to standard python (eg. decontainerify)
- Add security functions to encrypt/decrypt files and directories (collecting/zipping contents in a tar)
- Add Transactionable/Packable replacements for more standard python types
- Possibly add 1-2 tutorials
- Write more comprehensive unit tests and report test coverage

Contributions and suggestions are always welcome.

