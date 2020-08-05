
from collections import OrderedDict, deque
import heapq

from .utils import safe_self_execute
from .errors import LoadInitFailureError
from .packing import Packable, pack_member, unpack_member
from .transactions import Transactionable
from .hashing import Hashable

class Container(Transactionable, Packable, Hashable):
	pass


# keys must be primitives, values can be primitives or Packable instances/subclasses
class tdict(Container, OrderedDict):
	'''
	Humpack dictionary, replaces the standard dict
	Has all the same functionality of a dict, plus being Transactionable or Packable
	'''
	def __new__(cls, *args, **kwargs):
		
		self = super().__new__(cls)
		
		self.__dict__['_data'] = OrderedDict()
		self.__dict__['_shadow'] = None
		
		return self
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		self.__dict__['_data'] = OrderedDict(*args, **kwargs)
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			return
			self.commit()  # partial transactions are committed
		
		self._shadow = self._data
		self._data = self._data.copy()
		
		for child in self.values():  # if keys could be Transactionable instances: chain(self.keys(), self.values())
			if isinstance(child, Transactionable):
				child.begin()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		self._shadow = None
		for child in self.values():  # if keys could be Transactionable instances: chain(self.keys(), self.values())
			if isinstance(child, Transactionable):
				child.commit()
	
	def abort(self):
		if not self.in_transaction():
			return
		
		self._data = self._shadow
		self._shadow = None
		for child in self.values():  # if keys could be Transactionable instances: chain(self.keys(), self.values())
			if isinstance(child, Transactionable):
				child.abort()
	
	def todict(self):
		return {k:v for k,v in self.items()}
	
	def update(self, other):
		self._data.update(other)
	
	def fromkeys(self, keys, value=None):
		self._data.fromkeys(keys, value)
	
	def clear(self):
		self._data.clear()
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __len__(self):
		return len(self._data)
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	
	def __reversed__(self):
		return self._data.__reversed__()
	
	def __iter__(self):
		return iter(self._data)
	
	def keys(self):
		return self._data.keys()
	
	def values(self):
		return self._data.values()
	
	def items(self):
		return self._data.items()
	
	def pop(self, key):
		return self._data.pop(key)
	
	def popitem(self):
		return self._data.popitem()
	
	def move_to_end(self, key, last=True):
		self._data.move_to_end(key, last)
	
	def __pack__(self):
		
		data = {}
		
		data['_pairs'] = {}
		data['_order'] = []
		
		for key, value in self.items():
			k, v = pack_member(key, force_str=True), pack_member(value)
			data['_pairs'][k] = v
			data['_order'].append(k)
		
		if self.in_transaction():  # TODO: maybe write warning about saving in the middle of a transaction
			
			data['_shadow_pairs'] = {}
			data['_shadow_order'] = []
			
			for key, value in self._shadow.items():
				k, v = pack_member(key, force_str=True), pack_member(value)
				data['_shadow_pairs'][k] = v
				data['_shadow_order'].append(k)
		
		return data
	
	def __unpack__(self, data):
		
		# TODO: write warning about overwriting state - which can't be aborted
		# if self.in_transaction():
		# 	pass
		
		self.abort()
		self._data.clear()
		for key in data['_order']:
			self._data[unpack_member(key)] = unpack_member(data['_pairs'][key])
		
		if '_shadow_pairs' in data:  # TODO: maybe write warning about loading into a partially completed transaction
			self._shadow = OrderedDict()
			for key in data['_shadow_order']:
				self._shadow[unpack_member(key)] = unpack_member(data['_shadow_pairs'][key])
		
		return self
	
	def get(self, k, *args, **kwargs):
		return self._data.get(k, *args, **kwargs)
	
	def setdefault(self, key, default=None):
		self._data.setdefault(key, default)
	
	def __getitem__(self, item):
		return self._data[item]
	
	def __setitem__(self, key, value):  # TODO: write warning if key is not a primitive, subclass of Packable, or instance of Packable
		self._data[key] = value
	
	def __delitem__(self, key):
		del self._data[key]
	
	
	def __str__(self, default='{...}'):
		return safe_self_execute(self, lambda: 't{}{}{}'.format('{', ', '.join(str(key) for key in iter(self)), '}'),
		                         default=default, flag='self printed flag')
	
	def __repr__(self, default='{...}'):
		return safe_self_execute(self, lambda: 't{}{}{}'.format('{', ', '.join(
			('{}:{}'.format(repr(key), repr(value)) for key, value in self.items())), '}'),
		                         default=default, flag='self printed flag')

