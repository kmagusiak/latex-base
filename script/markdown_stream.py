#!/usr/bin/env python
"""
Streams a markdown file.

Uses concatenation for documents imported using:

	![description](filename.md)

"""

import os.path
import re
import sys

MD_EXT = ['md', 'markdown', 'mkdn', 'mdown']

def copy_markdown(out, filename,
		copy_header=False,
		recursion=None, ext=None,
		err=sys.stderr):
	""" Copies the markdown file to the output stream """
	err.write("Reading markdown: %s\n" % filename)
	if recursion is None:
		recursion = copy_markdown
	if ext is None:
		ext = MD_EXT
	try:
		with open(filename, 'r') as f:
			header = not copy_header
			for line in f:
				if header:
					if line.strip().startswith('%'):
						continue
					else:
						header = False
				m = None
				if not header:
					m = re.search(r'!\[[^]]+\]\(([^)]+)(?:\s["\'].*["\'])?\)', line)
				if m is not None:
					ref = m.group(1)
					if os.path.splitext(ref)[1] in ['.' + ext for ext in ext]:
						out.write(line[:m.start()])
						recursion(out, ref,
								recursion=recursion, ext=ext, err=err)
						out.write(line[m.end():])
						continue
				out.write(line)
	except IOError as ex:
		err.write("IOError when reading: %s\n" % filename)
		out.write(str(ex))

def main():
	"""The main program"""
	out = sys.stdout
	first = True
	for filename in sys.argv[1:]:
		copy_markdown(out, filename, first)
		first = False

if __name__ == '__main__':
	main()
