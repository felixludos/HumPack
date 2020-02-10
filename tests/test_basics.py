

from humpack import tdict, tlist, tset


def test_init():
	'''
	Test creating some standard humpack objects
	'''
	x = tdict()
	assert len(x) == 0
	
	x = tlist()
	assert len(x) == 0
	
	x = tset()
	assert len(x) == 0


def test_tdict():
	'''
	Test basic operations with tdict
	'''
	
	x = tdict()
	assert str(x) == 't{}'
	
	x.a = 'a'
	assert str(x) == 't{a}'
	
	x.b = 10
	assert str(x) == 't{a, b}'
	assert len(x) == 2
	
	l = list(iter(x))
	assert str(l) == "['a', 'b']"
	
	assert x.a == 'a'
	assert x['a'] == 'a'
	
	
