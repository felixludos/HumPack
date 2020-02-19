
from typing import Any, Union, Dict, List, Set, Tuple, NoReturn, ClassVar, TextIO, Callable, NewType
import json
from collections import namedtuple
import time
from .errors import SavableClassCollisionError, ObjectIDReadOnlyError, UnregisteredClassError

primitive = (str, int, float, bool, type(None)) # all json readable and no sub elements
# all_primitives = , *primitive

py_types = (bytes, complex, range, tuple)
py_containers = (dict, list, set)

_py_cls2name = {c: c.__name__ for c in (*primitive, *py_types, *py_containers)}
_py_name2cls = {n: c for c, n in _py_cls2name.items()}

def _full_name(cls: ClassVar) -> str:
	'''
	Find the full, unique name of a class by connecting it to the module where is is declared.
	
	:param cls: type
	:return: unique name of the class
	'''
	name = str(cls.__name__)
	module = str(cls.__module__)
	if module is None:
		return name
	return '.'.join([module, name])


_packable_registry = {}
_packable_cls = {}
_packable_item = namedtuple('Packable_Item', ['name', 'cls', 'pack_fn', 'create_fn', 'unpack_fn'])


_ref_prefix = '<>'
def _get_obj_id(obj: 'SERIALIZABLE') -> str:
	'''
	Compute the object ID for packing objects, which must be unique and use the reference prefix

	:param obj: object to get the reference for
	:return: unique ID associated with `obj` for packing
	'''
	
	if type(obj) == type:
		return _get_cls_id(obj)
	
	return '{}{}'.format(_ref_prefix, id(obj))

def _get_cls_id(cls: ClassVar) -> str:
	'''
	Compute the object ID for packing classes, which must be unique and use the reference prefix

	:param cls: class to be packed
	:return: unique ID associated with `cls` for packing
	'''
	if cls in _packable_cls:
		name = _packable_cls[cls].name
	elif cls in _py_cls2name:
		name = _py_cls2name[cls]
	else:
		raise TypeError('Unknown class: {}'.format(cls))
	
	return '{}:{}'.format(_ref_prefix, name)

def get_cls(name: str) -> ClassVar:
	'''
	Get the registered type from the registered name
	
	:param name:
	:return:
	'''
	if name in _py_name2cls:
		return _py_name2cls[name]
	
	try:
		return _packable_registry[name].cls
	except KeyError:
		raise UnregisteredClassError(name)

def get_cls_from_ref(name: str) -> ClassVar:
	'''
	Recover the registered type from the reference thereof
	
	:param name: reference to a registered type
	:return: type
	'''
	name = name[len(_ref_prefix) + 1:]
	return get_cls(name)

def register_packable(cls: ClassVar, pack_fn: Callable, create_fn: Callable, unpack_fn: Callable,
                      name: str = None) -> NoReturn:
	'''
	Register a type to be packable. Requires a pack_fn, create_fn, and unpack_fn to store and restore object state.
	
	:param cls: type to be registered
	:param pack_fn: callable input is an instance of the type, and packs all data necessary to recover the state
	:param create_fn: callable input is the expected type and the packed data, creates a new instance of the type,
	without unpacking any packed data (to avoid reference loops)
	:param unpack_fn: callable input is the instance of packed data and then restores that instance to the original
	state using the packed data by unpacking any values therein.
	:param name: (optional) name of the class used for storing
	:return: A `SavableClassCollisionError` if the name is already registered
	'''
	
	if name is None:
		name = _full_name(cls)
		
	if name in _packable_cls:
		raise SavableClassCollisionError(name, cls)

	item = _packable_item(name, cls, pack_fn, create_fn, unpack_fn)
	_packable_registry[name] = item
	_packable_cls[cls] = item

