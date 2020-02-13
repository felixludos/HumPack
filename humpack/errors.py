

# packing

class WrongKeyError(Exception):
	'''Error thrown when the provided key for decryption is incorrect'''
	def __init__(self):
		super().__init__('Unable to decrypt the data because provided hash is invalid')

class LoadInitFailureError(Exception):
	'''Error thrown when an object cannot be recreated'''
	def __init__(self, obj_type):
		super().__init__('An instance of {obj_type} was unable to load (make sure {obj_type}.__init__ doesnt '
		                 'have any required arguments)'.format(obj_type=obj_type))

class ObjectIDReadOnlyError(Exception):
	'''Error thrown when trying to overwrite the obj_id'''
	def __init__(self):
		super().__init__('The attribute "_obj_id" is reserved for saving/loading and should not be set')

class SavableClassCollisionError(Exception):
	'''Error thrown when trying to re-register a class already registered'''
	def __init__(self, addr, cls):
		super().__init__('A class with the address {} is already in the class register of Packable'.format(addr))
		self.cls = cls

class UnregisteredClassError(Exception):
	'''Error thrown when trying to pack an instance of an unregistered class'''
	def __init__(self, name):
		super().__init__('"{}" is not registered (does it subclass Packable?)'.format(name))


