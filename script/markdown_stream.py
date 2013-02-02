#!/usr/bin/env python
# Streams a markdown file.
#
# Uses concatenation for documents imported using:
# ![description](filename.md)

import os.path
import re
import sys

MD_EXT = ['md', 'markdown', 'mkdn', 'mdown']

def copy_markdown(out, filename, copyHeader=False,
		recursion=None, ext=MD_EXT,
		err=sys.stderr):
	""" Copies the markdown file to the output stream """
	err.write("Reading markdown: %s\n" % filename)
	if recursion is None:
		recursion = copy_markdown
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
					if os.path.splitext(ref)[1] in ['.' + ext for ext in ext]:
						out.write(line[:m.start()])
						recursion(out, ref)
						out.write(line[m.end():])
						continue
				out.write(line)
	except IOError as e:
		err.write("IOError when reading: %s\n" % filename)
		out.write(str(e))

if __name__ == '__main__':
	"""The main program."""
	out = sys.stdout
	first = True
	for f in sys.argv[1:]:
		copy_markdown(out, f, first)
		first = False
