from OSUCS461.Utilities import bisectSearchRC

class PositiveNumbers:
	Code = None
	MaxValue = None
	WkgSize = None
	EncodedLength = None

	def __init__(self, size=7, code=None):
		self.Code = [c for c in code or '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz']
		self.EncodedLength = size
		self.WkgSize = len(self.Code)
		self.MaxValue = int(self.WkgSize**self.EncodedLength)

# 		print 'EncodedLength:', self.EncodedLength
# 		print 'WkgSize:', self.WkgSize
# 		print 'MaxValue:', self.MaxValue

	def encode(self, n):
		if n < 0 or n > self.MaxValue: return;
		if n < self.WkgSize:
			return str(self.Code[int(n-self.WkgSize)]).rjust(self.EncodedLength, '0')
		else:
			def getchar(n, i):
# 				print 'getchar:', n, i
				tmpn = n-self.WkgSize
# 				print 'tmpn(b4):', tmpn
				if i != self.EncodedLength:
# 					print 'tmpn -> i != self.EncodedLength:', tmpn, self.WkgSize, i, (self.WkgSize**i)
					tmpn = (tmpn/self.WkgSize**i);
# 				print 'tmpn:', tmpn, '\n'
				return self.Code[int(tmpn%self.WkgSize)]
			return ''.join([getchar(n,i) for i in range(1, self.EncodedLength+1)])

	def decode(self, c):
# 		print 'decode:', c
		if len(c) == 1: return bisectSearchRC(self.Code, c);

		item_alt = 0
		if c[0] != '0': item_alt = self.WkgSize;

		for i in range(1, self.EncodedLength+1):
			wkg_char = c[i-1:i]
#  			print "wkg_character:", wkg_char
			if wkg_char == '0': continue;
			char = bisectSearchRC(self.Code, wkg_char)
			if i != self.EncodedLength: item_alt += char*(self.WkgSize**i);
			else: item_alt += char;
		return item_alt

	def e(self, n): return self.encode(n)

	def d(self, n): return self.decode(n)


PositiveNumbers7Char = PositiveNumbers(7)
PositiveNumbers9Char = PositiveNumbers(9)


if __name__ == "__main__":
	g = PositiveNumbers7Char

	def test(v):
	# 	print
		e = g.e(v)
		print ('%s.encode: %s' % (v,e))
		d = g.d(e) if e else None
	# 	print '%s.decode: %s' % (v,d)
		print ('%s == %s: %s' % (v, d, (v == d)))
		return (v == d)

	test(1)
	test(15)
	test(60)
	test(61)
	test(62)
	test(63)
	test(1000)
	test(12123)
	test(12124)
	test(12125)
	test(25000)
	test(88471)
	test(5045902)
	test(25760187211)
	test(3142712836021)
