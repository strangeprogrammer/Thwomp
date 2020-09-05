#!/bin/python3

# ToBeGreen is a python3 library used for (de)serialization between python data objects and bytes strings.
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



### Notes:

# VLQ is an acronym that basically means 'variable-length int'
# More information on VLQ can be found at:
# https://en.wikipedia.org/wiki/Variable-length_quantity

### Backend Interface

def strToBytes(s):		return bytes(str(s), "utf-8")
def bytesToStr(byteobj):	return str(bytes(byteobj), "utf-8")

def intToVLQ(n):
	"""Takes an integer and returns a bytes object representing its VLQ equivalent."""
	n = abs(int(n))
	result = []
	
	while True:
		result = [n & 0b01111111 | 0b10000000] + result
		n >>= 7
		
		if not 0 < n:
			break
	
	result[-1] &= 0b01111111
	return bytes(result)

def VLQToInt(bobj):
	"""Takes a bytes object representing a VLQ and returns its integer equivalent."""
	n = 0
	while True:
		n <<= 7
		[x, bobj] = [bobj[0], bobj[1:]]
		n += x & 0b01111111
		
		if not x & 0b10000000:
			return n

def skipVLQ(bobj):
	"""Takes a bytes object and skips over its VLQ header."""
	while True:
		x = bobj[0]
		if x & 0b10000000:
			bobj = bobj[1:]
		else:
			return bobj[1:]

def pascalify(bobj):		return intToVLQ(len(bobj)) + bobj
def depascalify(bobj):		return [VLQToInt(bobj), skipVLQ(bobj)]

def peel(bobj):
	[blength, bobj] = depascalify(bobj)
	return [
		bobj[ : blength], # What we expect to receive given 'blength'
		bobj[blength : ], # What we didn't expect to receive
	]

### Serializers

def _bytes_ser(x):		return bytes(x)
def _str_ser(x):		return strToBytes(x)
def _int_ser(x):		return intToVLQ(x)
def _bool_ser(x):		return b"\xFF" if x else b"\x00"

def _list_ser(x):
	bobj = b""
	for y in x:
		bobj += pascalify(Ser(y))
	return bobj

def _tuple_ser(x):		return _list_ser(x)
def _set_ser(x):		return _list_ser(x)
def _frozenset_ser(x):		return _list_ser(x)
def _dict_ser(x):		return _list_ser(map(_list_ser, x.items()))

### Deserializers

def _bytes_des(bobj):		return bobj
def _str_des(bobj):		return bytesToStr(bobj)
def _int_des(bobj):		return VLQToInt(bobj)
def _bool_des(bobj):		return False if bobj[0] == "\x00" else True

def _list_des(bobj):
	x = []
	while bobj != b"":
		[y, bobj] = peel(bobj)
		x.append(Des(y))
	return x

def _tuple_des(bobj):		return tuple(_list_des(bobj))
def _set_des(bobj):		return set(_list_des(bobj))
def _frozenset_des(bobj):	return frozenset(_list_des(bobj))
def _dict_des(bobj):		return dict(map(_list_des, _list_des(bobj)))

### Frontend Interface

codecs = {
	"bytes":	[_bytes_ser,		_bytes_des],
	"str":		[_str_ser,		_str_des],
	"int":		[_int_ser,		_int_des],
	"bool":		[_bool_ser,		_bool_des],
	"list":		[_list_ser,		_list_des],
	"tuple":	[_tuple_ser,		_tuple_des],
	"set":		[_set_ser,		_set_des],
	"frozenset":	[_frozenset_ser,	_frozenset_des],
	"dict":		[_dict_ser,		_dict_des],
}

def Ser(x):
	"""Serializes a python object into a bytes string."""
	
	try:
		t = type(x).__name__
		serializer = codecs[t][0]
	except Exception:
		raise Exception("Error: object of type '" + type(x).__name__ + "' couldn't be serialized...")
	
	return pascalify(strToBytes(t)) + pascalify(serializer(x))

def Des(bobj):
	"""Deserializes a bytes string into a python object."""
	
	try:
		[t, bobj] = peel(bobj)
		deserializer = codecs[bytesToStr(t)][1]
	except Exception:
		raise Exception("Error: object of type '" + t + "' couldn't be deserialized...")
	return deserializer(peel(bobj)[0]) # We don't use 'skipVLQ' since this function uses the length given, while skipVLQ does not

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

