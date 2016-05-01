#!/usr/bin/env python3

# Generate prototyping board (grid of pads) for Eagle CAD
# Copyright 2016 Eric Smith <spacewar@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the version 3 of the GNU General Public License
# as published by the Free Software Foundation.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import collections
import math
import re
import sys
from xml.etree.ElementTree import ElementTree, Element, SubElement, Comment, tostring


re_fract_str = "(((\d+)\+)?)(\d+)/(\d+)"
re_fract = re.compile(re_fract_str)

def fract_arg(s):
    m = re_fract.match(s)
    if not m:
        raise argparse.ArgumentTypeError("bad argument value")
    if m.group(3):
        base = int(m.group(3))
    else:
        base = 0
    num = int(m.group(4))
    denom = int(m.group(5))
    value = (1.0 * base) + (1.0 * num) / (1.0 * denom)
    return value

def inch_arg(s):
    try:
        value = float(s)
    except:
        value = fract_arg(s)
    return value

parser = argparse.ArgumentParser(description='Prototyping board generator for Eagle CAD',
                                 epilog='Parameters specified in inches may be provided as integers (e.g. 3), decimals (e.g., 3.5), or integers with fractions (separated by a plus sign, e.g. 3+1/8).')
parser.add_argument("width",   help="overall board width (inches)",  type=inch_arg)
parser.add_argument("length",  help="overall board length (inches)", type=inch_arg)
parser.add_argument("outfile", help="Eagle board file",              type=argparse.FileType('wb'))
                    #, nargs='?', default=sys.stdout)
                    # doesn't work because can't write binary encoded UTF-8 to stdout  :-(
parser.add_argument("-w",      help="hole count, width",             type=int)
parser.add_argument("-l",      help="hole count, length",            type=int)
parser.add_argument("--grid",  help="grid pitch (inches)",           type=inch_arg, default=0.1)
parser.add_argument("--drill", help="drill diameter (inches)",       type=inch_arg, default=0.042)
parser.add_argument("--pad",   help="pad diameter (inches)",         type=inch_arg, default=0.075)

parser.add_argument("--no-mtg", help="no mounting holes", action='store_true')

parser.add_argument("--mtg",   help="mounting hole dia (inches)",    type=inch_arg, default=0.125)
parser.add_argument("--inset", help="mounting hole inset (inches)",  type=inch_arg, default=0.1875)
parser.add_argument("--corner", help="exclude corner rows",         type=int,      default=3)

args = parser.parse_args()
print(args)

width = args.width
height = args.length

inset  = args.inset
if args.no_mtg:
    mtg_hole_dia = None
else:
    mtg_hole_dia = args.mtg

grid_pitch = args.grid
pad_drill = args.drill
pad_dia = args.pad

border = 0.015

exclude_corner_pads = args.corner

if args.l is not None:
    pads_h = args.l
else:
    pads_h = math.floor((height-border)/grid_pitch)

if args.w is not None:
    pads_w = args.w
else:
    pads_w = math.floor((width-border)/grid_pitch)


print("%d x %d" % (pads_w, pads_h))

holes = []
for x in (inset, width - inset):
    for y in (inset, height - inset):
        holes.append((x, y))

def distance(c1, c2):
    return math.sqrt((c2[0]-c1[0])**2 + (c2[1]-c1[1])**2)

def too_close(x, y, threshold = 0.1875):
    global holes
    for h in holes:
        if distance((x, y), h) < threshold:
            return True
    return False


def in_to_mm(x):
    return x * 25.4

Layer = collections.namedtuple('Layer', ['number',
                                         'name',
                                         'color',
                                         'fill',
                                         'visible',
                                         'active'])

eagle = Element('eagle', { 'version': '6.5.0' })

drawing = Element('drawing')
eagle.append(drawing)

settings = Element('settings')
drawing.append(settings)