class adict(tdict):

	def __getattr__(self, item):
		if item in self.__dict__:
			return super().__getattribute__(item)
		return self.__getitem__(item)

	def __setattr__(self, key, value):
		if key in self.__dict__:
			return super().__setattr__(key, value)
		return self.__setitem__(key, value)

	def __delattr__(self, item):
		if item in self.__dict__:
			# raise Exception('{} cannot be deleted'.format(item))
			return super().__delattr__(item)
		return self.__delitem__(item)

class tlist(Container, list):
	'''
	Humpack list, replaces the standard list
	Has all the same functionality of a list, plus being Transactionable or Packable
	'''
	
	def __new__(cls, *args, **kwargs):
		
		self = super().__new__(cls)
		
		self._data = []
		self._shadow = None
		
		return self
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		self._data = list(*args, **kwargs)
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			return
			self.commit()  # partial transactions are committed
		
		self._shadow = self._data
		self._data = self._data.copy()
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.begin()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		self._shadow = None
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.commit()
	
	def abort(self):
		if not self.in_transaction():
			return
		
		self._data = self._shadow
		self._shadow = None
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.abort()
	
	def tolist(self):
		return [x for x in self]
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __pack__(self):
		state = {}
		state['_entries'] = [pack_member(elm) for elm in iter(self)]
		if self.in_transaction():  # TODO: maybe write warning about saving in the middle of a transaction
			state['_shadow'] = [pack_member(elm) for elm in self._shadow]
		return state
	
	def __unpack__(self, state):
		
		# TODO: write warning about overwriting state - which can't be aborted
		# if self.in_transaction():
		# 	pass
		
		self._data.extend(unpack_member(elm) for elm in state['_entries'])
		if '_shadow' in state:  # TODO: maybe write warning about loading into a partially completed transaction
			self._shadow = [unpack_member(elm) for elm in state['_shadow']]
	
	def __getitem__(self, item):
		if isinstance(item, slice):
			return tlist(self._data[item])
		return self._data[item]
	
	def __setitem__(self, key, value):
		self._data[key] = value
	
	def __delitem__(self, idx):
		del self._data[idx]
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)
	
	def count(self, object):
		return self._data.count(object)
	
	def append(self, item):
		return self._data.append(item)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	
	def extend(self, iterable):
		return self._data.extend(iterable)
	
	def insert(self, index, object):
		self._data.insert(index, object)
	
	def remove(self, value):
		self._data.remove(value)
	
	def __iter__(self):
		return iter(self._data)
	
	def __reversed__(self):
		return self._data.__reversed__()
	
	def reverse(self):
		self._data.reverse()
	
	def pop(self, index=None):
		if index is None:
			return self._data.pop()
		return self._data.pop(index)
	
	def __len__(self):
		return len(self._data)
	
	def clear(self):
		self._data.clear()
	
	def sort(self, key=None, reverse=False):
		self._data.sort(key=key, reverse=reverse)
	
	def index(self, object, start=None, stop=None):
		self._data.index(object, start, stop)
	
	def __mul__(self, other):
		return tlist(self._data.__mul__(other))
	
	def __rmul__(self, other):
		return tlist(self._data.__rmul__(other))
	
	def __add__(self, other):
		out = self.copy()
		out.extend(other)
		return out
	
	def __iadd__(self, other):
		self._data.__iadd__(other)
	
	def __imul__(self, other):
		self._data.__imul__(other)
	
	def __str__(self, default='[...]'):
		return safe_self_execute(self, lambda: 't[{}]'.format(', '.join(map(str, self))),
		                         default=default, flag='self printed flag')
	
	def __repr__(self, default='[...]'):
		return safe_self_execute(self, lambda: 't[{}]'.format(', '.join(map(repr, self))),
		                         default=default, flag='self printed flag')

