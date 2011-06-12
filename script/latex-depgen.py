#!/usr/bin/python
# Quick LaTeX file dependency generator

import re
import os.path
import sys

GEN_FROM = 'Makefile.files'
IMG_ROOT_DIR = 'img'
IMG_EXT_NORMAL = ['eps', 'jpg', 'pdf', 'png']
IMG_EXT_DEF = 'pdf' # must be in IMG_EXT_NORMAL
LISTINGS_EXT = ['c', 'cpp', 'idl', 'java', 'h', 'py', 'tex']

def getTexFileDep(filename, dep = None):
	"""Generates dependencies for a tex file."""
	# check the arguments
	if dep is None:
		dep = set()
	if os.path.splitext(filename)[1] != '.tex':
		sys.stderr.write("getTexFileDep(%s): works only for tex files\n"
			% filename)
		return dep
	if not os.path.isfile(filename):
		sys.stderr.write("getTexFileDep(%s): file does not exist\n"
			% filename)
		return dep
	# analyse the lines of the given file
	with open(filename, 'r') as f:
		match_arg = '\\{(.+?)\\}'
		match_opt = '(?:\\[[^\\]]*\\])?'
		match_opt_arg = match_opt + match_arg
		old_line = ''
		while True:
			line = f.readline()
			if line == '': break # eof
			(line, unfinished) = stripLatexLine(line, old_line)
			if unfinished:
				old_line = line
				continue
			old_line = ''
			if line == '': continue
			# -------------------------------
			# document class
			getTexFileDepMatch(dep, line,
				'\\\\documentclass' + match_opt_arg, ext = 'cls',
				optional = True)
			# style files
			getTexFileDepMatch(dep, line,
				'\\\\usepackage'+match_opt_arg, ext = 'sty',
				optional = True)
			# include | input
			getTexFileDepMatch(dep, line,
				'\\\\(?:input|include)' + match_arg, ext = 'tex')
			# bibliography
			getTexFileDepMatch(dep, line,
				'\\\\bibliography' + match_arg, ext = 'bib')
			# includegraphics
			getTexFileDepMatch(dep, line,
				'\\\\includegraphics' + match_opt_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF)
			# includeimage | includeimagefigure
			getTexFileDepMatch(dep, line,
				'\\\\includeimage(?:base|figure)?' + match_opt_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF,
				dir = IMG_ROOT_DIR)
			# lstinputlisting
			getTexFileDepMatch(dep, line,
				'\\\\lstinputlisting' + match_opt_arg,
				ext = LISTINGS_EXT)
			# -------------------------------
	return dep

def getTexFileDepMatch(dep, line, regex,
		ext = '', extdef = '', dir = '',
		invalid = '.*#\\d+.*|.*\\\\.*', optional = False):
	"""Tries to match a dependency on a tex file line."""
	# find
	m = re.search(regex, line)
	if m is None: return
	f = m.group(1)
	if (f == '' or (
		invalid is not None and
		re.match(invalid, f) is not None)): return
	# add the directory
	if dir != '': f = os.path.join(dir, f)
	# check the extension
	if not isinstance(ext, list):
		ext = [ext]
		if extdef == '': extdef = ext[0]
	# find the files
	fns = [ f + '.' + e for e in ext if e != '' ]
	fns.append(f)
	found = [ nf for nf in fns if os.path.isfile(nf) ]
	# set f to the found file
	if len(found) > 0:
		f = found[0]
	else:
		# try to set the default extension
		if extdef != '':
			f += '.' + extdef
		if optional and not os.path.isfile(f):
			return # nothing has been found
	# add the file
	if f in dep: return
	dep.add(f)
	# recursive?
	if os.path.splitext(f)[1] == '.tex':
		getTexFileDep(f, dep)

def stripLatexLine(line, old_line = ''):
	"""Removes comments and strips a tex line."""
	unfinished = False
	line = line.strip()
	i = line.find('%')
	if i == 0:
		return (old_line, unfinished)
	while i > 0:
		if line[i - 1] != '\\':
			unfinished = (i == len(line) - 1)
			line = line[:i]
			break
		i = line.find('%', i + 1)
	return (old_line + line.strip(), unfinished)

def writeDeps(out, deps, suffix = ''):
	"""Writes the list of dependencies."""
	for d in sorted(deps):
		out.write(' \\\n\t')
		out.write(d)
	out.write(suffix)

def writeDependencies(out, file, deps, outext = 'pdf'):
	"""Write dependencies for a tex file"""
	genfile = file.replace('.tex', '.' + outext)
	if genfile == file: return
	out.write("# Generated for %s\n" % file)
	out.write(genfile + ': ' + file)
	writeDeps(out, deps, suffix = "\n\n")

if __name__ == '__main__':
	"""The main program."""
	out = sys.stdout
	out.write("###########################################\n")
	out.write("# Makefile (LaTeX) generated dependencies #\n")
	out.write("###########################################\n")
	out.write("\n")
	dd = set()
	for file in sys.argv[1:]:
		d = getTexFileDep(file)
		writeDependencies(out, file, d)
		dd |= set(d)
		dd.add(file)
	accept = lambda f: (os.path.splitext(f)[1] in
		['.' + ext for ext in ['bib', 'cls', 'tex']])
	dd = set(filter(accept, dd))
	out.write("# Dependencies of this file\nMakefile.d:")
	out.write(" " + GEN_FROM)
	writeDeps(out, dd, "\n\n")
	out.write("# EOF\n")
