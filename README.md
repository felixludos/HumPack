# HumPack
Human Readable Serialization of Python Objects

Primarily Savable and Transactionable mixins.
Including Savable/Transactionable versions of python containers (dict, list, set) - called tdict, tlist, tset.
Also includes an ObjectWrapper, so to make custom classes serializable you can either subclass them from Savable, or wrap them with the custom ObjectWrapper subclass (see Array for example).
