
from typing import Any
from wrapt import ObjectProxy

try:
	import numpy as np
except ImportError:
	print('WARNING: unable to import numpy')

from .packing import Packable, pack_member, unpack_member
from .transactions import Transactionable
from .basic_containers import adict, tset, tlist


class Packable_Array(Packable, use_cls=np.ndarray):
	'''
	Wrapper to allow saving numpy arrays.
	Aside from being rather useful, this serves as an example for how to write a Packable wrapper.

	Note the necessary Packable methods are all static, and the use of "use_cls" in the class declaration.
	'''
	
	@staticmethod
	def __create__(data):
		'''
		Creates an empty np.array

		:param data: packed data
		:return: empty array with the correct size
		'''
		shape, dtype = data['shape'], data['dtype']
		return np.empty(shape, dtype)
	
	@staticmethod
	def __pack__(obj):
		'''
		Pack the np.array data.

		Note: that the information necessary for creating thet instance (shape, dtype) is not packed,
		but still valid json objects

		:param obj: instance of numpy.ndarray to be packed
		:return: packed data
		'''
		
		data = {}
		
		data['shape'] = list(obj.shape)
		data['dtype'] = obj.dtype.name
		
		data['data'] = pack_member(obj.tolist())
		
		return data
	
	@staticmethod
	def __unpack__(obj, data):
		'''
		Unpack the data and save the data to the created object

		:param obj: instance with empty data to populate with the unpacked data
		:param data: packed data
		:return: None
		'''
		
		obj[:] = np.array(unpack_member(data['data']), dtype=data['dtype'])


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
	
	def __pack__(self):  # save everything from the internal state
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


class Array(ObjectWrapper):
	'''
	This is an example of how to use the `ObjectWrapper`.
	Wraps numpy arrays.

	WARNING: it is NOT recommended to use this wrapper for numpy arrays (they are already registered).
	'''
	
	def begin(self):
		super().begin()
		if self.dtype.name == 'object':
			for el in self.flat:
				if isinstance(el, Transactionable):
					el.begin()
	
	def commit(self):
		super().commit()
		if self.dtype.name == 'object':
			for el in self.flat:
				if isinstance(el, Transactionable):
					el.commit()
	
	def abort(self):
		super().abort()
		if self.dtype.name == 'object':
			for el in self.flat:
				if isinstance(el, Transactionable):
					el.abort()
		
	
	def __pack__(self):
		'''
		Pack data to restore numpy array.
		
		:return: packed data
		'''
		data = {
			'dtype': pack_member(self.dtype.name),
			'data': pack_member(self.tolist()),
			'shape': pack_member(self.shape),
		}
		
		return data
	
	def __build__(self, data=None):
		'''
		Restore state of numpy array by unpacking data
		
		:param data: packed data
		:return: restored state
		'''
		return np.array(unpack_member(data['data']), dtype=unpack_member(data['dtype']))



