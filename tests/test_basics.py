
from _util_test import get_adict
from humpack import adict, tdict, tlist, tset


def test_init():
	'''
	Test creating some standard humpack objects
	'''
	x = adict()
	assert len(x) == 0
	
	x = tlist()
	assert len(x) == 0
	
	x = tset()
	assert len(x) == 0


def test_adict():
	'''
	Test basic operations with tdict
	'''
	
	x = adict()
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


def test_elements():
	data = get_adict()
	
	data[dict] = data
	assert len(data) == len(data[dict])
	
	data[1234] = 'element'
	assert 1234 in data
	assert 'element' == data[1234]
	
	data.abc = 123
	assert 'abc' in data
	assert data.abc == 123
	assert data['abc'] == 123


