
try:
	import numpy as np
except:
	print('No numpy found') # use logging instead

from typing import Any
from wrapt import ObjectProxy

from .packing import Packable, pack_data, unpack_data
from .transactions import Transactionable
from .basic_containers import tdict, tset, tlist

# all wrapped objects must be able to be copied (shallow copy) using
# note: Transactionable objects cant be wrapped
class ObjectWrapper(Transactionable, Packable, ObjectProxy):
	'''
	Wrapper to transform an object to be transactionable.
	
	Note: wrapped object must be copyable (shallow copy using `.copy()`)
	
	WARNING: It is NOT recommended to use this wrapper, unless you need a transactionable features
	
	'''
	
	def __init__(self, obj):
		super().__init__(obj)
		
		self._self_shadow = None
		self._self_children = tset()
	
	def begin(self):
		if self.in_transaction():
			return
			self.commit()
		
		self._self_shadow = self.copy()
		self._self_children.begin()
	
	def in_transaction(self):
		return self._self_shadow is not None
	
	def commit(self):
		if not self.in_transaction():
			return
		
		self._self_shadow = None
		self._self_children.commit()
	
	
	def abort(self):
		if not self.in_transaction():
			return
		
		self.__wrapped__ = self._self_shadow
		self._self_shadow = None
		self._self_children.abort()
	
	def __repr__(self):
		return self.__wrapped__.__repr__()
	
	def __str__(self):
		return self.__wrapped__.__str__()
	
	def __setattr__(self, key, value):
		if isinstance(value, Transactionable) and not key == '_self_children':
			self._self_children.add(value)
		return super().__setattr__(key, value)
	
	def __delattr__(self, item):
		value = self.__getattr__(item)
		if isinstance(value, Transactionable):
			self._self_children.remove(value)
		return super().__delattr__(item)
	
	def __unpack__(self, data):
		obj = self.__build__(data)
		
		self.__init__(obj)
	
	# must be overridden
	
	def __pack__(self): # save everything from the internal state
		'''
		Save all the necessary data from the internal state (and pack any subdata)
		
		:return: packed data
		'''
		raise NotImplementedError
	
	def __build__(self, data):
		'''
		Recover the wrapped object in the correct state from data and return wrapped object
		
		:param data: packed data
		:return: wrapped object with the loaded state
		'''
		raise NotImplementedError


class Transactionable_Array(ObjectWrapper):
	'''
	This is an example of how to use the `ObjectWrapper`.
	Wraps numpy arrays.
	
	WARNING: it is NOT recommended to use this wrapper for numpy arrays (they are already registered).
	'''
	
	def __pack__(self):
		data = {}
		
		data['dtype'] = pack_data(self.dtype.name)
		data['data'] = pack_data(self.tolist())
		
		return data
	
	def __build__(self, data=None):
		return np.array(unpack_data(data['data']), dtype=unpack_data(data['dtype']))

