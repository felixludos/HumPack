
from typing import Any, Union, Dict, List, Set, Tuple, NoReturn, ClassVar
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
		name = _packable_names[cls]
	elif cls in _py_cls:
		name = _py_cls[cls]
	else:
		raise TypeError('Unknown class: {}'.format(cls))
	
	return '{}:{}'.format(_ref_prefix, name)

_packable_registry = {}
_packable_cls = {}
_packable_item = namedtuple('Packable_Item', ['name', 'cls', 'pack_fn', 'unpack_fn'])

def get_cls(name: str) -> ClassVar:
	try:
		return _packable_registry[name].cls
	except KeyError:
		raise UnregisteredClassError(name)

def register_packable(cls, pack_fn, unpack_fn, name=None):
	if name is None:
		name = _full_name(cls)
		
	if name in _packable_cls:
		raise SavableClassCollisionError(name, cls)

	item = _packable_item(name, cls, pack_fn, unpack_fn)
	_packable_registry[name] = item
	_packable_cls[cls] = item

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
		register_packable(cls, cls.__pack__, cls.__unpack__)

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

def pack_data(obj: 'SERIALIZABLE', force_str: bool = False) -> 'PACKED':
	# refs = _ref_table
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
				data['_data'] = {pack_data(k, force_str=True): pack_data(v) for k, v in obj.items()}
			elif typ == range:
				data['_data'] = {'start': obj.start, 'stop': obj.stop, 'step': obj.step}
			elif typ == complex:
				data['_data'] = [obj.real, obj.imag]
			elif typ == bytes:
				data['_data'] = obj.decode('latin1')
			else:
				data['_data'] = [pack_data(x) for x in obj]
			data['_type'] = _py_cls2name[typ]
		else:
			raise TypeError('Unrecognized type: {}'.format(type(obj)))
	
	return ref

def unpack_data(data: 'PACKED') -> 'SERIALIZABLE':

	if isinstance(data, str) and data.startswith(_ref_prefix):  # reference or class

		if ':' in data:  # class
			
			cls_name = data[len(_ref_prefix) + 1:]
			
			try:
				return cls.get_cls(cls_name)
			except UnregisteredClassError:
				return eval(cls_name)
		
		elif data in _obj_table:  # reference
			return _obj_table[data]

		else:
			ref = data
			typname = _ref_table[ref]['_type']
			data = _ref_table[ref]['_data']
			
			if typname in {'str', 'int', 'float', 'bool'}:
				obj = data
			elif typname == 'tuple':  # since tuples are immutable they have to created right away (no loop issues)
				obj = tuple(unpack_data(x) for x in data)
			elif typname == 'range':
				obj = range(data['start'], data['stop'], data['step'])
			elif typname == 'bytes':
				obj = data.encode('latin1')
			elif typname == 'complex':
				obj = complex(data['real'], data['imag'])
			elif typname in _py_name2cls:
				obj = _py_name2cls[typname]()
			else:  # must be an instance of Packable
				new = get_cls(typname)
				# use data carefully (usually not at all, unless __new__ requires args)
				obj = new.__new__(new, data=data)
			
			del _ref_table[ref]
			_obj_table[ref] = obj

			# after adding empty obj to obj table, populate obj with state from data
			if typname == 'dict':
				obj.update({unpack_data(k): unpack_data(v) for k, v in data.items()})
			elif typname == 'set':
				obj.update(unpack_data(x) for x in data)
			elif typname == 'list':
				obj.extend(unpack_data(x) for x in data)
			elif typname in _packable_registry:
				_packable_registry[typname].unpack_fn(obj, data)
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


def pack(obj: SERIALIZABLE, meta: Dict[str, PACKED] = None, include_timestamp: bool = False) -> JSONABLE:
	global _ref_table
	_ref_table = {}

	try:
		out = pack_data(obj)

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

def unpack(data: PACKED, return_meta: bool = False) -> SERIALIZABLE:
	# add the current cls.__ID_counter to all loaded objs
	global _ref_table, _obj_table
	_ref_table = data['table'].copy()
	_obj_table = {}

	try:
		obj = unpack_data(data['head'])
	except Exception as e:
		raise e
	finally:
		_ref_table = None
		_obj_table = None

	if return_meta:
		return obj, data['meta']
	return obj


def pack_json(obj, include_timestamp=False):
	return json.dumps(pack(obj, include_timestamp=include_timestamp))

def unpack_json(data, return_meta=False):
	return unpack(json.loads(data), return_meta=return_meta)