settings.append(Element('setting', {'alwaysvectorfont': 'no'}))
settings.append(Element('setting', {'verticaltext': 'up'}))

drawing.append(Element('grid', {'distance':    '0.050',
                                'unitdist':    'inch',
                                'unit':        'inch',
                                'style':       'lines',
                                'multiple':    '1',
                                'display':     'no',
                                'altdistance': '0.025',
                                'altunitdist': 'inch',
                                'altunit':     'inch'}))

layers_list = [ Layer(number='1',  name='Top',       color='4',  fill='1',  visible='yes', active='yes'),
                Layer(number='2',  name='Route2',    color='1',  fill='3',  visible='no',  active='no'),
                Layer(number='3',  name='Route3',    color='4',  fill='3',  visible='no',  active='no'),
                Layer(number='4',  name='Route4',    color='1',  fill='4',  visible='no',  active='no'),
                Layer(number='5',  name='Route5',    color='4',  fill='4',  visible='no',  active='no'),
                Layer(number='6',  name='Route6',    color='1',  fill='8',  visible='no',  active='no'),
                Layer(number='7',  name='Route7',    color='4',  fill='8',  visible='no',  active='no'),
                Layer(number='8',  name='Route8',    color='1',  fill='2',  visible='no',  active='no'),
                Layer(number='9',  name='Route9',    color='4',  fill='2',  visible='no',  active='no'),
                Layer(number='10', name='Route10',   color='1',  fill='7',  visible='no',  active='no'),
                Layer(number='11', name='Route11',   color='4',  fill='7',  visible='no',  active='no'),
                Layer(number='12', name='Route12',   color='1',  fill='5',  visible='no',  active='no'),
                Layer(number='13', name='Route13',   color='4',  fill='5',  visible='no',  active='no'),
                Layer(number='14', name='Route14',   color='1',  fill='6',  visible='no',  active='no'),
                Layer(number='15', name='Route15',   color='4',  fill='6',  visible='no',  active='no'),
                Layer(number='16', name='Bottom',    color='1',  fill='1',  visible='yes', active='yes'),
                Layer(number='17', name='Pads',      color='2',  fill='1',  visible='yes', active='yes'),
                Layer(number='18', name='Vias',      color='2',  fill='1',  visible='yes', active='yes'),
                Layer(number='19', name='Unrouted',  color='6',  fill='1',  visible='yes', active='yes'),
                Layer(number='20', name='Dimension', color='15', fill='1',  visible='yes', active='yes'),
                Layer(number='21', name='tPlace',    color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='22', name='bPlace',    color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='23', name='tOrigins',  color='15', fill='1',  visible='yes', active='yes'),
                Layer(number='24', name='bOrigins',  color='15', fill='1',  visible='yes', active='yes'),
                Layer(number='25', name='tNames',    color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='26', name='bNames',    color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='27', name='tValues',   color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='28', name='bValues',   color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='29', name='tStop',     color='7',  fill='3',  visible='no',  active='yes'),
                Layer(number='30', name='bStop',     color='7',  fill='6',  visible='no',  active='yes'),
                Layer(number='31', name='tCream',    color='7',  fill='4',  visible='no',  active='yes'),
                Layer(number='32', name='bCream',    color='7',  fill='5',  visible='no',  active='yes'),
                Layer(number='33', name='tFinish',   color='6',  fill='3',  visible='no',  active='yes'),
                Layer(number='34', name='bFinish',   color='6',  fill='6',  visible='no',  active='yes'),
                Layer(number='35', name='tGlue',     color='7',  fill='4',  visible='no',  active='yes'),
                Layer(number='36', name='bGlue',     color='7',  fill='5',  visible='no',  active='yes'),
                Layer(number='37', name='tTest',     color='7',  fill='1',  visible='no',  active='yes'),
                Layer(number='38', name='bTest',     color='7',  fill='1',  visible='no',  active='yes'),
                Layer(number='39', name='tKeepout',  color='4',  fill='11', visible='yes', active='yes'),
                Layer(number='40', name='bKeepout',  color='1',  fill='11', visible='yes', active='yes'),
                Layer(number='41', name='tRestrict', color='4',  fill='10', visible='yes', active='yes'),
                Layer(number='42', name='bRestrict', color='1',  fill='10', visible='yes', active='yes'),
                Layer(number='43', name='vRestrict', color='2',  fill='10', visible='yes', active='yes'),
                Layer(number='44', name='Drills',    color='7',  fill='1',  visible='no',  active='yes'),
                Layer(number='45', name='Holes',     color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='46', name='Milling',   color='3',  fill='1',  visible='no',  active='yes'),
                Layer(number='47', name='Measures',  color='7',  fill='1',  visible='no',  active='yes'),
                Layer(number='48', name='Document',  color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='49', name='Reference', color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='51', name='tDocu',     color='7',  fill='1',  visible='yes', active='yes'),
                Layer(number='52', name='bDocu',     color='7',  fill='1',  visible='yes', active='yes') ]
                

