



class Hashable(object):
	
	def __hash__(self):
		return id(self)
	
	def __eq__(self, other):
		return id(self) == id(other)