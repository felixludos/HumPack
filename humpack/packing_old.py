
from typing import Any, Union, Dict, List, Set, Tuple, NoReturn, ClassVar

import time
from .errors import SavableClassCollisionError, ObjectIDReadOnlyError, UnregisteredClassError

primitive = (type(None), str, int, float, bool) # all json readable and no sub elements

_savable_id_attr = '_pack_id' # instances of all subclasses cant use this identifier as an attribute
_py_cls_codes = {dict: '_dict', list: '_list', set: '_set', tuple: '_tuple'}
_py_code_cls = {v: k for k, v in _py_cls_codes.items()}
_ref_prefix = '<>'

class Packable(object):
	'''
	Any subclass of this mixin can be serialized using `pack`
	'''
	__subclasses = {}
	__obj_id_counter = 0
	
	# temporary data for saving/loading
	__obj_table = None
	__ref_table = None
	__py_table = None
	
	def __init_subclass__(cls, *args, **kwargs):
		'''
		This method automatically registers any subclass that is declared.
		
		:param args:
		:param kwargs:
		:return:
		'''
		super().__init_subclass__()
		name = cls._full_name(cls)
		if name in cls.__subclasses:
			raise SavableClassCollisionError(name, cls)
		cls.__subclasses[name] = cls
	
	def __new__(cls, *args, _gen_id=True, **kwargs):
		obj = super().__new__(cls)
		if _gen_id:
			obj.__dict__[_savable_id_attr] = cls.__gen_obj_id() # all instances of Packable have a unique obj_id
		return obj
	
	def __setattr__(self, key: str, value: Any):
		# if key == self.__class__._savable_id_attr:
		if key == _savable_id_attr:
			raise ObjectIDReadOnlyError()
		return super().__setattr__(key, value)
	
	@staticmethod
	def _full_name(cls: ClassVar) -> str:
		name = str(cls.__name__)
		module = str(cls.__module__)
		if module is None:
			return name
		return '.'.join([module, name])
	
	@staticmethod
	def __gen_obj_id() -> int:
		ID = Packable.__obj_id_counter  # TODO: make thread safe (?)
		Packable.__obj_id_counter += 1
		return ID
	
	@classmethod
	def get_cls(cls, name: str) -> ClassVar:
		try:
			return cls.__subclasses[name]
		except KeyError:
			raise UnregisteredClassError(name)
	
	@classmethod
	def pack(cls, obj: 'SERIALIZABLE', meta: Dict[str,'PACKED'] = None, include_timestamp: bool = False) -> 'JSONABLE':
		
		# savefile contains
		assert cls.__ref_table is None, 'There shouldnt be a object table already here'
		cls.__ref_table = {}  # create object table
		cls.__py_table = {}
		
		out = cls._pack_obj(obj)
		
		# additional meta info
		if meta is None:
			meta = {}
		if include_timestamp:
			meta['timestamp'] = time.strftime('%Y-%m-%d_%H%M%S')
		
		data = {
			'table': cls.__ref_table,
			'meta': meta,
		}
		
		cls.__ref_table = None  # clear built up object table
		cls.__py_table = None
		
		# save parent object separately
		data['head'] = out
		
		return data
	
	@classmethod
	def unpack(cls, data: 'PACKED', return_meta: bool = False) -> 'SERIALIZABLE':
		# add the current cls.__ID_counter to all loaded objs
		cls.__ref_table = data['table']
		cls.__obj_table = {}
		
		obj = cls._unpack_obj(data['head'])
		
		cls.__ref_table = None
		cls.__obj_table = None
		
		if return_meta:
			return obj, data['meta']
		return obj
	
	@classmethod
	def _pack_obj(cls, obj: 'SERIALIZABLE') -> 'PACKED':
		refs = cls.__ref_table
		pys = cls.__py_table
		
		if isinstance(obj, primitive):
			if isinstance(obj, str) and obj.startswith(_ref_prefix):
				ref = cls.__gen_obj_id()
				refs[ref] = {'_type': '_str', '_data': obj}
			else:
				return obj
		elif isinstance(obj, Packable):
			# if refs is not None:
			ref = obj._getref()
			if ref not in refs:
				refs[ref] = None # create entry in refs to stop reference loops
				refs[ref] = {'_type': Packable._full_name(type(obj)), '_data': obj.__pack__()}
		elif type(obj) in _py_cls_codes:  # known python objects
			ID = id(obj)
			if ID not in pys:
				pys[ID] = cls.__gen_obj_id()
			ref = pys[ID]
			
			if ref not in refs:
				data = {}
				
				refs[ref] = data
				
				if type(obj) == dict:
					data['_data'] = {cls._pack_obj(k): cls._pack_obj(v) for k, v in obj.items()}
				else:
					data['_data'] = [cls._pack_obj(x) for x in obj]
				data['_type'] = _py_cls_codes[type(obj)]
		
		elif issubclass(obj, Packable):
			return '{}:{}'.format(_ref_prefix, Packable._full_name(obj))
		
		elif obj in _py_cls_codes:
			return '{}:{}'.format(_ref_prefix, obj.__name__)
		
		else:
			raise TypeError('Unrecognized type: {}'.format(type(obj)))
		
		return '{}{}'.format(_ref_prefix, ref)
	
	@classmethod
	def _unpack_obj(cls, data: 'PACKED') -> 'SERIALIZABLE':
		refs = cls.__ref_table
		objs = cls.__obj_table
		
		if isinstance(data, str) and data.startswith(_ref_prefix):  # reference or class
			
			if ':' in data:  # class
				
				cls_name = data[len(_ref_prefix) + 1:]
				
				try:
					return cls.get_cls(cls_name)
				except UnregisteredClassError:
					return eval(cls_name)
			
			else:  # reference
				
				ID = int(data[len(_ref_prefix):])
				
				if ID in objs:
					return objs[ID]
				
				typ = refs[ID]['_type']
				data = refs[ID]['_data']
				
				if typ == '_str':
					obj = refs[ID]['_data']
				elif typ == '_tuple':  # since tuples are immutable they have to created right away (no loop issues)
					obj = tuple(cls._unpack_obj(x) for x in data)
				elif typ in _py_code_cls:
					obj = _py_code_cls[typ]()
				else:  # must be an instance of Packable
					new = cls.get_cls(typ)
					obj = new.__new__(new,
					                  data=data)  # use data carefully (usually not at all, unless __new__ requires args)
				
				del refs[ID]
				objs[ID] = obj
				
				# after adding empty obj to obj table, populate obj with state from data
				if typ in _py_code_cls:
					if typ == '_dict':
						obj.update({cls._unpack_obj(k): cls._unpack_obj(v) for k, v in data.items()})
					elif typ == '_set':
						obj.update(cls._unpack_obj(x) for x in data)
					elif typ == '_list':
						obj.extend(cls._unpack_obj(x) for x in data)
					elif typ == '_tuple':
						pass # already loaded
					else:
						raise TypeError('Unrecognized type {}: {}'.format(type(obj) ,obj))
				elif isinstance(obj, Packable):
					obj.__unpack__(data)
		
		else:
			assert isinstance(data, primitive), '{}, {}'.format(type(data), data)
			obj = data
		
		return obj
	
	def _getref(self) -> int:
		'''
		Returns the unique ID of `self`
		
		:return: the unique ID to this instance (ie. `self`)
		'''
		return self.__dict__[_savable_id_attr]
	
	def __deepcopy__(self, memodict: Dict[Any,Any] = None) -> Any:
		'''
		Produces a deep copy of the data by packing and repacking.
		
		:param memodict: Unused
		:return: A deep copy of self
		'''
		return self.__class__.unpack(self.__class__.pack(self))
	
	def __pack__(self) -> Dict[str,'PACKED']:
		'''
		Collect all data in self necessary to store the state.
		
		.. warning:: All data must be "packed" storing it. This is done by passing the data into
		`Packable._pack_obj` and using what is returned.
		
		:return: A dict of packed data necessary to recover the state of self.
		'''
		raise NotImplementedError
	
	def __unpack__(self, data: Dict[str, 'PACKED']) -> NoReturn:
		'''
		Using `data`, recover the packed state.
		Must be overridden by all subclasses.
		
		.. warning:: All data must be "unpacked" before using it. This is done by passing the data into
		`Packable._unpack_obj` and using what is returned.
		
		:param data: The information that is returned by `__pack__`.
		:return: Nothing. Once returned, the object should be in the same state as when it was packed.
		'''
		raise NotImplementedError

PRIMITIVE = Union[primitive]
'''Valid primitives'''

SERIALIZABLE = Union[Packable, PRIMITIVE, Dict['SERIALIZABLE', 'SERIALIZABLE'],
                     List['SERIALIZABLE'], Set['SERIALIZABLE'], Tuple['SERIALIZABLE']]
'''Types that can be serialized using `pack`'''

JSONABLE = Union[Dict[str,'JSONABLE'], List['JSONABLE'], PRIMITIVE]
'''Any object that is valid in json (eg. using `json.dumps`)'''

PACKED = Union[PRIMITIVE, List['PACKED'], Dict['PACKED', 'PACKED']]
'''Any information that is valid json and can be unpacked to recover the state of `Packable` subclasses.'''

def pack(obj: SERIALIZABLE) -> JSONABLE:
	'''
	Serialize `obj`
	
	:param obj: data to be serialized
	:return: serialized data
	'''
	return Packable.pack(obj)

def unpack(data: JSONABLE) -> SERIALIZABLE:
	'''
	Use data to unserialize and recover object
	
	:param data: data
	:return:
	'''
	return Packable.unpack(data)

