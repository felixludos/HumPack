# HumPack
Human Readable Serialization of Python Objects

Primarily Packable and Transactionable mixins.
Including Packable/Transactionable versions of python containers (dict, list, set) - called tdict, tlist, tset.
Also includes an ObjectWrapper, so to make custom classes serializable you can either subclass them from Packable, or wrap them with the custom ObjectWrapper subclass (see Array for example).
