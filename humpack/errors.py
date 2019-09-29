

# saving

class LoadInitFailureError(Exception):
	def __init__(self, obj_type):
		super().__init__('An instance of {obj_type} was unable to load (make sure {obj_type}.__init__ doesnt have any required arguments)'.format(obj_type=obj_type))

class ObjectIDReadOnlyError(Exception):
	def __init__(self):
		super().__init__('The attribute "_obj_id" is reserved for saving/loading and should not be set')

class SavableClassCollisionError(Exception):
	def __init__(self, addr, cls):
		super().__init__('A class with the address {} is already in the class register of Savable'.format(addr))
		self.cls = cls

class UnregisteredClassError(Exception):
	def __init__(self, name):
		super().__init__('"{}" is not registered (does it subclass Savable?)'.format(name))


