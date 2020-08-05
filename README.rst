
.. role:: py(code)
   :language: python



.. raw:: html

    <img align="right" width="150" height="150" src="docs/_static/img/logo_border.png" alt="HumPack">

-------
HumPack
-------

.. image:: https://readthedocs.org/projects/humpack/badge/?version=latest
    :target: https://humpack.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

.. image:: https://travis-ci.com/felixludos/HumPack.svg?branch=master
    :target: https://travis-ci.com/felixludos/HumPack
    :alt: Test Status

.. setup-marker-do-not-remove

.. role:: py(code)
   :language: python

This package contains several high level utilities for python development, including:

- Packing: Human Readable Serialization of Python Objects
- Transactions: Grouping multiple python statements into an atomic operation that can be committed or aborted
- Containers: dropin replacements for several common python types (including :py:`dict`, :py:`list`, :py:`set`, etc.)
- Cryptography: simple utilities for common cryptography functionality (very high-level on top of standard python libraries)


Install
=======

.. install-marker-do-not-remove

Everything is tested with Python 3.7 on Ubuntu 18.04, but there is no reason it shouldn't also work for Windows.

You can install this package through pip:

.. code-block:: bash

    pip install humpack

Alternatively, you can clone this repo and install the local version for development:

.. code-block:: bash

    git clone https://github.com/felixludos/HumPack
    pip install -e ./HumPack

.. end-install-marker-do-not-remove


Quick Start
===========

.. quickstart-marker-do-not-remove



Containers
----------

The provided containers: :py:`tdict`, :py:`tlist`, and :py:`tset` serve as drop-in replacements for pythons :py:`dict`, :py:`list`, and :py:`set` types that are :py:`Transactionable` and :py:`Packable` (more info below). Furthermore, all keys in :py:`adict` that are valid attribute names, can be treated as attributes.

A few examples:

.. code-block:: python

    from humpack import adict, tdict, tlist, tset
    from humpack import json_pack, json_unpack
    from humpack import AbortTransaction

    d = adict({'apple':1, 'orange':10, 'pear': 3})
    d.apple += 10
    d.update({'non-det banana':tset({2,3,7}), 'orange': None})
    del d.pear
    assert d.apple == 11 and 2 in d['non-det banana'] and 'pear' not in d
    options = tlist(d.keys())
    options.sort()
    first = options[0]
    assert first == 'apple'
    d.order = options

    json_d = json_pack(d)
    assert isinstance(json_d, str)

    d.begin() # starts a transaction (tracking all changes)
    assert options.in_transaction()

    d['non-det banana'].discard(7)
    d.cherry = 4.2
    assert 'cherry' in d and len(d['non-det banana']) == 2
    d['order'].extend(['grape', 'lemon', 'apricot'])
    assert 'grape' in options
    del d.order[0]
    del d['orange']
    d.order.sort()
    assert options[0] == 'apricot'

    d.abort()
    assert 'cherry' not in d and 7 in d['non-det banana']
    assert 'grape' not in options

    with d:
        assert d['non-det banana'].in_transaction()
        d.clear()
        assert len(d) == 0
        d.melon = 100j
        assert 'melon' in d and d['melon'].real == 0
        raise AbortTransaction

    assert 'melon' not in d

    assert json_pack(d) == json_d
    assert sum(d['non-det banana']) == sum(json_unpack(json_d)['non-det banana'])

    with d:
        assert 'cherry' not in d
        d.cherry = 5
        # automatically commits transaction on exiting the context if no exception is thrown

    assert 'cherry' in d

When starting with data in standard python, it can be converted to using the "t" series counter parts using :py:`containerify`.

.. code-block:: python

    from humpack import containerify
    from humpack import AbortTransaction

    x = {'one': 1, 1:2, None: ['hello', 123j, {1,3,4,5}]}

    d = containerify(x)

    assert len(x) == len(d)
    assert len(x[None]) == len(d[None])
    assert x['one'] == d.one
    with d:
        assert d[None][-1].in_transaction()
        del d.one
        d.two = 2
        d[None][-1].add(1000)
        assert d['two'] == 2 and 'one' not in d and sum(d[None][-1]) > 1000
        raise AbortTransaction
    assert 1000 not in d[None][-1] and 'one' in d and 'two' not in d

Finally, there are a few useful containers which don't have explicit types in standard python are also provided including heaps and stacks: :py:`theap` and :py:`tstack`.


Packing (serialization)
-----------------------

To serializing an object into a human-readable, json compliant format, this library implements packing and unpacking. When an object is packed, it can still be read (and manipulated, although that not recommended), converted to a valid json string, or encrypted/decrypted (see the Security section below). However for an obejct to be packable it and all of it's submembers (recursively) must either be primitives (:py:`int`, :py:`float`, :py:`str`, :py:`bool`, :py:`None`) or registered as a :py:`Packable`, which can be done

Packing and unpacking is primarily done using the :py:`pack` and :py:`unpack` functions, however, several higher level functions are provided to combine packing and unpacking with other common features in object serialization. For custom classes to be :py:`Packable`, they must implement three methods: :py:`__pack__`, :py:`__create__`, :py:`__unpack__` (for more info see the documentation for :py:`Packable`). When implementing these methods, all members of the objects that should be packed/unpacked, must use :py:`pack_member` and :py:`unpack_member` to avoid reference loops.

.. code-block:: python

    from humpack import pack, unpack

    x = {'one': 1, 1:2, None: ['hello', 123j, {1,3,4,5}]}

    p = pack(x) # several standard python types are already packable
    assert isinstance(p, dict)
    deepcopy_x = unpack(p)
    assert repr(x) == repr(deepcopy_x)

    from humpack import json_pack, json_unpack # Convert to/from json string

    j = json_pack(x)
    assert isinstance(j, str)
    deepcopy_x = json_unpack(j)
    assert repr(x) == repr(deepcopy_x)


    from humpack import save_pack, load_pack # Save/load packed object to disk as json file
    import os, tempfile

    fd, path = tempfile.mkstemp()
    try:
        with open(path, 'w') as tmp:
            save_pack(x, tmp)
        with open(path, 'r') as tmp:
            deepcopy_x = load_pack(tmp)
    finally:
        os.remove(path)
    assert repr(x) == repr(deepcopy_x)


For examples of how to any types can registered to be :py:`Packable` or objects can be wrapped in :py:`Packable` wrappers, see the :code:`humpack/common.py` and :code:`humpack/wrappers.py` scripts.

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
- Add Transactionable/Packable replacements for more standard python types (especially tuples)
- Possibly add 1-2 tutorials
- Write more comprehensive unit tests and report test coverage
- Allow packing bound methods of Packable types
- Add option to save class attributes

Contributions and suggestions are always welcome.

.. end-setup-marker-do-not-remove

Last maintained: May 29, 2020