class Packable(object):
	'''
	Any subclass of this mixin can be serialized using `pack`
	
	All subclasses must implement __create__, __pack__, and __unpack__ to register the type. By passing a type to
	`use_cls` the type for which these methods are used can be overridden from the subclass.
	'''
	def __init_subclass__(cls, use_cls: ClassVar = None, name: str = None) -> NoReturn:
		'''
		This method automatically registers any subclass that is declared.
		
		:param use_cls: The class to register (if it is different than `cls`)
		:return: None
		'''
		super().__init_subclass__() # TODO: remove
		
		if use_cls is None:
			use_cls = cls
		
		register_packable(use_cls, cls.__pack__, cls.__create__, cls.__unpack__, name=name)

	def __deepcopy__(self, memodict: Dict[Any,Any] = None) -> Any:
		'''
		Produces a deep copy of the data by packing and repacking.
		
		:param memodict: Unused
		:return: A deep copy of self
		'''
		return unpack(pack(self))
	
	@classmethod
	def __create__(cls, data: Dict[str, 'PACKED']) -> 'Packable':
		'''
		Create the object without loading the state from data. You can use the data to inform how
		to initialize the object, however no stored objects should be unpacked (to avoid reference loops)
		
		:param data: packed data to restore object state, should NOT be unpacked here
		:return: A fresh instance of the class registered with this create_fn
		'''
		return cls.__new__(cls)
	
	def __pack__(self) -> Dict[str,'PACKED']:
		'''
		Collect all data in self necessary to store the state.
		
		.. warning:: All data must be "packed" storing it. This is done by passing the data into
		`Packable._pack_obj` and using what is returned.
		
		:return: A dict of packed data necessary to recover the state of self
		'''
		raise NotImplementedError
	
	def __unpack__(self, data: Dict[str, 'PACKED']) -> NoReturn:
		'''
		Using `data`, recover the packed state.
		Must be overridden by all subclasses.
		
		.. warning:: All data must be "unpacked" before using it. This is done by passing the data into
		`Packable._unpack_obj` and using what is returned.
		
		:param data: The information that is returned by `__pack__`.
		:return: Nothing. Once returned, the object should be in the same state as when it was packed
		'''
		raise NotImplementedError


PRIMITIVE = Union[primitive]
'''Valid primitives'''
#
# SERIALIZABLE = Union[Packable, PRIMITIVE, Dict['SERIALIZABLE', 'SERIALIZABLE'],
#                      List['SERIALIZABLE'], Set['SERIALIZABLE'], Tuple['SERIALIZABLE']]
# '''Types that can be serialized using `pack`'''
#
# JSONABLE = Union[Dict[str,'JSONABLE'], List['JSONABLE'], PRIMITIVE]
# '''Any object that is valid in json (eg. using `json.dumps`)'''
#
# PACKED = Union[PRIMITIVE, List['PACKED'], Dict['PACKED', 'PACKED']]
# '''Any information that is valid json and can be unpacked to recover the state of `Packable` subclasses.'''



SERIALIZABLE = NewType('SERIALIZABLE', object)
JSONABLE = NewType('JSONABLE', object)
PACKED = NewType('PACKED', object)


_ref_table = None
_obj_table = None

def pack_member(obj: 'SERIALIZABLE', force_str: bool = False) -> PACKED:
	'''
	Store the object state by packing it, possibly returning a reference.
	
	This function should be called inside implemented __pack__ on all data in an object necessary to restore
	the object state.
	
	Note: this function should not be called on the top level (use `pack` instead).
	
	:param obj: serializable data that should be packed
	:param force_str: if the data is a key for a dict, set this to true to ensure the key is a str
	:return: packed data
	'''
	if isinstance(obj, primitive):
		if (isinstance(obj, str) and obj.startswith(_ref_prefix)) or (not isinstance(obj, str) and force_str):
			ref = _get_obj_id(obj)
			_ref_table[ref] = {'_type': _py_cls2name[type(obj)], '_data': obj}
		elif force_str and not isinstance(obj, str):
			ref = _get_obj_id(obj)
			_ref_table[ref] = {'_type': _py_cls2name[type(obj)], '_data': obj}
		else:
			return obj
	else:
		ref = _get_obj_id(obj)
		typ = type(obj)

		if ref in _ref_table or typ == type:
			return ref
		data = {}
		_ref_table[ref] = data  # create entry in refs to stop reference loops
		if typ in _packable_cls:
			info = _packable_cls[typ]

			data['_type'] = info.name
			data['_data'] = info.pack_fn(obj)

		elif typ in _py_cls2name:  # known python types
			if typ == dict:
				data['_data'] = {pack_member(k, force_str=True): pack_member(v) for k, v in obj.items()}
			elif typ == range:
				data['_data'] = {'start': obj.start, 'stop': obj.stop, 'step': obj.step}
			elif typ == complex:
				data['_data'] = [obj.real, obj.imag]
			elif typ == bytes:
				data['_data'] = obj.decode('latin1')
			else:
				data['_data'] = [pack_member(x) for x in obj]
			data['_type'] = _py_cls2name[typ]
		else:
			raise TypeError('Unrecognized type: {}'.format(type(obj)))
	
	return ref

