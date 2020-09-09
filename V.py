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



import abc
import itertools

### Notes

# 1.
# Checking whether or not even a simple, arbitrarily constructed list's elements
# meet an arbitrary type specification would be the same as constructing a
# Turing Machine that verifies whether or not an arbitrary string is an element
# of an arbitrary language. So, the problem of finding out whether or not some
# data meets a type specification is not a generally solvable problem in python.

# 2.
# Because of '1.', this library may feel incomplete/not have enough
# functionality to solve arbitrary type specifications concisely: it is
# basically impossible to do so. This is why there are some base classes that
# allow the user to extend the functionality of 'Ver': the user should at least
# somehow be able to get what they need out of this library.

# 3.
# The function 'map' is used in certain places instead of list comprehensions
# since it preserves short-circuit operation of the 'any' and 'all' builtin
# functions. This is because 'map' is effectively a generator function, while
# list comprehensions must perform full initialization of the list first.

### Backend Interface

class VERIFYABLE(abc.ABC):
	@abc.abstractmethod
	def verify(self, obj):
		return True

### Specifications

class CUSTOM(VERIFYABLE, abc.ABC):
	def __init__(self, tipo, *args, **kwargs):
		[
			self.tipo,
			self.args,
			self.kwargs,
		] = [
			tipo,
			args,
			kwargs,
		]
	
	@abc.abstractmethod
	def verify(self, obj):
		if type(obj) != self.tipo:
			return False
		
		return super().verify(obj)

class SUM(VERIFYABLE):
	def __init__(self, *args):
		self.args = args
	
	def verify(self, obj):
		return any(map(
			lambda tipo: Ver(obj, tipo),
			self.args
		))

class PRODUCT(VERIFYABLE):
	def __init__(self, *args):
		self.args = args
		self.length = len(args)
	
	def verify(self, objs):
		if len(objs) != self.length:
			return False
		
		return all(map(
			lambda obj, arg: Ver(obj, arg),
			objs, self.args
		))

class ITERABLE(CUSTOM):
	def __init__(self, tipo, subtipo, *args, **kwargs):
		self.subtipo = subtipo
		super().__init__(tipo, *args, **kwargs)
	
	def verify(self, objs):
		return super().verify(objs) and all(map(
			lambda obj: Ver(obj, self.subtipo),
			objs
		))

class LIST(ITERABLE):
	def __init__(self, *args, **kwargs):
		super().__init__(list, *args, **kwargs)

class TUPLE(ITERABLE):
	def __init__(self, *args, **kwargs):
		super().__init__(tuple, *args, **kwargs)

class SET(ITERABLE):
	def __init__(self, *args, **kwargs):
		super().__init__(set, *args, **kwargs)

class FROZENSET(ITERABLE):
	def __init__(self, *args, **kwargs):
		super().__init__(frozenset, *args, **kwargs)

class DICT(CUSTOM):
	def __init__(self, KVtipo, *args, **kwargs):
		self.KVtipo = KVtipo
		super().__init__(dict, *args, **kwargs)
	
	def verify(self, objs):
		return super().verify(objs) and all(itertools.starmap(
			lambda k, v: self.KVtipo.verify([k, v]),
			objs.items()
		))

### Frontend Interface

def Ver(obj, spec):
	if isinstance(spec, VERIFYABLE):
		return spec.verify(obj)
	else:
		return isinstance(obj, spec)

### Unit Tests

import unittest
from unittest.mock import call, patch, Mock
import itertools

