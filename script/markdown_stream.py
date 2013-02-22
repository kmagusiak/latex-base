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
HEADER_LINES = ['title', 'author', 'date']

def copy_markdown(out, filename,
		copy_header=False,
		recursion=None,
		err=sys.stderr):
	"""Copies the markdown file to the output stream.

	out: the output stream
	filename: the file from which to read
	copy_header=False: whether to copy the header to the output
	recursion=None: array of function to copy recursively
	err=sys.stderr: stream to print error messages

	The recursion a dictionary of str extensions to functions applied when an
	extension matches. A default function can be given for an extension ''.
	If None is given, it is initialized using RECURSION_FUNCTIONS.
	"""
	err.write("Reading markdown: %s\n" % filename)
	if recursion is None:
		recursion = RECURSION_FUNCTIONS
	try:
		with open(filename, 'r') as f:
			header = len(HEADER_LINES) if copy_header else None
			for line in f:
				if header is not None:
					if line.strip().startswith('%'):
						if header > 0: out.write(line)
						header -= 1
						continue
					else:
						header = None
				m = re.search(r'!\[[^]]+\]\(([^)]+)(?:\s["\'].*["\'])?\)',
						line)
				if m is not None and m.group(1).find("://") < 0:
					ref = m.group(1)
					ext = os.path.splitext(ref)[1][1:]
					if ext in recursion or '' in recursion:
						out.write(line[:m.start()])
						recfunc = recursion[ext] if ext in recursion else recursion['']
						recfunc(out, ref, recursion=recursion, err=err)
						out.write(line[m.end():])
						continue
					else:
						err.write("Included file (skipped): %s\n" % ref)
				out.write(line)
	except IOError as ex:
		err.write("IOError when reading: %s\n" % filename)
		out.write(str(ex))
		out.write("\n")

def parse_header(filename):
	"""Parses the header of a markdown file.

	Returns a dict containing:
	- author (str)
	- date (str)
	- title (str)
	- args ([str])
	Returns None when there is no header.
	"""
	header = {prop: '' for prop in HEADER_LINES}
	header['args'] = []
	order = [None] + HEADER_LINES
	with open(filename, 'r') as f:
		i = 0
		for line in f:
			i += 1
			line = line.strip()
			if not line.startswith('%'):
				if i == 1:
					return None
				break
			line = line[1:].strip()
			key = i
			if i < len(order):
				header[order[i]] = line
			else:
				header['args'].append(line)
	return header

def execute(input_files, out=sys.stdout, err=sys.stderr, header=True):
	"""Executes the copy of markdown files."""
	for filename in input_files:
		copy_markdown(out, filename, copy_header=header, err=err)
		header = False

def main(out=sys.stdout, err=sys.stderr):
	"""The main program.

	Usage: [--no-header] [--exec prog] -- input files

	--no-header does not output the header
	--exec pipes the output to a sub-process
	"""
	# Variables
	prog = None
	input_files = None
	header = True
	# Parse arguments
	for arg in sys.argv[1:]:
		if arg == '--':
			input_files = []
			continue
		if input_files is not None:
			input_files.append(arg)
			continue
		if prog is not None:
			prog.append(arg)
			continue
		if arg == '--exec':
			prog = []
			continue
		if arg == '--no-header':
			header = False
			continue
		input_files = [arg]
	if input_files is None or len(input_files) == 0:
		err.write("No input files\n")
		return
	# Parse the header
	header = parse_header(input_files[0])
	if header is not None:
		for h in HEADER_LINES:
			err.write("%s: %s\n" % (h, header[h]))
		if prog is not None:
			prog = prog + header['args']
	# Execute
	wait = None
	if prog is not None:
		err.write("Piping output: %s\n" % str(prog))
		import io
		import subprocess
		progp = subprocess.Popen(prog, stdin=subprocess.PIPE)
		out = io.TextIOWrapper(progp.stdin)
		wait = progp
	execute(input_files, header=header, out=out, err=err)
	# Wait
	if wait is not None:
		err.write("Document transformed\n")
		out.close()
		wait.wait()

RECURSION_FUNCTIONS = {e: copy_markdown for e in MD_EXT}

if __name__ == '__main__':
	main()
