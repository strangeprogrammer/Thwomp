#!/usr/bin/env python3

# ToBeGreen is a python3 library used for (de)serialization between python data objects and blobs.
# Copyright (C) 2020 Stephen Fedele <32551324+strangeprogrammer@users.noreply.github.com>
# 
# This file is part of ToBeGreen.
# 
# ToBeGreen is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# ToBeGreen is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# and the GNU Lesser General Public License along with ToBeGreen.  If not, see
# <https://www.gnu.org/licenses/>.
# 
# Additional terms apply to this file.  Read the file 'LICENSE.txt' for
# more information.



"""Serialization and deserialization tools."""

# 'Sphinx' will complain a lot if 'MiniCLEB' isn't installed on the system
# (virtualenv's don't count, unfortunately), so we create a dummy library
# instead to assuage its wrath.
try:
	import MiniCLEB as LEB
except Exception as e:
	class DepNotFoundException(Exception):
		"Raised when the a dependency hasn't been found for import (it's probably not installed)."
		
		def __init__(self, dep, *args):
			super().__init__("Dependency '" + str(dep) + "' not found (is it in installed in your virtualenv)?")
	
	def DocOnly(depname):
		class wrapper:
			"""This class should only ever be used by 'Sphinx' internally."""
			
			def __getattribute__(self, name):
				raise DepNotFoundException(depname)
		
		return wrapper()
	
	LEB = DocOnly("MiniCLEB")

__all__ = [
	### Backend Interface
	
	"strToBytes",
	"bytesToStr",
	"ObeseMessageException",
	"pascalify",
	"depascalify",
	"peel",
	
	### Serializers
	
	"_bytes_ser",
	"_str_ser",
	"_bool_ser",
	"_int_ser",
	"_list_ser",
	"_tuple_ser",
	"_set_ser",
	"_frozenset_ser",
	"_dict_ser",
	
	### Deserializers
	
	"_bytes_des",
	"_str_des",
	"_bool_des",
	"_int_des",
	"_list_des",
	"_tuple_des",
	"_set_des",
	"_frozenset_des",
	"_dict_des",
	
	### Frontend Interface
	
	"serers",
	"desers",
	"Ser",
	"Des",
]

### Backend Interface

def strToBytes(s):
	"""Converts a string into its blob equivalent."""
	return bytes(str(s), "utf-8")

def bytesToStr(byteobj):
	"""Converts a blob into its string equivalent."""
	return str(bytes(byteobj), "utf-8")

# Wrappers for 'MiniCLEB'

class ObeseMessageException(Exception):
	"Raised by 'depascalify' when the message is too large to put into RAM (or is malformed as such)."
	
	def __init__(self, *args):
		super().__init__("The message was too large to put into RAM (or is malformed as such).")

def pascalify(blob):
	"""Concatenate the length of a blob with the object itself, and return the result."""
	return LEB.fromInt(len(blob)) + blob

def depascalify(blob):
	"""Return the length of a blob along with EVERYTHING following said length field."""
	[leb, blob] = LEB.extract(blob)
	if not LEB.valid(leb):
		raise ObeseMessageException()
	return [LEB.toInt(leb), blob]

def peel(blob):
	"""Deconcatenate and depascalify a blob, and return it along with EVERYTHING that's left over."""
	[blength, blob] = depascalify(blob)
	return [
		blob[ : blength], # What we expect to receive given 'blength'
		blob[blength : ], # What we didn't expect to receive
	]

### Serializers

def _bytes_ser(x):
	"""Serialize a blob."""
	return bytes(x)

def _str_ser(x):
	"""Serialize a string."""
	return strToBytes(x)

def _bool_ser(x):
	"""Serialize a boolean."""
	return b"\xFF" if x else b"\x00"

def _int_ser(x):
	"""Serialize an integer."""
	return _bool_ser(0 <= x) + LEB.fromInt(abs(x))

def _float_ser(x):
	"""Serialize a float."""
	return strToBytes(x.hex())

def _complex_ser(x):
	"Serialize a complex."
	return _float_ser(x.real) + b" " + _float_ser(x.imag)

def _list_ser(x):
	"""Serialize a list recursively."""
	blob = b""
	for y in x:
		blob += pascalify(Ser(y))
	return blob

def _tuple_ser(x):
	"""Serialize a tuple recursively."""
	return _list_ser(x)

def _set_ser(x):
	"""Serialize a set recursively."""
	return _list_ser(x)

def _frozenset_ser(x):
	"""Serialize a frozenset recursively."""
	return _list_ser(x)

def _dict_ser(x):
	"""Serialize a dict recursively."""
	return _list_ser(map(_list_ser, x.items()))

### Deserializers

def _bytes_des(blob):
	"""Deserialize into a blob."""
	return blob