class setwiseChecker():
	"""Checks that all of the specified function calls have been made in any order.""" + \
	"""NOTE: this currently only works with 1 function call at most per the given arguments."""
	def __init__(self, *args): self.reset(*args)
	
	def __call__(self, *args, **kwargs):
		try:
			i = list(filter(
				lambda t: t[1] == args and t[2] == kwargs,
				zip(itertools.count(), self.fargs, self.fkwargs),
			))[0][0]
		except IndexError:
			raise AssertionError("Error: function was called with unexpected arguments:\n" + \
				str(args) + " " + str(kwargs))
		
		if self.fwascalled[i]:
			raise AssertionError("Error: function was called more than once with arguments:\n" + \
				str(args) + " " + str(kwargs))
		
		self.fwascalled[i] = True
		
		return self.fresults[i]
	
	def reset(self, fargs, fkwargs, fresults):
		assert len(fargs) == len(fkwargs) == len(fresults), "Function was invoked with differently sized fargs, fkwargs, or fresults lists."
		
		self.fargs = fargs
		self.fkwargs = fkwargs
		self.fresults = fresults
		self.fwascalled = [False] * len(fargs)
	
	def hasCalls(self, *indeces):
		if 0 < len(indeces):
			return all([
				self.fwascalled[i]
				for i
				in indeces
			])
		else:
			return all(self.fwascalled)

class checkCallsMixin(unittest.TestCase):
	def checkCalls(self, mock, *calls):
		side_effect = mock.side_effect # Preserve the mock's return values across calls
		mock.assert_has_calls(calls)
		mock.reset_mock()
		mock.side_effect = side_effect

class testLooperMixin(unittest.TestCase):
	def loopTests(
		self,
		args,
		expecteds,
		f,
		befores = itertools.repeat(lambda: None),
		afters = itertools.repeat(lambda: None)
	):
		for [i, [arg, expected, before, after]] in enumerate(zip(args, expecteds, befores, afters)):
			with self.subTest(i = i):
				before()
				result = f(arg)
				self.assertEqual(result, expected)
				after()