class tset(Container, set):
	'''
	Humpack set, replaces the standard set
	Has all the same functionality of a set, plus being Transactionable or Packable
	'''
	
	def __new__(cls, *args, **kwargs):
		
		self = super().__new__(cls)
		
		self._data = OrderedDict()
		self._shadow = None
		
		return self
	
	def __init__(self, iterable=[]):
		super().__init__()
		for x in iterable:
			self.add(x)
		self._shadow = None
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			return
			self.commit()  # partial transactions are committed
		
		self._shadow = self._data
		self._data = self._data.copy()
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.begin()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		self._shadow = None
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.commit()
	
	def abort(self):
		if not self.in_transaction():
			return
		
		self._data = self._shadow
		self._shadow = None
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.abort()
	
	def toset(self):
		return {x for x in self}
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __pack__(self):
		state = {}
		state['_elements'] = [pack_member(elm) for elm in iter(self)]
		if self.in_transaction():
			state['_shadow'] = [pack_member(elm) for elm in self._shadow]
		return state
	
	def __unpack__(self, data):
		
		# TODO: write warning about overwriting state - which can't be aborted
		# if self.in_transaction():
		# 	pass
		
		self.update(unpack_member(elm) for elm in data['_elements'])
		
		if '_shadow' in data:  # TODO: maybe write warning about loading into a partially completed transaction
			self._shadow = OrderedDict()
			for elm in data['_shadow']:
				self._shadow[unpack_member(elm)] = None
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)
	
	def __and__(self, other):
		copy = self.copy()
		for x in self:
			if x in other:
				copy.add(x)
			else:
				copy.remove(x)
		return copy
	
	def __or__(self, other):
		copy = self.copy()
		copy.update(other)
		return copy
	
	def __xor__(self, other):
		copy = self.copy()
		for x in list(other):
			if x in other:
				copy.add(x)
			else:
				copy.remove(x)
		return copy
	
	def __sub__(self, other):
		copy = self.copy()
		for x in other:
			copy.discard(x)
		return copy
	
	def __rand__(self, other):
		return self & other
	
	def __ror__(self, other):
		return self | other
	
	def __rxor__(self, other):
		return self ^ other
	
	def __rsub__(self, other):
		copy = other.copy()
		for x in self:
			copy.discard(x)
		return copy
	
	def difference_update(self, other):
		self -= other
	
	def intersection_update(self, other):
		self &= other
	
	def union_update(self, other):
		self |= other
	
	def symmetric_difference_update(self, other):
		self ^= other
	
	def symmetric_difference(self, other):
		return self ^ other
	
	def union(self, other):
		return self | other
	
	def intersection(self, other):
		return self & other
	
	def difference(self, other):
		return self - other
	
	def issubset(self, other):
		for x in self:
			if x not in other:
				return False
		return True
	
	def issuperset(self, other):
		for x in other:
			if x not in self:
				return False
		return True
	
	def isdisjoint(self, other):
		return not self.issubset(other) and not self.issuperset(other)
	
	def __iand__(self, other):
		for x in list(self):
			if x not in other:
				self.remove(x)
	
	def __ior__(self, other):
		self.update(other)
	
	def __ixor__(self, other):
		for x in other:
			if x in self:
				self.remove(x)
			else:
				self.add(x)
	
	def __isub__(self, other):
		for x in other:
			if x in self:
				self.remove(x)
	
	def pop(self):
		return self._data.popitem()[0]
	
	def remove(self, item):
		del self._data[item]
	
	def discard(self, item):
		if item in self._data:
			self.remove(item)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	
	def __len__(self):
		return len(self._data)
	
	def __iter__(self):
		return iter(self._data)
	
	def clear(self):
		return self._data.clear()
	
	def update(self, other):
		for x in other:
			self.add(x)
	
	def add(self, item):
		self._data[item] = None
	
	def __str__(self, default='{...}'):
		return safe_self_execute(self, lambda: 't{}{}{}'.format('{', ', '.join(map(str, self)), '}'),
		                         default=default, flag='self printed flag')
	
	def __repr__(self, default='{...}'):
		return safe_self_execute(self, lambda: 't{}{}{}'.format('{', ', '.join(map(repr, self)), '}'),
		                         default=default, flag='self printed flag')


