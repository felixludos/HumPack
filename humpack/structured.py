
import traceback

from .basic_containers import adict, tlist



class TreeSpace(adict):
	'''
	Namespace - like a dictionary but where keys can be accessed as attributes, and if not found will create new NS
	allowing:

	a = TreeSpace()
	a.b.c.d = 'hello'
	print(repr(a)) # --> {{'b':{{'c':{{'d':'hello'}}}}}}

	NOTE: avoid ``hasattr``! - always returns true (creating new attrs), use ``__contains__`` instead

	'''
	
	def __getitem__(self, key):
		try:
			v = super().__getitem__(key)
			# print(key,v)
			return v
		except KeyError:
			try:
				return super().__getattribute__(key)
			except AttributeError:
				# print('**WARNING: defaulting {}'.format(key))
				return self._missing_key(key)
	
	def _missing_key(self, key):
		obj = self.__class__()
		self.__setitem__(key, obj)
		return obj
	
	def todict(self):
		d = {}
		for k ,v in self.items():
			if isinstance(v, TreeSpace):
				v = v.todict()
			d[k] = v
		return d
	
	def __repr__(self):
		return '{}{}{}'.format('{{', ', '.join(['{}:{}'.format(repr(k), repr(v)) for k ,v in self.items()]), '}}')

class Table(tlist):
	'''
	Essentially a database (elements are rows, keys are cols)
	Allowing nonrectangular entries
	All elements should be dicts (or ideally tdicts)
	'''
	
	def __init__(self, *args, _type=adict, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__['_el_type'] = _type
	
	def sort_by(self, *keys):
		self.__dict__['_data'] = sorted(self, key=lambda x: tuple(x[k] for k in keys))
	
	def select(self, key, skip=True):
		for x in self.selects(key, skip=skip):
			yield x[0]
	
	def selects(self, *keys, skip=True):
		for x in self:
			l = []
			for k in keys:
				if k in x:
					l.append(x[k])
				elif skip:
					l = None
					break
				else:
					raise KeyError(k)
			if l is not None:
				yield l
	
	def select_items(self, key, skip=True, skip_flag=None):
		for x in self:
			if key in x:
				yield x[key], x
			elif not skip:
				yield skip_flag, x
	
	def _join(self, other, cmp, merge_fn=None):
		
		if isinstance(cmp, str):
			cmp = lambda a ,b: a[cmp] == b[cmp]
		elif isinstance(cmp, tuple):
			ca, cb = cmp
			cmp = lambda a ,b: a[ca] == b[cb]
		if merge_fn is None:
			def merge_fn(a ,b):
				a = a.copy()
				a.update(b)
				return a
		
		for a in self:
			for b in other:
				if cmp(a ,b):
					yield merge_fn(a ,b)
	
	def join_(self, other, cmp, merge_fn=None):
		if merge_fn is None:
			merge_fn = lambda a ,b: a.update(b)
		for _ in self._join(other, cmp, merge_fn=merge_fn):
			pass
	
	def join(self, other, cmp, merge_fn=None):
		return self.__class__(self._join(other, cmp, merge_fn=merge_fn))
	
	def filter_(self, fn):
		self.__dict__['_data'] = [x for x in self if fn(x)]
	
	def filter(self, fn):
		return self.__class__(x for x in self if fn(x))
	
	def new(self, *args, **kwargs):
		obj = self._el_type(*args, **kwargs)
		self.append(obj)
		return obj
	
	def map(self, fn, indexed=False, safe=False, pbar=None, reduce=None):
		'''
		fn is a callable taking one run as input
		'''
		
		outs = []
		
		seq = self if pbar is None else pbar(self)
		
		for i, x in enumerate(seq):
			try:
				inp = (i ,x) if indexed else (x,)
				out = fn(*inp)
				outs.append(out)
			except Exception as e:
				if safe:
					print(f'elm {i} failed')
					traceback.print_exc()
				else:
					raise e
		
		if pbar is not None:
			seq.close()
		
		if reduce is not None:
			return reduce(outs)
		return outs
	
	# def through(self, **map_kwargs):
	#
	# 	def _execute(fn, args=[], kwargs={}):
	# 		return self.map(lambda run: fn(run, *args, **kwargs),
	# 		                **map_kwargs)
	#
	# 	return make_ghost(self._el_type, _execute)

class _nothing:
	pass

class Key_Table(Table):
	'''
	Very similar to Table, but with a specified key that can be used with the get() function
	(so the table acts a little more like a dict)
	'''
	
	def __init__(self, *args, _get_key=None, **kwargs):
		super().__init__(*args, **kwargs)
		self.__dict__['_keys'] = {}
		self.__dict__['_get_key'] = _get_key
	
	def new(self, *args, **kwargs):
		obj = super().new(*args, **kwargs)
		get_key = self.__dict__['_get_key']
		self.__dict__['_keys'][get_key(obj)] = obj
		return obj

	def get(self, key, default=_nothing):
		if default is _nothing:
			return self.__dict__['_keys'][key]
		return self.__dict__['_keys'].get(key, default)

