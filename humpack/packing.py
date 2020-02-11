
from typing import Any, Union, Dict, List, Set, Tuple, NoReturn, ClassVar

from _collections import namedtuple
import time
from .errors import SavableClassCollisionError, ObjectIDReadOnlyError, UnregisteredClassError

primitive = (str, int, float, bool, ) # all json readable and no sub elements
all_primitives = type(None), *primitive

py_containers = (dict, list, set, tuple, range, bytes, complex)

_py_cls = {c: c.__name__ for c in (*all_primitives, *py_containers)}
_py_names = {n: c for c, n in _py_cls.items()}

def _full_name(cls: ClassVar) -> str:
	name = str(cls.__name__)
	module = str(cls.__module__)
	if module is None:
		return name
	return '.'.join([module, name])

_ref_prefix = '<>'
def _get_obj_id(obj: 'SERIALIZABLE') -> str:
	'''
	Compute the object ID for packing objects, which must be unique and use the reference prefix
	
	:param obj:
	:return: unique ID associated with `obj` for packing
	'''
	return '{}{}'.format(_ref_prefix, id(obj))

def _get_cls_id(cls: ClassVar) -> str:
	'''
	Compute the object ID for packing classes, which must be unique and use the reference prefix

	:param cls: class to be packed
	:return: unique ID associated with `cls` for packing
	'''
	if cls in _packable_subclass_names:
		name = _packable_subclass_names[cls]
	elif cls in _py_cls:
		name = _py_cls[cls]
	else:
		raise TypeError('Unknown class: {}'.format(cls))
	
	return '{}:{}'.format(_ref_prefix, name)

_packable_cls = {}
_packable_names = {}
def get_cls(name: str) -> ClassVar:
	try:
		return _packable_cls[name]
	except KeyError:
		raise UnregisteredClassError(name)

_packable_registry = {}
_packable_item = namedtuple('Packable_Item', ['pack_fn', 'unpack_fn'])
def register_packable(cls, pack_fn, unpack_fn, name=None):
	if name is None:
		name = cls.__name__
		
	if name in _packable_cls:
		raise SavableClassCollisionError(name, cls)
	
	_packable_registry[name] = _packable_item(pack_fn, unpack_fn)
	_packable_cls[name] = cls
	_packable_names[cls] = name

def Pack(pack_fn, unpack_fn, name=None):
	def _register(cls):
		nonlocal pack_fn, unpack_fn, name
		register_packable(cls=cls, pack_fn=pack_fn, unpack_fn=unpack_fn, name=name)
		return cls
	return _register


class Packable(object):
	'''
	Any subclass of this mixin can be serialized using `pack`
	'''
	def __init_subclass__(cls, *args, **kwargs):
		'''
		This method automatically registers any subclass that is declared.
		
		:param args:
		:param kwargs:
		:return:
		'''
		super().__init_subclass__()
		name = _full_name(cls)
		if name in _packable_cls: # TODO: this should be a warning
			raise SavableClassCollisionError(name, cls)
		_packable_subclasses[name] = cls
		_packable_subclass_names[cls] = name

	
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

_ref_table = None
_obj_table = None

def pack(obj: 'SERIALIZABLE', meta: Dict[str, 'PACKED'] = None, include_timestamp: bool = False) -> 'JSONABLE':
	
	_ref_table = {}
	
	out = pack_data(obj)
	
	# additional meta info
	if meta is None:
		meta = {}
	if include_timestamp:
		meta['timestamp'] = time.strftime('%Y-%m-%d_%H%M%S')
	
	data = {
		'table': _ref_table,
		'meta': meta,
	}
	
	# save parent object separately
	data['head'] = out
	
	return data

def unpack(data: 'PACKED', return_meta: bool = False) -> 'SERIALIZABLE':
	# add the current cls.__ID_counter to all loaded objs
	_ref_table = data['table']
	_obj_table = {}
	
	obj = unpack_data(data['head'])
	
	_ref_table = None
	_obj_table = None
	
	if return_meta:
		return obj, data['meta']
	return obj

def pack_data(obj: 'SERIALIZABLE', force_str: bool = False) -> 'PACKED':
	# refs = _ref_table
	if isinstance(obj, all_primitives):
		if isinstance(obj, str) and obj.startswith(_ref_prefix):
			ref = _get_obj_id(obj)
			_ref_table[ref] = {'_type': _py_cls[type(obj)], '_data': obj}
		elif force_str and not isinstance(obj, str):
			ref = _get_obj_id(obj)
			_ref_table[ref] = {'_type': _py_cls[type(obj)], '_data': obj}
		else:
			return obj
	else:
		ref = _get_obj_id(obj)
		typ = type(obj)
		
		if isinstance(obj, Packable):
			if ref not in _ref_table:
				_ref_table[ref] = None  # create entry in refs to stop reference loops
				_ref_table[ref] = {'_type': _packable_names[typ],
				                    '_data': obj.__pack__()}  # TODO: maybe run _pack_obj to be safe
		elif typ in _py_cls:  # known python types
			if ref not in _ref_table:
				data = {}
				
				_ref_table[ref] = data
				
				if typ == dict:
					data['_data'] = {pack_data(k, force_str=True): pack_data(v)
					                 for k, v in obj.items()}
				elif typ == range:
					data['_data'] = {'start': obj.start, 'stop': obj.stop, 'step': obj.step}
				elif typ == complex:
					data['_data'] = str(obj)
				elif typ == bytes:
					data['_data'] = 
				else:
					data['_data'] = [pack_data(x) for x in obj]
				data['_type'] = _py_names[typ]
		
		elif issubclass(obj, Packable):
			return _get_cls_id(obj)
		
		elif obj in _py_cls:
			return '{}:{}'.format(_ref_prefix, obj.__name__)
		
		else:
			raise TypeError('Unrecognized type: {}'.format(type(obj)))
	
	return '{}{}'.format(_ref_prefix, ref)

def unpack_data(data: 'PACKED') -> 'SERIALIZABLE':
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
					pass  # already loaded
				else:
					raise TypeError('Unrecognized type {}: {}'.format(type(obj), obj))
			elif isinstance(obj, Packable):
				obj.__unpack__(data)
	
	else:
		assert isinstance(data, primitive), '{}, {}'.format(type(data), data)
		obj = data
	
	return obj

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

