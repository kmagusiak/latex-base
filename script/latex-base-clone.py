#!/usr/bin/env python
# Script for merging latex-base directories

import os
import os.path
import shutil
import subprocess
import sys

def multi_call(n, f, arg):
	"""
	Calls a function several times and returns f(f(...f(arg))) where f is
	applied n times.
	"""
	while n > 0:
		arg = f(arg)
		n -= 1
	return arg

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
	return multi_call(2, os.path.dirname, sys.argv[0])

# ------------------------------------------------------------------------------

class AbortException(Exception):
	""" Used inside this script to signal aborting. """
	def __init__(self, message='Aborted'):
		super(Exception, self).__init__(message)

def dir_update(dest, recursive_src=None):
	if os.path.isdir(dest):
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

def file_update(dest, src, only_create=False):
	"""
	Updates a single file.
	If only_create is True, nothing happens if the destination file already
	exists.
	"""
	if not os.path.exists(src):
		raise AbortException('Source does not exist: %s' % src)
	if os.path.exists(dest):
		if only_create or os.path.getctime(dest) >= os.path.getctime(src):
			return
		print("File already exists: %s" % dest)
		if confirm("Show diff?", default=False):
			pdiff = subprocess.Popen(['diff', '-u', src, dest],
				stdout=subprocess.PIPE)
			pless = subprocess.Popen(['less'],
				stdin=pdiff.stdout)
			pless.wait()
		if not confirm("Overwrite the file?"):
			raise AbortException()
	print('Updating file: %s' % dest)
	shutil.copyfile(src, dest)

def update_files(dest, src):
	""" Updates the files by copying what is necessary """
	# Create directories
	for dirname in ['img']:
		dir_update(os.path.join(dest, dirname))
	# Update directories
	for nextdir in ['input', 'script']:
		dir_update(os.path.join(dest, nextdir), os.path.join(src, nextdir))
	# Update files
	for f in ['Makefile']:
		file_update(os.path.join(dest, f), os.path.join(src, f))
	# file: Makefile.files
	def mkfs_replace(f):
		with open(f, 'r+') as fp:
			lines = []
			rem = False
			for l in fp:
				if rem:
					if l.startswith("\t"): continue
					rem = False
				elif l.startswith("DOC="):
					rem = True
					l = "DOC=\n"
				lines.append(l)
			fp.seek(0)
			fp.write("".join(lines))
			fp.truncate()
	f = 'Makefile.files'
	dest_f = os.path.join(dest, f)
	file_update(dest_f, os.path.join(src, f),
		only_create=True)
	mkfs_replace(dest_f)

def read_make_files(filename, prefix):
	""" Reads files from a Makefile file which are entered as dependencies """
	reading = False
	files = []
	with open(filename, 'r') as fp:
		for line in fp:
			if reading:
				pass
			elif line.startswith(prefix):
				line = line[len(prefix):]
				reading = True
			else:
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
			if not cont: break
	return files

def list_templates(directory):
	""" Lists template files declared in Makefile.files """
	return read_make_files(os.path.join(directory, 'Makefile.files'), "DOC=")

def update_template(name, dest, src, deps=None):
	""" Updates a template file """
	f_dest = os.path.join(dest, name)
	f_src = os.path.join(src, name)
	print("Create '%s' from '%s'..." % (f_dest, f_src))
	if not os.path.isfile(f_src):
		raise AbortException('Source is not a file')
	if os.path.exists(f_dest) and not confirm(
		"File already exists, overwrite?"):
		raise AbortException()
	file_update(f_dest, f_src)
	if deps is None:
		deps = confirm("Copy dependencies?", default=True)
	if not deps: return
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

def command_init(path, base=get_base_directory()):
	path = os.path.join(os.getcwd(), path)
	if os.path.exists(path):
		raise AbortException("'%s' already exists." % path)
	os.mkdir(path)
	update_files(path, base)
	print('Done.')

def command_update(base=get_base_directory()):
	path = os.getcwd()
	if not os.path.isdir(path):
		raise AbortException("'%s' is not a directory!" % path)
	if (not os.path.exists(os.path.join(path, 'Makefile.files'))
		and not confirm(
		"'%s' does not seems to be a latex-base directory, continue?" % path)):
		raise AbortException()
	update_files(path, base)
	print('Done.')

def command_template(name='', base=get_base_directory()):
	# (List files and choose one)
	if name == '':
		print('List of files:')
		for t in list_templates(base):
			print('  ' + t)
		print('')
		name = prompt("Enter a template name:")
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
	update_template(name, cwd, base)
	print('Done.')

if __name__ == '__main__':
	def usage():
		script_name = os.path.basename(sys.argv[0])
		print('Usage: %s init PATH [BASE]' % script_name)
		print('       %s update [BASE]' % script_name)
		print('       %s template [NAME] [BASE]' % script_name)
		print('')
		print(' init: creates a new repository PATH from BASE')
		print(' update: updates files in the current folder from BASE')
		print(' template: copies a template file')
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
