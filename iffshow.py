#!/usr/bin/env python

# Show an IFF-ILBM file in a PyGame window

import pygame
import sys, os, time
from math import ceil

# window resolution
res = 1200, 900

fn = sys.argv[1]

f = open(fn, "rb")

a = bytearray(f.read())

def limit(x):
    "Exclude forbidden characters in chunk names; print a question mark instead"
    if x < 0x20 or x > 0x7e:
        x = 0x3f
    return x

def s(n):
    "Get chunk name"
    return "".join([chr(limit(a[q])) for q in range(n, n+4)])

def get_size(n):
    "Get chunk size"
    return 256**3 * a[n] + 256**2 * a[n+1] + 256 * a[n+2] + a[n+3]

xdim, ydim, planes, comp, HAM = 0, 0, 1, False, False
colormap = []

def bmhd(n):
    "BMHD chunk handler"
    global xdim, ydim, planes, comp

    xdim = 256*a[n+8] + a[n+9]
    ydim = 256*a[n+10] + a[n+11]
    planes = a[n+16]
    if a[n+18]:
        nc = ""
        comp = True
    else:
        nc = "not "
    print(f"{xdim}x{ydim}, {planes} planes, {nc}compressed")
    if planes == 24 or planes == 32:
        print("deep image")

def cmap(n):
    "CMAP chunk handler"
    global colormap

    s = get_size(n+4)
    n += 8
    cm1, cm2 = [], []
    for i in range(s // 3):
        cm1.append( (a[n+3*i], a[n+3*i+1], a[n+3*i+2]) )
        # add EHB colors:
        cm2.append( (a[n+3*i]//2, a[n+3*i+1]//2, a[n+3*i+2]//2) )
    #print(colormap)
    colormap = cm1 + cm2
    print(s // 3, "colors loaded")

if s(0) != "FORM":
    print("not a FORM")
    sys.exit(1)

if s(8) != "ILBM":
    print("not an ILBM")
    sys.exit(1)

file_size = get_size(4) + 8

pos = 12

body_start = 0

while True:
    ch = s(pos)
    siz = get_size(pos+4)
    print("chunk:", ch, "; size:", siz)
    if ch == "BMHD":
        bmhd(pos)
    if ch == "CMAP":
        cmap(pos)
    if ch == "CAMG":
        if a[pos + 10] & 8:
            print("HAM mode")
            HAM = True 
    if ch == "BODY":
        body_start = pos + 8
    if siz % 2:
        siz += 1
    pos += 8 + siz
    if pos >= len(a) or pos >= file_size:
        break

img = pygame.Surface((xdim, ydim))

pos = body_start

bits_per_line = 16 * int(ceil(xdim / 16))
bytes_per_line = int(bits_per_line * planes / 8)

for y in range(ydim):
    # handle run-length image compression
    if comp == 1:
        tmp = []
        while True:
            con = a[pos]
            # http://fileformats.archiveteam.org/wiki/PackBits
            if 0 <= con <= 127:
                for k in range(con+1):
                    tmp.append(a[pos+1+k])
                pos += con + 2
            elif 129 <= con <= 255:
                for k in range(257 - con):
                    tmp.append(a[pos+1])
                pos += 2
            else:
                pos += 1
            if len(tmp) > bytes_per_line:
                print(y, "error")
                1/0
            if len(tmp) == bytes_per_line:
                break
        bb = bytearray(tmp)
    else:
        bb = a[pos:pos+bytes_per_line]
        pos += bytes_per_line

    bits = ""
    for n in range(bytes_per_line):
        bits += format(bb[n], '08b')

    # set up HAM variables
    if HAM:
        rr, gg, bb = 0, 0, 0
        hi, lo = 2**(planes-1), 2**(planes-2)
        if planes == 6:
            fact = 16
            mask = 15
        if planes == 8:
            fact = 4
            mask = 63
    for x in range(xdim):
        col = 0
        for p in range(planes):
            if bits[bits_per_line * p + x] == "1":
                col |= 1 << p
        if planes == 24 or planes == 32:
            bb = (col >> 16) & 255
            gg = (col >>  8) & 255
            rr =  col        & 255
            img.set_at((x, y), (rr, gg, bb))
        elif HAM:   # https://en.wikipedia.org/wiki/ILBM
            if col & hi == 0 and col & lo == 0:
                index = col & mask
                img.set_at((x, y), colormap[index])
                rr, gg, bb = colormap[index][0], colormap[index][1], colormap[index][2]
            if col & hi == 0 and col & lo == lo:
                bb = fact * (col & mask)
                img.set_at((x, y), (rr, gg, bb))
            if col & hi == hi and col & lo == lo:
                gg = fact * (col & mask)
                img.set_at((x, y), (rr, gg, bb))
            if col & hi == hi and col & lo == 0:
                rr = fact * (col & mask)
                img.set_at((x, y), (rr, gg, bb))
        else:
            img.set_at((x, y), colormap[col])


# Open a PyGame window

pygame.init()

screen = pygame.display.set_mode(res)
img2 = pygame.transform.scale(img, res)
run = True
pygame.display.set_caption(f"IFFshow: {os.path.basename(fn)} ({xdim}x{ydim})")

while run:
    for event in pygame.event.get():
        if (event.type == pygame.QUIT or 
            (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE)):
            run = False
    screen.blit(img2, (0, 0))
    pygame.display.flip()
    time.sleep(0.1)

pygame.quit()


