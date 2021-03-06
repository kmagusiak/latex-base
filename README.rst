==================
latex-base package
==================

latex-base eases writing of LaTeX documents by providing a set of templates,
examples and tools to build a PDF automatically.

Most of the time, the user will use a copy of this project for another project
containing a set of documents. Additional templates may later be added back to
this project and updates of this project should not break the compatibility.

Dependencies
============

- pdflatex
- bibtex
- makeglossary
- makeindex
- GNU make
- python (for dependency generation)

Optional dependencies:

- biber
- dia
- docutils
- gnuplot
- graphviz
- inkscape or imagemagick
- latexmk
- pandoc
- plantuml
- plotutils
- pygments
- umlgraph (included)

Description of documents and directories
========================================

LaTeX files and input directory
-------------------------------
- biblio.bib: BibTeX database
- document.tex: an example of a document
  (it contains document-example.tex)
- presentation.tex: a Beamer presentation
  (contains the body, metadata and an example)
- presentation-article.tex: presentation.tex rendered as an article
- simple.tex: a nearly minimal document
- simple-presentation.tex: minimal Beamer presentation
- tikz.tex: a generated image

The directory input contains files that are included by the documents to add
macros, import a set of packages, define the theme, etc. A document should
include an ``input/style/*`` file in the prelude.

Images
------
The directory `img` contains all images manipulated by the project. You can
create sub-directories to classify your files. Also, files that are source of
generated images should be in that directory.

Scripts and generation
----------------------
There is a Makefile for building the project and auxiliary scripts in the script
directory. The `Makefile.files` describes what LaTeX files are source of a
generated document, by default the files are found automatically.
Finally, the file `Makefile.d` that includes automatic dependencies can be
generated, also `Makefile.genfiles` lists all the generated files;
these should not be under revision control.

Basic workflow
==============

Initializing the project
------------------------
The script ``latex-base-clone.py`` can be used to generate and update user's
files in other projects.  The used script is the one located in the *cloned*
directory, not the current one.

- Initializing a new project
  To create a new clone use ``init PATH`` where ``PATH`` is the name of the
  directory to create.
- Updating an existing project
  Go to the destination directory and run the script with ``update``.
- Copying/updating a template
  Go to the destination directory and run the script with ``template``.
  Optionally, add a name of the template to copy/update.

Editing files
-------------
The user selects the type of documents they want to use and make a copy of these
on the root of the project.
Optionally, they register these files explicitely in `Makefile.files` and they
edit the input styles by making a copy of an existing style and changing it.
Then, images should be added to `img`.
It is also good to adopt a naming strategy if more than one resulting file will
be present in the project, such as a common prefix.

Makefile
--------
Use ``make`` to compile the files.
When running, consider using -s option to mask the executed commands.

For a list of targets, run:

.. code:: bash

    make help

If you want the output of LaTeX, run:

.. code:: bash

	make VERBOSE=yes

For a quick build, where ``3`` is the number of concurrent tasks, use:

.. code:: bash

	make -sj3

For debugging purposes, a target debug-* is added for listing values of the
variables:

.. code:: bash

    make debug-DOC debug-DOC_AUTODEP

Useful links and tutorials
==========================

- LaTeX Wikibooks

  http://en.wikibooks.org/wiki/LaTeX

- Andy Robert's tutorial

  http://www.andy-roberts.net/misc/latex/

- List of LaTeX commands

  http://www.emerson.emory.edu/services/latex/latex_toc.html

- Beamer Guide

  http://www.scribd.com/doc/28011/beamer-guide

- The Comprehensive LaTeX Symbol list

  http://www.ctan.org/tex-archive/info/symbols/comprehensive/symbols-a4.pdf

- The Not So Short Introduction to LATEX2e
