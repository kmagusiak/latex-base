#!/usr/bin/env python
# Streams a markdown file.
#
# Uses concatenation for documents imported using:
# ![description](filename.md)

import os.path
import re
import sys

MD_EXT = ['md', 'markdown', 'mkdn', 'mdown']

def copy_markdown(out, filename, copyHeader = True):
	""" Copies the markdown file to the output stream """
	sys.stderr.write("Reading markdown: %s\n" % filename)
	try:
		with open(filename, 'r') as f:
			header = not copyHeader
			for line in f:
				if header:
					if line.strip().startswith('%'):
						continue
					else:
						header = False
				m = None
				if not header:
					m = re.search('!\[[^]]+\]\(([^)]+)(?:\s["\'].*["\'])?\)', line)
				if m is not None:
					ref = m.group(1)
					if os.path.splitext(ref)[1] in ['.' + ext for ext in MD_EXT]:
						out.write(line[:m.start()])
						copy_markdown(out, ref, False)
						out.write(line[m.end():])
						continue
				out.write(line)
	except IOError as e:
		sys.stderr.write("IOError when reading: %s\n" % filename)
		out.write(str(e))

if __name__ == '__main__':
	"""The main program."""
	out = sys.stdout
	first = True
	for f in sys.argv[1:]:
		copy_markdown(out, f, first)
		first = False
