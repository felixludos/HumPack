



class Hashable(object):
	'''Mixin to allow hashing'''
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)