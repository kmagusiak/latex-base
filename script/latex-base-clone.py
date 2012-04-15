#!/usr/bin/env python
# Script for merging latex-base directories

import hashlib
import os
import os.path
import re
import shutil
import subprocess
import sys

def prompt(message='Input:', choice=None, default=None):
	""" Prompts a user to enter some text."""
	while True:
		response = raw_input(message + ' ')
		if choice is not None:
			response = response.lower()
			if (len(response) == 0
				and default is not None
				and response not in choice):
				response = default.lower()
			if response in choice:
				return choice[response]
			else:
				print('Invalid response.')
		elif len(response) > 0:
			return response
		elif default is not None:
			return default

def confirm(message='Confirm?', default=None):
	""" The user replies by yes or no. """
	if default is None:
		message += ' [y/n]'
	elif default:
		default = 'y'
		message += ' [Y/n]'
	else:
		default = 'n'
		message += ' [y/N]'
	return prompt(message=message,
		default=default,
		choice={
		'yes': True, 'y': True,
		'no': False, 'n': False})

def get_base_directory():
	""" Gets the root directory where the files are located (BASE) """
	d = os.path.dirname(sys.argv[0])
	d = os.path.join(d, '..')
	d = os.path.normpath(d)
	return d

def hash_file(path):
	""" Returns a hash of a file. """
	with open(path, 'rb') as fp:
		return hashlib.md5(fp.read()).hexdigest()

# ------------------------------------------------------------------------------

class AbortException(Exception):
	""" Used inside this script to signal aborting. """
	def __init__(self, message='Aborted'):
		super(Exception, self).__init__(message)

def dir_update(dest, recursive_src=None, optional=False, ask=False):
	if not os.path.isdir(recursive_src) and optional:
		return
	if not os.path.isdir(dest):
		if ask and not confirm("Copy the directory '%s'?" % recursive_src,
				default=True):
			return
		print('Creating directory: %s' % dest)
		os.mkdir(dest)
	if recursive_src is None:
		return
	for f in os.listdir(recursive_src):
		f_dest = os.path.join(dest, f)
		f_src = os.path.join(recursive_src, f)
		if os.path.isfile(f_src):
			file_update(f_dest, f_src)
		elif os.path.isdir(f_src):
			dir_update(f_dest, f_src)

def file_update(dest, src, only_create=False, optional=False):
	"""
	Updates a single file.
	If only_create is True, nothing happens if the destination file already
	exists.
	"""
	if not os.path.isfile(src):
		if optional: return False
		raise AbortException('Source is not a file: %s' % src)
	if os.path.exists(dest):
		if (only_create
			or os.path.isdir(dest)
			or os.path.getmtime(dest) >= os.path.getmtime(src)
			or hash_file(dest) == hash_file(src)):
			return False
		print("File already exists: %s" % dest)
		if confirm("Show diff?", default=False):
			pdiff = subprocess.Popen(['diff', '-u', dest, src],
				stdout=subprocess.PIPE)
			pless = subprocess.Popen(['less'],
				stdin=pdiff.stdout)
			pdiff.stdout.close() # allow diff to receive SIGPIPE
			pless.wait()
		if not confirm("Overwrite the file?"):
			raise AbortException()
	print('Updating file: %s' % dest)
	destdir = os.path.dirname(dest)
	if not os.path.exists(destdir):
		os.makedirs(destdir)
	shutil.copyfile(src, dest)
	return True

def check_latex_base_directory(path, brep=False):
	""" Checks if path points to a latex-base directory. """
	if path == '':
		path = './'
	if not os.path.isdir(path):
		if brep: return False
		raise AbortException("'%s' is not a directory!" % path)
	if not os.path.exists(os.path.join(path, 'Makefile.files')):
		if brep: return False
		if not confirm(
			"'%s' does not seem to be a latex-base directory, continue?"
			% path):
			raise AbortException()
	if brep: return True

def update_files(dest, src):
	""" Updates the files by copying what is necessary """
	check_latex_base_directory(src)
	# Directories
	for f in ['script']:
		dir_update(os.path.join(dest, f), os.path.join(src, f))
	# Files
	for f in ['Makefile']:
		file_update(os.path.join(dest, f), os.path.join(src, f))
	# dir: input
	f = 'input'
	dir_update(os.path.join(dest, f), os.path.join(src, f),
			optional=True, ask=True)
	# file: Makefile.files
	f = 'Makefile.files'
	file_update(os.path.join(dest, f), os.path.join(src, f),
			only_create=True, optional=True)

def read_make_files(filename, prefix):
	""" Reads files from a Makefile file which are entered as dependencies """
	with open(filename, 'r') as fp:
		return read_make_files_all(fp, prefix)[0]

