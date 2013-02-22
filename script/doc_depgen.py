#!/usr/bin/env python
"""
Quick document file dependency generator:

- parses LaTeX files
- parses markdown
"""

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

def find_tex_dependencies(filename, dep):
	"""Generates dependencies for a tex file."""
	# check the arguments
	if os.path.splitext(filename)[1] != '.tex':
		sys.stderr.write("find_tex_dependencies(%s): works only for tex files\n"
			% filename)
		return dep
	if not os.path.isfile(filename):
		sys.stderr.write("find_tex_dependencies(%s): file does not exist\n"
			% filename)
		return dep
	# analyse the lines of the given file
	with open(filename, 'r') as f:
		match_arg = '\\{(.+?)\\}'
		match_arg_ignore = '\\{.+?\\}'
		match_opt = '(?:\\[[^\\]]*\\])?'
		match_opt_arg = match_opt + match_arg
		for line in latex_lines(f):
			if line == '': continue
			# -------------------------------
			# document class
			match_tex_dependency(dep, line,
				'\\\\documentclass' + match_opt_arg, ext = 'cls',
				optional = True)
			# style files
			match_tex_dependency(dep, line,
				'\\\\usepackage'+match_opt_arg, ext = 'sty',
				optional = True)
			# include | input
			match_tex_dependency(dep, line,
				'\\\\(?:input|include)' + match_arg, ext = 'tex')
			# bibliography
			match_tex_dependency(dep, line,
				'\\\\bibliography' + match_arg, ext = 'bib')
			# includegraphics
			match_tex_dependency(dep, line,
				'\\\\includegraphics' + match_opt_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF)
			# includeimage | includeimagefigure
			match_tex_dependency(dep, line,
				'\\\\includeimage(?:base|figure)?'
				+ '(?:' + match_opt + ')*' + match_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF,
				directory = IMG_ROOT_DIR)
			# pgfdeclareimage
			match_tex_dependency(dep, line,
				'\\\\pgfdeclareimage' + match_opt
					+ match_arg_ignore + match_arg,
				ext = IMG_EXT_NORMAL, extdef = IMG_EXT_DEF)
			# inputminted
			match_tex_dependency(dep, line,
				'\\\\inputminted' + match_arg_ignore + match_arg)
			# lstinputlisting
			match_tex_dependency(dep, line,
				'\\\\lstinputlisting' + match_opt_arg)
			# -------------------------------

def match_tex_dependency(dep, line, regex,
		ext = '', extdef = '', directory = '',
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
	if directory != '': f = os.path.join(directory, f)
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
	find_dependencies(f, dep)

def latex_lines(f):
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

def find_md_dependencies(filename, dep):
	"""Generates markdown file dependencies"""
	if os.path.splitext(filename)[1] not in ['.' + ext for ext in MD_EXT]:
		sys.stderr.write("find_md_dependencies(%s): works only for markdown files\n"
			% filename)
		return dep
	if not os.path.isfile(filename):
		sys.stderr.write("find_md_dependencies(%s): file does not exist\n"
			% filename)
		return dep
	# analyse the lines of the given file
	with open(filename, 'r') as f:
		for line in f:
			# an example of reference: ![some text](url "optional description")
			m = re.search(r'!\[[^]]+\]\(([^)]+)(?:\s["\'].*["\'])?\)', line)
			if m is None: continue
			url = m.group(1)
			if url in dep or url.find('://') >= 0: continue
			dep.add(url)
			find_dependencies(url, dep)

# =========================================================

def write_dep(out, dep):
	"""Writes a dependency file"""
	if ' ' in dep:
		sys.stderr.write("File '%s' contains invalid characters\n" % dep)
	out.write(dep)

def write_deps(out, deps, suffix = ''):
	"""Writes the list of dependencies."""
	for dep in sorted(deps):
		out.write(' \\\n\t')
		write_dep(out, dep)
	out.write(suffix)

def write_dependencies(out, filename, deps, outext = 'pdf'):
	"""Write dependencies for a file"""
	genfile = os.path.splitext(filename)[0] + '.' + outext
	if genfile == filename:
		sys.stderr.write("No dependencies writen for %s\n" % filename)
		return
	out.write("# Generated for %s\n" % filename)
	write_dep(out, genfile)
	out.write(': ')
	write_dep(out, filename)
	write_deps(out, deps, suffix = "\n\n")

def find_dependencies(filename, dep = None):
	"""Gets the dependencies for a file"""
	no_result = dep
	if dep is None:
		dep = set()
	if filename.endswith('.tex'):
		find_tex_dependencies(filename, dep)
	elif os.path.splitext(filename)[1] in ['.' + ext for ext in MD_EXT]:
		find_md_dependencies(filename, dep)
	else:
		return no_result
	return dep

# =========================================================

def main():
	"""The main program."""
	out = sys.stdout
	out.write("###########################################\n")
	out.write("# Makefile (LaTeX) generated dependencies #\n")
	out.write("###########################################\n")
	out.write("\n")
	alldeps = set()
	for path in sys.argv[1:]:
		dep = find_dependencies(path)
		if dep is None:
			sys.stderr.write("Unsupported file: %s" % path)
			continue
		write_dependencies(out, path, dep)
		alldeps |= set(dep)
		alldeps.add(path)
	accept = lambda f: (os.path.splitext(f)[1] in
		['.' + ext for ext in ['bib', 'cls', 'tex'] + MD_EXT])
	alldeps = set(i for i in alldeps if accept(i))
	out.write("# Dependencies of this file\nMakefile.d:")
	out.write(" " + GEN_FROM)
	write_deps(out, alldeps, "\n\n")
	out.write("# EOF\n")

if __name__ == '__main__':
	main()