def unpack_member(data: 'PACKED') -> 'SERIALIZABLE':
	'''
	Restore the object data by unpacking it.
	
	This function should be called inside implemented __unpack__ on all data in an object necessary to restore
	the object state from the packed data.
	
	Note: this function should not be called on the top level (use `unpack` instead).
	
	:param data: packed data that should be unpacked
	:return: unpacked data to restore the state
	'''

	if isinstance(data, str) and data.startswith(_ref_prefix):  # reference or class

		if ':' in data:  # class
			return get_cls_from_ref(data)
		
		elif data in _obj_table:  # reference
			return _obj_table[data]

		else:
			ref = data
			typname = _ref_table[ref]['_type']
			data = _ref_table[ref]['_data']
			item = None
			
			if typname in {'str', 'int', 'float', 'bool'}:
				obj = data
			elif typname == 'tuple':  # since tuples are immutable they have to created right away (no loop issues)
				obj = tuple(unpack_member(x) for x in data)
			elif typname == 'range':
				obj = range(data['start'], data['stop'], data['step'])
			elif typname == 'bytes':
				obj = data.encode('latin1')
			elif typname == 'complex':
				obj = complex(*data)
			elif typname in _py_name2cls:
				obj = _py_name2cls[typname]()
			else:  # must be an instance of Packable
				item = _packable_registry[typname]
				obj = item.create_fn(data)
				
			del _ref_table[ref]
			_obj_table[ref] = obj

			# after adding empty obj to obj table, populate obj with state from data
			if typname == 'dict':
				obj.update({unpack_member(k): unpack_member(v) for k, v in data.items()})
			elif typname == 'set':
				obj.update(unpack_member(x) for x in data)
			elif typname == 'list':
				obj.extend(unpack_member(x) for x in data)
			elif item is not None:
				item.unpack_fn(obj, data)
	else:
		assert isinstance(data, primitive), '{}, {}'.format(type(data), data)
		obj = data
	
	return obj

def pack(obj: 'SERIALIZABLE', meta: Dict[str, 'PACKED'] = None, include_timestamp: bool = False) -> 'JSONABLE':
	'''
	Serializes any object, returning a json object that can be converted to a json string.
	
	:param obj: Object to be serialized
	:param meta: Meta information, must be jsonable
	:param include_timestamp: include a timestamp in the meta information
	:return: packed data, which can be converted to a json string using json.dumps
	'''
	global _ref_table
	_ref_table = {}

	try:
		out = pack_member(obj)

		# additional meta info
		if meta is None:
			meta = {}
		if include_timestamp:
			meta['timestamp'] = time.strftime('%Y-%m-%d_%H%M%S')

		data = {
			'table': _ref_table,
			'meta': meta,
			'head': out, # save parent object separately
		}

	except Exception as e:
		raise e
	finally:
		_ref_table = None

	return data

def unpack(data: 'PACKED', return_meta: bool = False) -> 'SERIALIZABLE':
	'''
	Deserialize a packed object to recover the original state.
	
	:param data: serialized (packed) state of an object
	:param return_meta: return any meta information from the serialized data
	:return: the unpacked (restored) object
	'''
	# add the current cls.__ID_counter to all loaded objs
	global _ref_table, _obj_table
	_ref_table = data['table'].copy()
	_obj_table = {}

	try:
		obj = unpack_member(data['head'])
	except Exception as e:
		raise e
	finally:
		_ref_table = None
		_obj_table = None

	if return_meta:
		return obj, data['meta']
	return obj


def save_pack(obj: 'SERIALIZABLE', fp: TextIO, meta: Dict[str, 'JSONABLE'] = None,
              include_timestamp: bool = False) -> NoReturn:
	'''
	Pack (serialize) the object and store it as a json file
	
	:param obj: object to be packed
	:param fp: writable file-like object where the packed object is stored
	:param include_timestamp: include timestamp in meta information
	:return: None
	'''
	return json.dump(pack(obj, meta=meta, include_timestamp=include_timestamp), fp)

def load_pack(fp: TextIO, return_meta: bool = False) -> 'SERIALIZABLE':
	'''
	Loads json file of packed object and unpacks the object
	
	:param fp: writable file-like object
	:param return_meta: return the meta information stored
	:return: unpacked object from json file
	'''
	return unpack(json.load(fp), return_meta=return_meta)


def json_pack(obj: 'SERIALIZABLE', meta: Dict[str, 'JSONABLE'] = None, include_timestamp:bool = False) -> str:
	'''
	Pack object and return a json string of the serialized object
	
	:param obj: to be packed
	:param meta: any meta information to include
	:param include_timestamp: include timestamp in meta information
	:return: json string of the serialized data
	'''
	return json.dumps(pack(obj, meta=meta, include_timestamp=include_timestamp))

def json_unpack(data: str, return_meta: bool = False) -> 'SERIALIZABLE':
	'''
	Unpack json string of a packed object.
	
	:param data: json string of a packed object
	:param return_meta: return meta information
	:return: unpacked object
	'''
	return unpack(json.loads(data), return_meta=return_meta)