def _str_des(blob):
	"""Deserialize into a string."""
	return bytesToStr(blob)

def _bool_des(blob):
	"""Deserialize into a boolean."""
	return False if blob == b"\x00" else True

def _int_des(blob):
	"""Deserialize into an integer."""
	pospart = blob[1:]
	if _bool_des(blob[0:1]):
		return LEB.toInt(pospart)
	else:
		return -LEB.toInt(pospart)

def _float_des(blob):
	"""Deserialize into a float."""
	return float.fromhex(bytesToStr(blob))

def _complex_des(bobj):
	"Deserialize into a complex."
	delim = bobj.index(b" ")
	return complex(
		_float_des(bobj[ : delim]),
		_float_des(bobj[delim + 1 : ])
	)

def _list_des(blob):
	"""Deserialize into a list (recursively)."""
	x = []
	while blob != b"":
		[y, blob] = peel(blob)
		x.append(Des(y))
	return x

def _tuple_des(blob):
	"""Deserialize into a tuple."""
	return tuple(_list_des(blob))

def _set_des(blob):
	"""Deserialize into a set."""
	return set(_list_des(blob))

def _frozenset_des(blob):
	"""Deserialize into a frozenset."""
	return frozenset(_list_des(blob))

def _dict_des(blob):
	"""Deserialize into a dict."""
	return dict(map(_list_des, _list_des(blob)))

### Frontend Interface

#: Full list of serializers available to 'Ser'.
serers = {
	bytes:		["bytes",	_bytes_ser],
	str:		["str",		_str_ser],
	bool:		["bool",	_bool_ser],
	int:		["int",		_int_ser],
	float:		["float",	_float_ser],
	complex:	["complex",	_complex_ser],
	list:		["list",	_list_ser],
	tuple:		["tuple",	_tuple_ser],
	set:		["set",		_set_ser],
	frozenset:	["frozenset",	_frozenset_ser],
	dict:		["dict",	_dict_ser],
}

#: Full list of deserializers available to 'Des'.
desers = {
	"bytes":	_bytes_des,
	"str":		_str_des,
	"bool":		_bool_des,
	"int":		_int_des,
	"float":	_float_des,
	"complex":	_complex_des,
	"list":		_list_des,
	"tuple":	_tuple_des,
	"set":		_set_des,
	"frozenset":	_frozenset_des,
	"dict":		_dict_des,
}

def Ser(x):
	"""Serializes a python object into a blob."""
	
	try:
		[name, serializer] = serers[type(x)]
	except Exception:
		raise Exception("Error: object '" + str(x) + "' couldn't be serialized...")
	
	return pascalify(strToBytes(name)) + pascalify(serializer(x))

def Des(blob):
	"""Deserializes a blob into a python object."""
	
	try:
		[name, blob] = peel(blob)
		deserializer = desers[bytesToStr(name)]
	except Exception:
		raise Exception("Error: object '" + str(blob) + "' couldn't be deserialized...")
	
	return deserializer(peel(blob)[0])

### Unit Tests

import unittest
from unittest.mock import call, patch
import itertools

class testLooperMixin(unittest.TestCase):
	def loopTests(self, args, expecteds, f, extraAsserts = None):
		if extraAsserts == None:
			extraAsserts = itertools.repeat(lambda: None)
		
		for [i, [arg, expected, extraAssert]] in enumerate(zip(args, expecteds, extraAsserts)):
			with self.subTest(i = i):
				result = f(arg)
				self.assertEqual(result, expected)
				extraAssert()

