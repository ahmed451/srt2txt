#!/usr/bin/env python
"""
vtt2txt - Convert text subtitles from the VTT format to Adobe text scripts (for use in Encore)

VTT files as exported from YouTube include timestamps in this format:

WEBVTT
Kind: captions
Language: en

00:03:17.440 --> 00:03:19.440
Subtitle text

...

Adobe TXT uses timecode frames, so we depend on the framerate (NTSC or PAL) :

Text subtitle scripts should follow this format
(from http://help.adobe.com/en_US/encore/cs/using/WSbaf9cd7d26a2eabfe807401038582db29-7ea2a.html)

Subtitle_# Start_Timecode End_Timecode Subtitle_text

Additional_line_of_subtitle_text

Additional_line_of_subtitle_text

NTSC: Frame # = (milliseconds * 29.97) / 1000

PAL: Frame # = (milliseconds * 25) / 1000

Update: Wed Dec 27 20:01:20 2017 
Make code compatible with python 3
Fix residual entry
aabdelali at hbku dot edu

"""

__author__ = 'Stephane Peter'
__email__ = 'megastep@megastep.org'

import sys
import argparse

# Input states
#SUB_NUMBER = 1
SUB_TIMES = 2
SUB_STRINGS = 3
VTT_HEADER = 4


def convert(vttfile, txtfile, format, gap):
    if format == 'pal':
        sep = ':'
        fps = 25
    else:  # NTSC
        sep = ';'
        fps = 29.97

    def to_frames(timecode):
        (t, ms) = timecode.split('.')
        elts = t.split(':')
        return ((int(elts[0])*3600 + int(elts[1])*60 + int(elts[2]))*1000 + int(ms)) * fps / 1000

    def convert_timecode(timecode, inc=0):
        (t, ms) = timecode.split('.')
        elts = t.split(':')
        return "%s%s%d" % (sep.join(elts), sep, (int(ms) * fps / 1000)+inc)

    last_end = 0
    state = VTT_HEADER
    subnum = 0
    for line in vttfile.readlines():
        line = line.strip()
        if state == SUB_TIMES and " --> " in line:
            times = line.strip().split(" --> ")
            txt = ""
            state = SUB_STRINGS
        elif state == SUB_STRINGS:
            if len(line.strip()) == 0:  # Just \n, end of entry
                #print("Time:",times," last:",last_end)
                diff = to_frames(times[0]) - last_end
                if diff < gap:
                    start = convert_timecode(times[0], gap - diff)
                else:
                    start = convert_timecode(times[0])
                if len(txt) != 0:
                    txtfile.write("{0:d}\t{1:s}\t{2:s}\t{3:s}\n".format(subnum, start, convert_timecode(times[1]), txt))
                last_end = to_frames(times[1])
                state = SUB_TIMES
            else:
                txt += line + ' ' # Connecting lines
        elif state == VTT_HEADER:
            if len(line.strip()) == 0:
                state = SUB_TIMES
    if len(line.strip()) != 0:
        txtfile.write("{0:d}\t{1:s}\t{2:s}\t{3:s}\n".format(subnum, start, convert_timecode(times[1]), txt,len()))
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert subtitles to Adobe text format.')
    parser.add_argument('--format', default='pal', choices=['ntsc', 'pal'],
                        help="Encoding to use (NTSC or PAL [default])")
    parser.add_argument('--gap', default=5, type=int,
                        help="Number of frames to insert between subsequent clips if needed (default = 5)")
    parser.add_argument('vttfile', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help="Filename for source VTT file.")
    parser.add_argument('txtfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
                        help="Destination file for converted Adobe data.")
    args = parser.parse_args()
    convert(args.vttfile, args.txtfile, args.format, args.gap)