class testVLQ(testLooperMixin):
	def test_intToVLQ(self):
		args = [
			0,
			55,
			127,
			128,
			129,
			246537,
		]
		
		expecteds = [
			b"\x00",
			b"\x37",
			b"\x7F",
			b"\x81\x00",
			b"\x81\x01",
			b"\x8F\x86\x09",
		]
		
		self.loopTests(args, expecteds, intToVLQ)
	
	def test_VLQToInt(self):
		args = [
			b"\x00garbage0",
			b"\x37garbage1",
			b"\x7Fgarbage2",
			b"\x81\x00garbage3",
			b"\x81\x01garbage4",
			b"\x8F\x86\x09garbage5",
		]
		
		expecteds = [
			0,
			55,
			127,
			128,
			129,
			246537,
		]
		
		self.loopTests(args, expecteds, VLQToInt)
	
	def test_skipVLQ(self):
		args = [
			b"\x00garbage0",
			b"\x37garbage1",
			b"\x7Fgarbage2",
			b"\x81\x00garbage3",
			b"\x81\x01garbage4",
			b"\x8F\x86\x09garbage5",
		]
		
		expecteds = [
			b"garbage0",
			b"garbage1",
			b"garbage2",
			b"garbage3",
			b"garbage4",
			b"garbage5",
		]
		
		self.loopTests(args, expecteds, skipVLQ)

class testSerializers(testLooperMixin):
	def test_bytes(self):
		arg = b"lwiherkjtghjfd"
		expected = b"lwiherkjtghjfd"
		result = _bytes_ser(arg)
		self.assertEqual(result, expected)
	
	# def test_str(self): # Too simple to write a test for as of now (except maybe the part where it uses 'utf-8', which doesn't encode arbitrary strings)
	
	# def test_int(self): # Unessecary since we've already tested 'intToVLQ' and 'VLQToInt' earlier
	
	# def test_bool(self): # Too simple to write a test for as of now
	
	@patch(__name__ + ".Ser")
	def test_list(self, notSer):
		notSer.side_effect = [
			b"\x03int\x01\x05",
			
			b"\x03str\x03bee",
			
			b"\x04list\x09" + \
				b"\x08\x03str\x03bee",
				
			b"\x03int\x01\x05",
			b"\x03str\x02hi",
			
			b"\x03int\x01\x05",
			b"\x04list\x09" + \
				b"\x08\x03str\x03bee",
			b"\x03str\x02hi",
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
			
			b"\x06\x03int\x01\x05",
			
			b"\x08\x03str\x03bee",
			
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee",
			
			b"\x06\x03int\x01\x05" + \
			b"\x07\x03str\x02hi",
			
			b"\x06\x03int\x01\x05" + \
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee" + \
			b"\x07\x03str\x02hi",
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
	
	# def test_int(self): # Unessecary since we've already tested 'intToVLQ' and 'VLQToInt' earlier
	
	# def test_bool(self): # Too simple to write a test for as of now
	
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
			
			b"\x06\x03int\x01\x05",
			
			b"\x08\x03str\x03bee",
			
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee",
			
			b"\x06\x03int\x01\x05" + \
			b"\x07\x03str\x02hi",
			
			b"\x06\x03int\x01\x05" + \
			b"\x0F\x04list\x09" + \
				b"\x08\x03str\x03bee" + \
			b"\x07\x03str\x02hi",
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
				call(b"\x03int\x01\x05")
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x03str\x03bee")
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x04list\x09" + \
					b"\x08\x03str\x03bee"),
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x03int\x01\x05"),
				call(b"\x03str\x02hi"),
			]),
			lambda: notDes.assert_has_calls([
				call(b"\x03int\x01\x05"),
				call(b"\x04list\x09" + \
					b"\x08\x03str\x03bee"),
				call(b"\x03str\x02hi"),
			]),
		]
		
		self.loopTests(args, expecteds, _list_des)
	
	# def test_tuple(self): # Since '_tuple_des' is just a call to '_list_des', it is redundant
	
	# def test_set(self): # Since '_set_des' is just a call to '_list_des', it is redundant
	
	# def test_frozenset(self): # Since '_frozenset_des' is just a call to '_list_des', it is redundant
	
	# @patch(__name__ + "._list_des")
	# def test_dict(self, notListDes): # I could test this, but it's too simple for me to bother

if __name__ == "__main__":
	unittest.main()