def __scopewrapper():
	# Local declarations to make life easier
	
	obj5 = b"\xFF" + LEB.fromInt(5)
	obj5 = LEB.fromInt(3) + b"int" + LEB.fromInt(len(obj5)) + obj5
	
	objbee = LEB.fromInt(3) + b"str" + LEB.fromInt(3) + b"bee"
	objbeeser = LEB.fromInt(len(objbee)) + objbee
	
	objlist = LEB.fromInt(4) + b"list" + LEB.fromInt(len(objbeeser)) + objbeeser
	
	objhi = LEB.fromInt(3) + b"str" + LEB.fromInt(2) + b"hi"
	objhiser = LEB.fromInt(len(objhi)) + objhi
	
	# Testing classes
	
	class testSerializers(testLooperMixin):
		def test_bytes(self):
			arg = b"lwiherkjtghjfd"
			expected = b"lwiherkjtghjfd"
			result = _bytes_ser(arg)
			self.assertEqual(result, expected)
		
		# def test_str(self): # Too simple to write a test for as of now (except maybe the part where it uses 'utf-8', which doesn't encode arbitrary strings)
		
		# def test_int(self): # Too simple to write a test for as of now
		
		# def test_bool(self): # Too simple to write a test for as of now
		
		# def test_float(self): # Too simple to write a test for as of now
		
		# def test_complex(self): # Too simple to write a test for as of now
		
		@patch(__name__ + ".Ser")
		def test_list(self, notSer):
			notSer.side_effect = [
				obj5,
				
				objbee,
				
				objlist,
				
				obj5,
				objhi,
				
				obj5,
				objlist,
				objhi,
			]
			
			args = [
				[],
				[5],
				["bee"],
				[["bee"]],
				[5, "hi"],
				[5, ["bee"], "hi"],
			]
			
			expecteds = [
				b"",
				
				LEB.fromInt(len(obj5)) + obj5,
				
				LEB.fromInt(len(objbee)) + objbee,
				
				LEB.fromInt(len(objlist)) + objlist,
				
				LEB.fromInt(len(obj5)) + obj5 + \
				LEB.fromInt(len(objhi)) + objhi,
				
				LEB.fromInt(len(obj5)) + obj5 + \
				LEB.fromInt(len(objlist)) + objlist + \
				LEB.fromInt(len(objhi)) + objhi,
			]
			
			extraAsserts = [
				lambda: notSer.assert_has_calls([call(5)]),
				lambda: notSer.assert_has_calls([call("bee")]),
				lambda: notSer.assert_has_calls([call(["bee"])]),
				lambda: notSer.assert_has_calls([call(5, "hi")]),
				lambda: notSer.assert_has_calls([call(5, ["bee"], "hi")]),
			]
			
			self.loopTests(args, expecteds, _list_ser)
		
		# def test_tuple(self): # Since '_tuple_ser' is just a call to '_list_ser', it is redundant
		
		# def test_set(self): # Since '_set_ser' is just a call to '_list_ser', it is redundant
		
		# def test_frozenset(self): # Since '_frozenset_ser' is just a call to '_list_ser', it is redundant
		
		# @patch(__name__ + "._list_ser")
		# def test_dict(self, notListSer): # I could test this, but it's too simple for me to bother
	
	class testDeserializers(testLooperMixin):
		def test_bytes(self):
			arg = b"lwiherkjtghjfd"
			expected = b"lwiherkjtghjfd"
			result = _bytes_des(arg)
			self.assertEqual(result, expected)
		
		# def test_str(self): # Too simple to write a test for as of now (except maybe the part where it uses 'utf-8', which doesn't encode arbitrary strings)
		
		# def test_int(self): # Too simple to write a test for as of now
		
		# def test_bool(self): # Too simple to write a test for as of now
		
		# def test_float(self): # Too simple to write a test for as of now
		
		# def test_complex(self): # Too simple to write a test for as of now
		
		@patch(__name__ + ".Des")
		def test_list(self, notDes):
			notDes.side_effect = [
				5,
				"bee",
				["bee"],
				5, "hi",
				5, ["bee"], "hi",
			]
			
			args = [
				b"",
				
				LEB.fromInt(len(obj5)) + obj5,
				
				LEB.fromInt(len(objbee)) + objbee,
				
				LEB.fromInt(len(objlist)) + objlist,
				
				LEB.fromInt(len(obj5)) + obj5 + \
				LEB.fromInt(len(objhi)) + objhi,
				
				LEB.fromInt(len(obj5)) + obj5 + \
				LEB.fromInt(len(objlist)) + objlist + \
				LEB.fromInt(len(objhi)) + objhi,
			]
			
			expecteds = [
				[],
				[5],
				["bee"],
				[["bee"]],
				[5, "hi"],
				[5, ["bee"], "hi"],
			]
			
			extraAsserts = [
				lambda: notDes.assert_has_calls([
					call(obj5)
				]),
				lambda: notDes.assert_has_calls([
					call(objbee)
				]),
				lambda: notDes.assert_has_calls([
					call(objlist),
				]),
				lambda: notDes.assert_has_calls([
					call(obj5),
					call(objhi),
				]),
				lambda: notDes.assert_has_calls([
					call(obj5),
					call(objlist),
					call(objhi),
				]),
			]
			
			self.loopTests(args, expecteds, _list_des)
		
		# def test_tuple(self): # Since '_tuple_des' is just a call to '_list_des', it is redundant
		
		# def test_set(self): # Since '_set_des' is just a call to '_list_des', it is redundant
		
		# def test_frozenset(self): # Since '_frozenset_des' is just a call to '_list_des', it is redundant
		
		# @patch(__name__ + "._list_des")
		# def test_dict(self, notListDes): # I could test this, but it's too simple for me to bother
	
	return [testSerializers, testDeserializers]

if __name__ == "__main__":
	[testSerializers, testDeserializers] = __scopewrapper()
	unittest.main()
