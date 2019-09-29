
import time
from .errors import SavableClassCollisionError, ObjectIDReadOnlyError, UnregisteredClassError

_primitives = (type(None), str, int, float, bool) # all json readable and no sub elements

_savable_id_attr = '_pack_id' # instances of all subclasses cant use this identifier as an attribute
_py_cls_codes = {dict: '_dict', list: '_list', set: '_set', tuple: '_tuple'}
_py_code_cls = {v: k for k, v in _py_cls_codes.items()}
_ref_prefix = '<>'

class Savable(object):
	__subclasses = {}
	__obj_id_counter = 0
	
	# temporary data for saving/loading
	__obj_table = None
	__ref_table = None
	__py_table = None
	
	def __init_subclass__(cls, *args, **kwargs):
		super().__init_subclass__()
		name = cls._full_name(cls)
		if name in cls.__subclasses:
			raise SavableClassCollisionError(name, cls)
		cls.__subclasses[name] = cls
	
	# cls._subclasses[cls.__name__] = cls
	
	def __new__(cls, *args, _gen_id=True, **kwargs):
		obj = super().__new__(cls)
		if _gen_id:
			obj.__dict__[_savable_id_attr] = cls.__gen_obj_id() # all instances of Savable have a unique obj_id
		return obj
	
	def __setattr__(self, key, value):
		# if key == self.__class__._savable_id_attr:
		if key == _savable_id_attr:
			raise ObjectIDReadOnlyError()
		return super().__setattr__(key, value)
	
	@staticmethod
	def _full_name(cls):
		name = cls.__name__
		module = cls.__module__
		if module is None:
			return name
		return '.'.join([module, name])
	
	@staticmethod
	def __gen_obj_id():
		ID = Savable.__obj_id_counter  # TODO: make thread safe (?)
		Savable.__obj_id_counter += 1
		return ID
	
	@classmethod
	def get_cls(cls, name):
		try:
			return cls.__subclasses[name]
		except KeyError:
			raise UnregisteredClassError(name)
	
	@classmethod
	def pack(cls, obj):  # top-level for dev/user to call
		
		# savefile contains
		assert cls.__ref_table is None, 'There shouldnt be a object table already here'
		cls.__ref_table = {}  # create object table
		cls.__py_table = {}
		
		out = cls._pack_obj(obj)
		
		# additional meta info
		meta = {}
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
	def unpack(cls, data, meta=False):
		# add the current cls.__ID_counter to all loaded objs
		cls.__ref_table = data['table']
		cls.__obj_table = {}
		
		obj = cls._unpack_obj(data['head'])
		
		cls.__ref_table = None
		cls.__obj_table = None
		
		if meta:
			return obj, data['meta']
		return obj
	
	@classmethod
	def _pack_obj(cls, obj):
		refs = cls.__ref_table
		pys = cls.__py_table
		
		if isinstance(obj, _primitives):
			if isinstance(obj, str) and obj.startswith(_ref_prefix):
				ref = cls.__gen_obj_id()
				refs[ref] = {'_type': '_str', '_data': obj}
			else:
				return obj
		elif isinstance(obj, Savable):
			# if refs is not None:
			ref = obj._getref()
			if ref not in refs:
				refs[ref] = None # create entry in refs to stop reference loops
				refs[ref] = {'_type': Savable._full_name(type(obj)), '_data': obj.__save__()}
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
		
		elif issubclass(obj, Savable):
			return '{}:{}'.format(_ref_prefix, Savable._full_name(obj))
		
		elif obj in _py_cls_codes:
			return '{}:{}'.format(_ref_prefix, obj.__name__)
		
		else:
			raise TypeError('Unrecognized type: {}'.format(type(obj)))
		
		return '{}{}'.format(_ref_prefix, ref)
	
	@classmethod
	def _unpack_obj(cls, data):
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
				else:  # must be an instance of Savable
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
				elif isinstance(obj, Savable):
					obj.__load__(data)
		
		else:
			assert isinstance(data, _primitives), '{}, {}'.format(type(data), data)
			obj = data
		
		return obj
	
	def _getref(self):
		return self.__dict__[_savable_id_attr]
	
	def __deepcopy__(self, memodict={}):
		return self.__class__.unpack(self.__class__.pack(self))
	
	# functions must be overridden => any information in an instance that should be saved/loaded that could be anything other than a primitive should be packed/unpacked using self.__class__.__pack and self.__class__.__unpack
	
	def __save__(self):  # should call self.__class__.__pack(obj) on all objects that are relevant to its state
		raise NotImplementedError
	
	def __load__(self, data):  # basically like a
		raise NotImplementedError

