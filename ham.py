#!/usr/bin/env python

# Convert an image file to HAM6 IFF-ILBM

import sys
import pygame

# output image width and height
res = 320, 256

fn = sys.argv[1]

img = pygame.image.load(fn)

# scale image down to given Amiga resolution
img = pygame.transform.smoothscale(img, res)

# image width and height
W, H = img.get_size()

def bit16(i):
    return [i // 256, i % 256]

w1, w2 = bit16(W)
h1, h2 = bit16(H)

def bit32(i):
    h = "%08x" % i
    w = [h[k:k+2] for k in (0,2,4,6)]
    return [int(q, 16) for q in w]

form = [
 70,   # F
 79,   # O
 82,   # R
 77,   # M
]

camg = [
 67,   # C
 65,   # A
 77,   # M
 71,   # G
  0,   # 
  0,   # 
  0,   # 
  4,   # 
  0,   # 
  0,   # 
  8,   # HAM mode
  0,   # 
]

ilbm = [
 73,   # I
 76,   # L
 66,   # B
 77,   # M
 66,   # B
 77,   # M
 72,   # H
 68,   # D
  0,   #   s
  0,   #   i
  0,   #   z
 20,   #   e
 w1,   # wid 1
 w2,   # wid 2
 h1,   # hei 1
 h2,   # hei 2
  0,   #  xor 1
  0,   #  xor 2
  0,   #  yor 1
  0,   #  yor 2
  6,   # planes
  0,   # mask 
  0,   # compression
  0,   # pad
  0,   #  trans1
  0,   #  trans2
 10,   # x aspect
 11,   # y aspect
 w1,   #  x wid1
 w2,   #  x wid2
 h1,   #  y hei1
 h2,   #  y hei2
]

body = [
 66,   # B
 79,   # O
 68,   # D
 89,   # Y
]


p = []

def get_data(rgb):
    "Convert a line of RGB values to a list of HAM6 bytes"
    cr, cg, cb = 0, 0, 0
    out = []
    for x in range(W):
        dr, dg, db = rgb[x][0], rgb[x][1], rgb[x][2]
        di = abs(cr - dr), abs(cg - dg), abs(cb - db)
        maxdiff = max(di)
        if abs(cr - dr) == maxdiff:
            c = 32 + dr // 16
            cr = dr
        elif abs(cg - dg) == maxdiff:
            c = 32 + 16 + dg // 16
            cg = dg
        else:
            c = 16 + db // 16
            cb = db
        out.append(c)
    return out

def bit_at(x, data, b):
    c = data[x]
    c = ( c >> b ) & 1
    return c

for y in range(H):
    rgb = []
    for x in range(W):
        rgb.append(img.get_at((x, y)))
    data = get_data(rgb)
    line = []
    for b in range(6):
        for x in range(W):
            line.append(bit_at(x, data, b))

    for ibyte in range(0, len(line), 8):
        bb = "".join([str(q) for q in line[ibyte:ibyte+8]])
        p.append(int(bb, 2))

out = ilbm + camg + body + bit32(len(p)) + p

out = form + bit32(len(out)) + out

out = bytearray(out)

g = open(fn + "-ham6.iff", "wb")

g.write(out)

g.close()