class tdeque(Container, deque):
	'''
	Humpack queue, replaces the standard deque
	Has all the same functionality of a set, plus being Transactionable or Packable
	'''
	
	def __new__(cls, *args, **kwargs):
		
		self = super().__new__(cls)
		
		self._data = deque()
		self._shadow = None
		
		return self
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		self._data = deque(*args, **kwargs)
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			return
			self.commit()  # partial transactions are committed
		
		self._shadow = self._data
		self._data = self._data.copy()
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.begin()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		self._shadow = None
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.commit()
	
	def abort(self):
		if not self.in_transaction():
			return
		
		self._data = self._shadow
		self._shadow = None
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.abort()
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __pack__(self):
		state = {}
		state['_entries'] = [pack_member(elm) for elm in iter(self)]
		if self.in_transaction():  # TODO: maybe write warning about saving in the middle of a transaction
			state['_shadow'] = [pack_member(elm) for elm in self._shadow]
		return state
	
	def __unpack__(self, state):
		
		# TODO: write warning about overwriting state - which can't be aborted
		# if self.in_transaction():
		# 	pass
		
		self._data.extend(unpack_member(elm) for elm in state['_entries'])
		if '_shadow' in state:  # TODO: maybe write warning about loading into a partially completed transaction
			self._shadow = [unpack_member(elm) for elm in state['_shadow']]
	
	def __getitem__(self, item):
		if isinstance(item, slice):
			return tdeque(self._data[item])
		return self._data[item]
	
	def __setitem__(self, key, value):
		self._data[key] = value
	
	def __delitem__(self, idx):
		del self._data[idx]
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)
	
	def count(self, object):
		return self._data.count(object)
	
	def append(self, item):
		return self._data.append(item)
	
	def appendleft(self, item):
		return self._data.appendleft(item)
	
	def __contains__(self, item):
		return self._data.__contains__(item)
	
	def extend(self, iterable):
		return self._data.extend(iterable)
	
	def extendleft(self, iterable):
		return self._data.extendleft(iterable)
	
	def insert(self, index, object):
		self._data.insert(index, object)
	
	def remove(self, value):
		self._data.remove(value)
	
	def __iter__(self):
		return iter(self._data)
	
	def __reversed__(self):
		return self._data.__reversed__()
	
	def reverse(self):
		self._data.reverse()
	
	def pop(self):
		return self._data.pop()
		
	def popleft(self):
		return self._data.popleft()
		
	def __len__(self):
		return len(self._data)
	
	def clear(self):
		self._data.clear()
	
	def sort(self, key=None, reverse=False):
		self._data.sort(key, reverse)
	
	def index(self, object, start=None, stop=None):
		self._data.index(object, start, stop)
	
	def rotate(self, n=1):
		return self._data.rotate(n=n)
	
	def __mul__(self, other):
		return tdeque(self._data.__mul__(other))
	
	def __rmul__(self, other):
		return tdeque(self._data.__rmul__(other))
	
	def __add__(self, other):
		out = self.copy()
		out.extend(other)
		return out
	
	def __iadd__(self, other):
		self._data.__iadd__(other)
	
	def __imul__(self, other):
		self._data.__imul__(other)
	
	def __str__(self, default='[...]'):
		return safe_self_execute(self, lambda: 't[{}]'.format(', '.join(map(str, self))),
		                         default=default, flag='self printed flag')
	
	def __repr__(self, default='[...]'):
		return safe_self_execute(self, lambda: 't[{}]'.format(', '.join(map(repr, self))),
		                         default=default, flag='self printed flag')

