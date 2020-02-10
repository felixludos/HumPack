
try:
	import numpy as np
except:
	print('No numpy found') # use logging instead

from typing import Any
from wrapt import ObjectProxy

from .packing import Packable
from .transactions import Transactionable
from .basic_containers import tdict, tset, tlist

# all wrapped objects must be able to be copied (shallow copy) using
# note: Transactionable objects cant be wrapped
class ObjectWrapper(Transactionable, Packable, ObjectProxy):
	
	def __new__(cls, *args, **kwargs):
		obj = super().__new__(cls, _gen_id=False) # delay adding a pack_id until after initialization
		return obj
	
	def __init__(self, obj):
		super().__init__(obj)
		
		self._self_pack_id = Packable._Savable__gen_obj_id()
		
		self._self_shadow = None
		self._self_children = tset()
	
	def _getref(self):
		return self._self_pack_id
	
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
	
	# def __getattribute__(self, item):
	# 	if item in super().__getattribute__('_self_special_attrs'):
	# 		return
	
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
		raise NotImplementedError
	
	def __build__(self, data): # recover wrapped object in correct state from data, return wrapped object
		raise NotImplementedError


class Array(ObjectWrapper):
	'''
	Wraps numpy arrays.
	'''
	
	def __pack__(self):
		pack = type(self)._pack_obj
		
		data = {}
		
		data['dtype'] = pack(self.dtype.name)
		data['data'] = pack(self.tolist())
		
		return data
	
	def __build__(self, data=None):
		unpack = type(self)._unpack_obj
		return np.array(unpack(data['data']), dtype=unpack(data['dtype']))