class testSpecifications(testLooperMixin, checkCallsMixin):
	def test_SUM(self):
		args = [
			[[], 8],
			[[int], 5],
			[[int], "hi"],
			[[str, float, int], "blegh"],
			[[str, float, int], 38 + 5j],
		]
		
		expecteds = [
			False,
			True,
			False,
			True,
			False,
		]
		
		self.loopTests(args, expecteds, lambda t: SUM(*t[0]).verify(t[1]))
	
	@patch(__name__ + ".Ver")
	def test_PRODUCT(self, notVer):
		notVer.side_effect = [
			
			
			True, False,
			True, True, True, True,
		]
		
		args = [
			[[],
				[]],
			[[str, float],
				["bem", 2.9, 8 + 5j]],
			[[str, str, int],
				["hi", 0, 67]],
			[[int, int, str, float],
				[1, 5, "hello", 3.5]],
		]
		
		expecteds = [
			True,
			False,
			False,
			True,
		]
		
		afters = [
			lambda: None,
			lambda: None,
			lambda: self.checkCalls(notVer,
				call("hi", str),
				call(0, str),
			),
			lambda: self.checkCalls(notVer,
				call(1, int),
				call(5, int),
				call("hello", str),
				call(3.5, float),
			),
		]
		
		self.loopTests(args, expecteds, lambda t: PRODUCT(*t[0]).verify(t[1]), afters = afters)
	
	@patch(__name__ + ".Ver")
	def test_ITERABLE(self, notVer):
		notVer.side_effect = setwiseChecker([], [], [])
		
		summer = SUM(str, int)
		prodder = PRODUCT(str, int)
		
		args = [
			[list, float,
				[]],
			[tuple, float,
				[]],
			[tuple, str,
				("hi", "there")],
			[set, summer,
				{"1", 2, "3", 4}],
			[frozenset, prodder,
				frozenset({("1", 2), (3.0, 4), ("5", 6)})],
		]
		
		expecteds = [
			True,
			False,
			True,
			True,
			False,
		]
		
		def before2(): notVer.side_effect = setwiseChecker(
			[	("hi", str),	("there", str),
			], [	{},		{},
			], [	True,		True,
			]
		)
		
		def before3(): notVer.side_effect = setwiseChecker(
			[	("1", summer),	(2, summer),	("3", summer),	(4, summer),
			], [	{},		{},		{},		{},
			], [	True,		True,		True,		True,
			]
		)
		
		def before4(): notVer.side_effect = setwiseChecker(
			[	(("1", 2), prodder),	((3.0, 4), prodder),	(("5", 6), prodder),
			], [	{},			{},			{},
			], [	True,			False,			True,
			]
		)
		
		befores = [
			lambda: None,
			lambda: None,
			before2,
			before3,
			before4,
		]
		
		afters = [
			lambda: None,
			lambda: None,
			lambda: self.assertTrue(notVer.hasCalls()),
			lambda: self.assertTrue(notVer.hasCalls()),
			lambda: self.assertTrue(notVer.hasCalls(1)),
		]
		
		self.loopTests(args, expecteds, lambda t: ITERABLE(t[0], t[1]).verify(t[2]), befores = befores, afters = afters)
	
	def test_DICT(self):
		### This is just a blueprint for the mocks used
		
		#prodder = PRODUCT(str, int)
		#summer = SUM(
		#	PRODUCT(float, int),
		#	PRODUCT(
		#		SUM(
		#			str,
		#			complex
		#		),
		#		float,
		#	)
		#)
		
		prodder = Mock(verify = Mock())
		summer = Mock(verify = Mock())
		
		args = [
			[prodder,
				{}],
			[prodder,
				{"hello": 5, "bye": 3}],
			[prodder,
				{5.5: 0, "chicken": 4}],
			[summer,
				{}],
			[summer,
				{4.4: 7, 4 + 6j: 6.6}],
			[summer,
				{"Hg": 80.0, "Pb": 82 + 0j}],
		]
		
		expecteds = [
			True,
			True,
			False,
			True,
			True,
			False,
		]
		
		def before1(): prodder.verify.side_effect = setwiseChecker(
			[	(["hello", 5],),	(["bye", 3],),
			], [	{},			{},
			], [	True,			True,
			]
		)
		
		def before2(): prodder.verify.side_effect = setwiseChecker(
			[	([5.5, 0],),	(["chicken", 4],),
			], [	{},		{},
			], [	False,		True,
			]
		)
		
		def before4(): summer.verify.side_effect = setwiseChecker(
			[	([4.4, 7],),	([4 + 6j, 6.6],),
			], [	{},		{},
			], [	True,		True,
			]
		)
		
		def before5(): summer.verify.side_effect = setwiseChecker(
			[	(["Hg", 80.0],),	(["Pb", 82 + 0j],),
			], [	{},			{},
			], [	True,			False,
			]
		)
		
		befores = [
			lambda: None,
			before1,
			before2,
			lambda: None,
			before4,
			before5,
		]
		
		afters = [
			lambda: None,
			lambda: self.assertTrue(prodder.verify.side_effect.hasCalls()),
			lambda: self.assertTrue(prodder.verify.side_effect.hasCalls(0)),
			lambda: None,
			lambda: self.assertTrue(summer.verify.side_effect.hasCalls()),
			lambda: self.assertTrue(summer.verify.side_effect.hasCalls(1)),
		]
		
		self.loopTests(args, expecteds, lambda t: DICT(t[0]).verify(t[1]), befores = befores, afters = afters)

if __name__ == "__main__":
	unittest.main()

#def example_func(pipe):
#	
#	response = Des(pipe.recv_bytes())
#	spec = TBG.LIST(
#		TBG.DICT(
#			TBG.SUM(
#				TBG.PRODUCT(
#					frozenset,
#					int,
#				),
#				TBG.PRODUCT(
#					str,
#					complex,
#				),
#			)
#			length = 1,
#		),
#		minlength = 5,
#		maxlength = 10
#	)
#	
#	if Ver(response, spec):
#		pass
#	else:
#		pass
