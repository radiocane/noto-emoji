#!/usr/bin/env python
#
# Copyright 2017 White_Rabbit.
#
# Licensed under the CC0.
# https://creativecommons.org/publicdomain/zero/1.0/legalcode

from __future__ import division

import os
import shutil

from PIL import Image

"""Generate a pidgin smiley theme from the images.

This script will create a directory, fill it with images taken from this
project and create a suitable text file called 'theme'. The directory can
be used as a pidgin smiley theme [0, 1]. Flags for country subdivisions are
encoded according to the specification [2].

References
[0] https://github.com/nobuyukinyuu/pidgin-emoji
[1] https://developer.pidgin.im/wiki/SmileyThemes
[2] http://www.unicode.org/reports/tr51/tr51-11.html"""

IMG_DIR = os.path.join('png', '128')
FLAG_DIR = os.path.join('third_party', 'region-flags', 'png')
THEME_DIR = 'noto-emoji'

os.mkdir(THEME_DIR)
theme = open(os.path.join(THEME_DIR, 'theme'), 'w')
# Theme header
theme.write('# Encoding utf-8\n')
theme.write('# https://github.com/radiocane/noto-emoji\n')
theme.write('Name=Noto Emoji\n')
theme.write('Description=All Google/Android emojis\n')
theme.write('Icon=EU.png\n')
theme.write('Author=White_Rabbit\n\n')

theme.write('[default]\n')

imgs = os.listdir(IMG_DIR)
imgs.sort()
for f in imgs:
    # Only emoji imgs
    if f[:7] != 'emoji_u':
        continue
    f_int = [int(cp, base=16) for cp in f[7:-4].split('_')]
    # No emoji for low codepoints
    if len(f_int) == 1 and f_int[0] < 0xFF:
        continue
    f_uni = u''.join((unichr(i) for i in f_int))
    theme.write(u'{}\t{}\n'.format(f, f_uni).encode('utf-8'))

    source = os.path.join(IMG_DIR, f)
    dest = os.path.join(THEME_DIR, f)
    shutil.copy(source, dest) 

flags = os.listdir(FLAG_DIR)
flags.sort()
RIS_BASE = 0x1F1A5  # REGION INDICATOR SYMBOL
TAG_BASE = u'\U0001F3F4'
TAG_SPEC = 0xE0000
TAG_TERM = u'\U000E007F'
links = {}
for g in flags:
    # Get encoding
    if len(g) == 6:
        # Two-letter code -> REGIONAL INDICATOR SYMBOL
        g_int = (RIS_BASE + ord(g[0]), RIS_BASE + ord(g[1]))
        # Some flags are already present as imgs. They're skipped here.
        g_imgs = 'emoji_u{:x}_{:x}.png'.format(g_int[0], g_int[1])
        if os.path.exists(os.path.join(THEME_DIR, g_imgs)):
            print('{} exists as {}'.format(g, g_imgs))
            continue
        g_uni = unichr(g_int[0]) + unichr(g_int[1])
    else:
        # Country subdivision -> tag_base + tag_spec: cc s* + tag_term
        # 'cc' = country
        # 's*' = subdivision
        letters = g.rstrip('.png').replace('-', '').lower()
        tag_spec = u''.join(unichr(TAG_SPEC + ord(l)) for l in letters)
        g_uni = TAG_BASE + tag_spec + TAG_TERM

    source = os.path.join(FLAG_DIR, g)
    # Some 2-letter flags are symlinks to 2-letter flags. Populate a dict
    # with key=pointed val=tab-separated pointing.
    if os.path.islink(source):
        pointed = os.readlink(source)
        pointed_uni = unichr(RIS_BASE + ord(pointed[0])) + unichr(RIS_BASE + ord(pointed[1]))
        if links.has_key(pointed_uni):
            links[pointed_uni] = links[pointed_uni] + u'\t' + g_uni
        else:
            links[pointed_uni] = u'\t' + g_uni
        continue
    dest = os.path.join(THEME_DIR, g)
    shutil.copy(source, dest) 

    theme.write(u'{}\t{}\n'.format(g, g_uni).encode('utf-8'))

theme.flush()
theme.close()
print('Images copied to theme folder.')

if links != {}:
    # Find the line pointed and add the pointing g_uni(s).
    t_path = os.path.join(THEME_DIR, 'theme')
    o_path = os.path.join(THEME_DIR, 'oldtheme')
    shutil.move(t_path, o_path)
    with open(o_path, 'r') as oldtheme:
        with open(t_path, 'w') as theme:
            for line in oldtheme:
                uni = line.rstrip().split('\t')[-1].decode('utf-8')
                if uni in links:
                    theme.write(line[:-1] + links[uni].encode('utf-8') + '\n')
                else:
                    theme.write(line)
    os.remove(o_path)

print('Theme file completed.')
print('Resizing images, please wait...')

# Resize images
TARGET_WIDTH = 25
for i in os.listdir(THEME_DIR):
    if i[-3:] != 'png':
        continue
    i_path = os.path.join(THEME_DIR, i)
    img = Image.open(i_path)
    ratio = img.width / TARGET_WIDTH
    t_height = int(round(img.height / ratio))
    img.resize((TARGET_WIDTH, t_height), Image.ANTIALIAS).save(i_path)

print('Resize complted.')
