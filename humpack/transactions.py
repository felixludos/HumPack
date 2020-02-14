
from typing import NoReturn, Union, Any, Type



class Transactionable(object):
	'''
	Mixin to enable beginning, committing, and aborting transactions (multiple statements).
	To use Transactionable functionality, subclasses must implement begin(), in_transaction(), commit(), and abort().
	'''
	
	def begin(self) -> NoReturn:
		'''
		Must be overridden by subclasses.
		This prepares `self` to track all changes to `self` until commit() or abort() is called.
		If any attributes or data kept by `self`, this method should probably also call begin() in them.
		
		Has no effect if `self` is already in a transaction.
		
		:return: None
		'''
		raise NotImplementedError
	
	def in_transaction(self) -> bool:
		'''
		Query whether `self` is in a transaction.
		
		:return: True if and only if `self` is currently in a transaction.
		'''
		raise NotImplementedError
	
	def commit(self) -> NoReturn:
		'''
		Make all the changes to `self` since transaction began, and stop tracking changes from now on.
		
		Has no effect if `self` is not in a transaction.
		
		:return: None
		'''
		raise NotImplementedError
	
	def abort(self) -> NoReturn:
		'''
		Revert all changes to `self` since the transaction began, and stop tracking changes from now on.
		
		Has no effect if `self` is not in a transaction.
		
		:return: None
		'''
		raise NotImplementedError

	def __enter__(self) -> NoReturn:
		self.begin()
	
	def __exit__(self, type: Union[type(None), Type], *args: Any) -> Union[type(None), Type]:
		'''
		Once the context is ended, if no exception was raised the transaction is committed, otherwise,
		
		:param type: Either None or an Exception type, if an Exception was raised in the context.
		:param args: Other possible args provided by the raised Exception
		:return: If there was no exception, or the
		'''
		if type is None:
			self.commit()
		else:
			self.abort()
		return None if type is None else type.__name__ == 'AbortTransaction'
	

class AbortTransaction(Exception):
	pass