def read_make_files_all(fp, prefix):
	"""
	Reads files from a Makefile file prefixed by a variable name.
	Returns a tuple with: (files, lines_before, lines_after)
	"""
	reading = 0
	lines_before = []
	lines_after = []
	files = []
	for line in fp:
		if reading == 1:
			pass
		elif line.startswith(prefix):
			line = line[len(prefix):]
			reading = 1
		else:
			if reading == 0:
				lines_before.append(line)
			else:
				lines_after.append(line)
			continue
		line = line.rstrip()
		cont = False
		if line[-1:] == "\\":
			cont = True
			line = line.rstrip("\\")
		fn = ''
		for e in line.split():
			fn += e
			if fn[-1:] == "\\":
				fn = fn[:len(fn) - 1] + ' '
			else:
				files.append(fn)
				fn = ''
		if not cont:
			reading = 2
	return (files, lines_before, lines_after)

def list_templates(directory):
	""" Lists template files declared in Makefile.files """
	p = subprocess.Popen(['make', 'debug-DOC'],
			cwd=directory,
			stdout=subprocess.PIPE)
	p.poll()
	result = p.communicate()[0]
	for line in result.split("\n"):
		if not line.startswith("DOC="): continue
		return re.split('\\s+', line[4:].strip())
	return [] # not found

def update_template(name, dest, src, deps=None):
	""" Updates a template file """
	f_dest = os.path.join(dest, name)
	f_src = os.path.join(src, name)
	print("Creating '%s' from '%s'..." % (f_dest, f_src))
	if not os.path.isfile(f_src):
		raise AbortException('Source is not a file')
	if os.path.exists(f_dest) and not confirm(
		"File already exists, overwrite?"):
		raise AbortException()
	file_update(f_dest, f_src)
	if deps is None:
		deps = confirm("Copy dependencies?", default=True)
	if deps:
		# Make depend
		print('> make depend (cwd: %s)' % src)
		subprocess.check_call(['make', 'depend'], cwd=src)
		print('')
		# Update dependencies
		for d in read_make_files(os.path.join(src, 'Makefile.d'),
			name.replace('.tex', '.pdf') + ':'):
			if d == name: continue
			file_update(os.path.join(dest, d), os.path.join(src, d))

# ------------------------------------------------------------------------------

def command_init(path='', base=get_base_directory()):
	path = os.path.join(os.getcwd(), path)
	exists = os.path.exists(path)
	if (exists and
		not confirm("Directory '%s' already exists, continue?" % path,
			default=False)):
		raise AbortException("'%s' already exists." % path)
	if not exists: os.mkdir(path)
	update_files(path, base)
	print('Done.')

def command_update(base=get_base_directory()):
	path = os.getcwd()
	check_latex_base_directory(path)
	update_files(path, base)
	print('Done.')

def command_template(name='', base=get_base_directory()):
	# (List files and choose one)
	if name == '':
		print('List of files:')
		for t in list_templates(base):
			print('  ' + t)
		print('')
		try:
			name = prompt("Enter a template name:")
		except EOFError:
			name = ''
		if name == '':
			raise AbortException('No name entered')
	# Check
	exists = os.path.isfile(os.path.join(base, name))
	if not exists:
		name += ".tex"
		exists = os.path.isfile(os.path.join(base, name))
	if not exists:
		raise AbortException("Template '%s' does not exist." % name)
	# Copy
	cwd = os.getcwd()
	check_latex_base_directory(cwd)
	update_template(name, cwd, base)
	print('Done.')

if __name__ == '__main__':
	def usage():
		script_name = os.path.basename(sys.argv[0])
		print('Usage: %s init [PATH] [BASE]' % script_name)
		print('       %s update [BASE]' % script_name)
		print('       %s template [NAME] [BASE]' % script_name)
		print('')
		print(' init: creates a new repository PATH from BASE')
		print(' update: updates files in the current folder from BASE')
		print(' template: copies a template file')
		print('')
		print(' BASE=' + get_base_directory())
	if len(sys.argv) < 2:
		usage()
		sys.exit(1)
	command = sys.argv[1]
	if command in ['init', 'update', 'template']:
		command = locals()['command_' + command]
		try:
			command(*sys.argv[2:])
		except TypeError as e:
			print(e)
			sys.exit(1)
		except AbortException as e:
			print('> ' + str(e))
			sys.exit(1)
		except KeyboardInterrupt:
			print(' > Interrupted')
			sys.exit(1)
		else:
			sys.exit(0)
	else:
		print("Command not found '%s'" % command)
		print('')
		usage()
		sys.exit(1)
