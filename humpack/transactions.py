




class Transactionable(object):
	
	def begin(self):
		raise NotImplementedError
	
	def in_transaction(self):
		raise NotImplementedError
	
	def commit(self):
		raise NotImplementedError
	
	def abort(self):
		raise NotImplementedError

# def __enter__(self):
# 	# self._context = True
# 	self.begin()
#
# def __exit__(self, type, *args):
# 	# self._context = False
# 	if type is None:
# 		self.commit()
# 	else:
# 		self.abort()
# 	return None if type is None else type.__name__ == 'AbortTransaction'