layers = Element('layers')
for l in layers_list:
    layers.append(Element('layer', l._asdict()))
drawing.append(layers)

board = Element('board')

plain = Element('plain')

# add board outline
plain.append(Element('wire', { 'x1': "%.3f" % 0,
                               'y1': "%.3f" % 0,
                               'x2': "%.3f" % 0,
                               'y2': "%.3f" % in_to_mm(height),
                               'width': '0',
                               'layer': '20' }))
plain.append(Element('wire', { 'x1': "%.3f" % 0,
                               'y1': "%.3f" % in_to_mm(height),
                               'x2': "%.3f" % in_to_mm(width),
                               'y2': "%.3f" % in_to_mm(height),
                               'width': '0',
                               'layer': '20' }))
plain.append(Element('wire', { 'x1': "%.3f" % in_to_mm(width),
                               'y1': "%.3f" % in_to_mm(height),
                               'x2': "%.3f" % in_to_mm(width),
                               'y2': "%.3f" % 0,
                               'width': '0',
                               'layer': '20' }))
plain.append(Element('wire', { 'x1': "%.3f" % in_to_mm(width),
                               'y1': "%.3f" % 0,
                               'x2': "%.3f" % 0,
                               'y2': "%.3f" % 0,
                               'width': '0',
                               'layer': '20' }))

if not args.no_mtg:
    for h in holes:
        plain.append(Element('hole', { 'x': "%.3f" % in_to_mm(h[0]),
                                       'y': "%.3f" % in_to_mm(h[1]),
                                       'drill': "%.3f" % in_to_mm(mtg_hole_dia) }))

board.append(plain)

signals = Element('signals')

pad_x_orig = (width - (pads_w - 1) * grid_pitch)/2
pad_y_orig = (height - (pads_h - 1) * grid_pitch)/2

signal_number = 0
for i in range(pads_w):
    x = pad_x_orig + i * grid_pitch
    for j in range(pads_h):
        y = pad_y_orig + j * grid_pitch
        if (not args.no_mtg and
            ((i < exclude_corner_pads) or (i >= pads_w - exclude_corner_pads)) and
            ((j < exclude_corner_pads) or (j >= pads_h - exclude_corner_pads))):
            continue
        signal_number += 1
        signal = Element('signal', { 'name': "S$%d" % signal_number })
        via = Element('via', { 'x': "%.3f" % in_to_mm(x),
                               'y': "%.3f" % in_to_mm(y),
                               'extent': '1-16',
                               'drill': "%.3f" % in_to_mm(pad_drill),
                               'diameter': "%.3f" % in_to_mm(pad_dia) })
        signal.append(via)
        signals.append(signal)

board.append(signals)

drawing.append(board)

doc = ElementTree(eagle)
doc.write(args.outfile, encoding='utf-8', xml_declaration=True)

