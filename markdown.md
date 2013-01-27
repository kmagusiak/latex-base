% MarkDown example

What is MarkDown
================

The websites
------------

A simple markup language for writing documents.
The [official website](http://daringfireball.net/projects/markdown) contains
the syntax description and all standard features.

Pandoc
------

This document will be compiled using
[pandoc](http://johnmacfarlane.net/pandoc).
It offers some extensions to the basic language:

- title block
- delimited code block (with highlighting)
- definition lists
- tables
- math support (see LaTeX)

Also, *markdown* is not the only language supported by *pandoc*.

The Makefile
------------

The provided `Makefile` uses a python script that can concatenate documents.
When an image in *markdown* is encountered with an extension of a *markdown*
document, the other file is read an embedded in the root file.
Arguments can also be passed to `make` to add a table of contents or other
features (see the *pandoc* manual).

The example
===========

Ease writing of documents with *MarkDown*. You can put images, add code and
many more...

![The logo](img/logo.png)

Here is a code sample:

	Hello world

