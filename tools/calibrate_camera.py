#!/usr/bin/env python3
"""Open the integrated calibration interface; replaces the old unchecked RMS helper."""
import argparse
import webbrowser

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--url', default='http://127.0.0.1:8077/')
args = parser.parse_args()
url = args.url.rstrip('/') + '/#calibration'
print('Start wingxtra-pl first, then calibrate at: ' + url)
webbrowser.open(url)