class tstack(tdeque):
	'''
	Humpack stack
	Has all the same functionality of a deque, except it's a stack (FIFO)
	Also implements Transactionable and Packable
	'''
	
	def pop(self):
		return super().popleft()
	
	def popend(self):
		return super().pop()
	
	def push(self, item):
		return super().appendleft(item)
	
	def push_all(self, items):
		return super().extendleft(reversed(items))
	
	def peek(self, n=0):
		return self[n]


class _theap_iter(object):
	def __init__(self, heap):
		self._heap = heap
	
	def __next__(self):
		if len(self._heap):
			return self._heap.pop()
		raise StopIteration

class theap(Container, object):
	'''
	Humpack heap
	Unordered for adding/removing, ordered when iterating.
	Note that iterating through the heap empties it.
	'''
	
	def __new__(cls, *args, **kwargs):
		
		self = super().__new__(cls)
		
		self._data = []
		self._shadow = None
		
		return self
	
	def __init__(self, *args, **kwargs):
		super().__init__()
		self._data = list(*args, **kwargs)
		heapq.heapify(self._data)
	
	def in_transaction(self):
		return self._shadow is not None
	
	def begin(self):
		if self.in_transaction():
			return
			self.commit()  # partial transactions are committed
		
		self._shadow = self._data
		self._data = self._data.copy()
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.begin()
	
	def commit(self):
		if not self.in_transaction():
			return
		
		self._shadow = None
		
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.commit()
	
	def abort(self):
		if not self.in_transaction():
			return
		
		self._data = self._shadow
		self._shadow = None
		for child in iter(self):
			if isinstance(child, Transactionable):
				child.abort()
	
	def copy(self):
		copy = type(self)()
		copy._data = self._data.copy()
		if self._shadow is not None:
			copy._shadow = self._shadow.copy()
		return copy
	
	def __pack__(self):
		state = {}
		state['_entries'] = [pack_member(elm) for elm in iter(self)]
		if self.in_transaction():  # TODO: maybe write warning about saving in the middle of a transaction
			state['_shadow'] = [pack_member(elm) for elm in self._shadow]
		return state
	
	def __unpack__(self, state):
		
		# TODO: write warning about overwriting state - which can't be aborted
		# if self.in_transaction():
		# 	pass
		
		self._data.extend(unpack_member(elm) for elm in state['_entries'])
		if '_shadow' in state:  # TODO: maybe write warning about loading into a partially completed transaction
			self._shadow = [unpack_member(elm) for elm in state['_shadow']]
			
	def __iter__(self): # Note: this actually pops entries - iterating through heap will empty it
		return _theap_iter(self.copy())
	
	def __len__(self):
		return len(self._data)
		
	def push(self, *items):
		for item in items:
			heapq.heappush(self._data, item)

	def pop(self, n=None):
		if n is None:
			return heapq.heappop(self._data)
		return tlist(heapq.heappop(self._data) for _ in range(n))
	
	def replace(self, item):
		return heapq.heapreplace(self._data, item)
	
	def pushpop(self, item):
		return heapq.heappushpop(self._data, item)
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)
	
	def __str__(self, default='[...]'):
		return safe_self_execute(self, lambda: 't[{}]'.format(', '.join(map(str, self._data))),
		                         default=default, flag='self printed flag')
	
	def __repr__(self, default='[...]'):
		return safe_self_execute(self, lambda: 't[{}]'.format(', '.join(map(repr, self._data))),
		                         default=default, flag='self printed flag')


def containerify(obj, dtype=tdict):
	'''
	Recursively, convert `obj` from using standard python containers to HumPack containers.

	:param obj: object using python containers (dict, list, set, tuple, etc.)
	:return: deep copy of the object using HumPack containers
	'''
	if isinstance(obj, deque):
		return tdeque(containerify(o, dtype=dtype) for o in obj)
	if isinstance(obj, list):
		return tlist(containerify(o, dtype=dtype) for o in obj)
	if isinstance(obj, set):
		return tset(containerify(o, dtype=dtype) for o in obj)
	if isinstance(obj, tuple):
		return tuple(containerify(o, dtype=dtype) for o in obj)
	if isinstance(obj, dict):
		return dtype({containerify(k, dtype=dtype): containerify(v, dtype=dtype) for k, v in obj.items()})
	
	return obj

