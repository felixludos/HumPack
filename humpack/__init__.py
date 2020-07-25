

from .packing import Packable, primitive, PRIMITIVE, SERIALIZABLE, JSONABLE, pack, unpack, pack_member, unpack_member
from .packing import save_pack, load_pack, json_pack, json_unpack
from .transactions import Transactionable, AbortTransaction
from .hashing import Hashable

# from .wrappers import ObjectWrapper, Array # causes an error if required libs aren't already installed
try:
	import numpy as _numpy
except ImportError:
	pass
else: # Register additional common packable types
	from . import common

from .basic_containers import tdict, tlist, tset, tstack, tdeque, theap
from .basic_containers import containerify

from .structured import TreeSpace, Table, Key_Table

import os

from yaml import safe_load
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.fig.yaml'), 'r') as f:
	info = safe_load(f)

__author__ = info['author']
__version__ = info['version']
__info__ = info

