#!/usr/bin/env python
# Quick document file dependency generator:
#  - parses LaTeX files
#  - parses markdown

import os.path
import re
import sys

GEN_FROM = 'Makefile.files'
IMG_ROOT_DIR = 'img'
IMG_EXT_NORMAL = ['eps', 'jpg', 'pdf', 'png']
IMG_EXT_DEF = 'pdf'
assert IMG_EXT_DEF in IMG_EXT_NORMAL
MD_EXT = ['md', 'markdown', 'mkdn', 'mdown']

# =========================================================

def getTexFileDep(filename, dep):
	"""Generates dependencies for a tex file."""
	# check the arguments
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
		match_arg_ignore = '\\{.+?\\}'
		match_opt = '(?:\\[[^\\]]*\\])?'
		match_opt_arg = match_opt + match_arg
		for line in latexLines(f):
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
				'\\\\includeimage(?:base|figure)?'
				+ '(?:' + match_opt + ')*' + match_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF,
				dir = IMG_ROOT_DIR)
			# pgfdeclareimage
			getTexFileDepMatch(dep, line,
				'\\\\pgfdeclareimage' + match_opt
					+ match_arg_ignore + match_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF)
			# inputminted
			getTexFileDepMatch(dep, line,
				'\\\\inputminted' + match_arg_ignore + match_arg)
			# lstinputlisting
			getTexFileDepMatch(dep, line,
				'\\\\lstinputlisting' + match_opt_arg)
			# -------------------------------

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
		if extdef != '' and not f.endswith('.' + extdef):
			f += '.' + extdef
		if optional and not os.path.isfile(f):
			return # nothing has been found
	# add the file
	if f in dep: return
	dep.add(f)
	getFileDep(f, dep)

def latexLines(f):
	"""Generator for relevant latex lines (without comments or spaces)."""
	acc = ''
	result = True
	for line in f:
		result = True
		i = line.find('%')
		while i >= 0:
			if i == 0 or line[i - 1] != '\\':
				result = False
				line = line[:i]
				break
			i = line.find('%', i + 1)
		acc += line
		if result:
			yield acc
			acc = ''
	if not result:
		yield acc

# =========================================================

def getMdFileDep(filename, dep):
	"""Generates markdown file dependencies"""
	if os.path.splitext(filename)[1] not in ['.' + ext for ext in MD_EXT]:
		sys.stderr.write("getMdFileDep(%s): works only for markdown files\n"
			% filename)
		return dep
	if not os.path.isfile(filename):
		sys.stderr.write("getMdFileDep(%s): file does not exist\n"
			% filename)
		return dep
	# analyse the lines of the given file
	with open(filename, 'r') as f:
		for line in f:
			# an example of reference: ![some text](url "optional description")
			m = re.search('!\[[^]]+\]\(([^)]+)(?:\s["\'].*["\'])?\)', line)
			if m is None: continue
			ref = m.group(1)
			if ref in dep: continue
			dep.add(ref)
			getFileDep(ref, dep)

# =========================================================

def writeDep(out, dep):
	"""Writes a dependency file"""
	if ' ' in dep:
		sys.stderr.write("File '%s' contains invalid characters\n" % dep)
	out.write(dep)

def writeDeps(out, deps, suffix = ''):
	"""Writes the list of dependencies."""
	for d in sorted(deps):
		out.write(' \\\n\t')
		writeDep(out, d)
	out.write(suffix)

def writeDependencies(out, filename, deps, outext = 'pdf'):
	"""Write dependencies for a file"""
	genfile = os.path.splitext(filename)[0] + '.' + outext
	if genfile == filename:
		sys.stderr.write("No dependencies writen for %s\n" % filename)
		return
	out.write("# Generated for %s\n" % filename)
	writeDep(out, genfile)
	out.write(': ')
	writeDep(out, filename)
	writeDeps(out, deps, suffix = "\n\n")

def getFileDep(filename, dep = None):
	noResult = dep
	if dep is None:
		dep = set()
	if filename.endswith('.tex'):
		getTexFileDep(filename, dep)
	elif os.path.splitext(filename)[1] in ['.' + ext for ext in MD_EXT]:
		getMdFileDep(filename, dep)
	else:
		return noResult
	return dep

# =========================================================

if __name__ == '__main__':
	"""The main program."""
	out = sys.stdout
	out.write("###########################################\n")
	out.write("# Makefile (LaTeX) generated dependencies #\n")
	out.write("###########################################\n")
	out.write("\n")
	dd = set()
	for file in sys.argv[1:]:
		d = getFileDep(file)
		if d is None:
			sys.stderr.write("Unsupported file: %s" % file)
			continue
		writeDependencies(out, file, d)
		dd |= set(d)
		dd.add(file)
	accept = lambda f: (os.path.splitext(f)[1] in
		['.' + ext for ext in ['bib', 'cls', 'tex'] + MD_EXT])
	dd = set(filter(accept, dd))
	out.write("# Dependencies of this file\nMakefile.d:")
	out.write(" " + GEN_FROM)
	writeDeps(out, dd, "\n\n")
	out.write("# EOF\n")