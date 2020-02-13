# HumPack
Human Readable Serialization of Python Objects

[![Build Status](https://travis-ci.com/fleeb24/HumPack.svg?branch=master)](https://travis-ci.com/fleeb24/HumPack)
[![Documentation Status](https://readthedocs.org/projects/humpack/badge/?version=latest)](https://humpack.readthedocs.io/en/latest/?badge=latest)

Primarily Packable and Transactionable mixins.
Including Packable/Transactionable versions of python containers (dict, list, set) - called tdict, tlist, tset.
Also includes an ObjectWrapper, so to make custom classes serializable you can either subclass them from Packable, or wrap them with the custom ObjectWrapper subclass (see Array for example).
