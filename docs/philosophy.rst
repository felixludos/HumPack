Philosophy
==========

This library is not meant to replace standard python objects (such as :py:`dict`, :py:`list`, etc.)

Serialization
-------------

Object serialization tends to focus on storing all the information necessary for restoring the state of an object in the most compressed form possible. This is especially important when transmitting information across processes or a network, however there are also downsides, including: cross-platform compatibility and future-proofing. By using a human readable format, the stored objects are


.. role:: py(code)
   :language: python
