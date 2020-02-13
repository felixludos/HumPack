
try:
	import numpy as np
except ImportError:
	print('WARNING: unable to import numpy')
from .packing import Packable, pack_data, unpack_data


class Array(Packable, use_cls=np.ndarray):
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
		
		data['data'] = pack_data(obj.tolist())
		
		return data
	
	@staticmethod
	def __unpack__(obj, data):
		'''
		Unpack the data and save the data to the created object

		:param obj: instance with empty data to populate with the unpacked data
		:param data: packed data
		:return: None
		'''
		
		obj[:] = np.array(unpack_data(data['data']), dtype=data['dtype'])



