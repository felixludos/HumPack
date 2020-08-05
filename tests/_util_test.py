from humpack import adict, tdict, tlist, tset

def get_adict():
	x = adict()
	x.a = 1
	x.x = x
	x.l = [tlist(), tset()]
	x[100] = '100'
	x[None] = 1.2
	x.m = None
	x[True] = tlist
	x[list] = complex
	x['<>)dksfl_ ds: gkal'] = '<>1234543224'
	x['d = ds=a _+ sd;'] = bytes(range(256))
	x[12.2344+.023j] = range(123,456,7)
	# np.random.seed(1)
	# x.b = np.random.randn(3).tobytes()
	x[b'\xaa'] = 'running'
	return x

