import bitstring

def foo(a, b, c, d):
    return bitstring.pack('uint:8, 0b110, int:6, bin, bits', a, b, c, d)

s1 = foo(12, 5, '0b00000', '')
s2 = foo(101, 3, '0b11011', s1)

print s1, s2