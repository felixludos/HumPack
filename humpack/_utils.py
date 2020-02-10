

def safe_self_execute(obj, fn, default='<<short circuit>>',
                 flag='safe execute flag'):
	
	if flag in obj.__dict__:
		return default  # short circuit
	obj.__dict__[flag] = True
	
	try:
		out = fn()
	except Exception as e:
		raise e
	else:
		return out
	finally:
		del obj.__dict__['self printed flag']

