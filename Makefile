######################
## Makefile (LaTeX) ##
######################

all: compile_clean

#########
# Files #
#########

# Variables and commands
DIA=dia
GRAPHVIZ_DOT=dot
LATEXMK=$(shell which latexmk 2> /dev/null)
PLANTUML_JAR=$(SCRIPT_DIR)/plantuml.jar
PYTHON=python
RM=rm -f
SCRIPT_DIR=script
SHELL=/bin/sh
UMLGRAPH_ARG=-private
UMLGRAPH_HOME=$(SCRIPT_DIR)
UMLGRAPH_JAR=$(UMLGRAPH_HOME)/UmlGraph.jar
VERBOSE=no
VIEWER=evince

# For Java
ifeq (x,x$(JAVA_HOME))
	JAVA=java
	JAVADOC=javadoc
else
	JAVA=$(JAVA_HOME)/bin/java
	JAVADOC=$(JAVA_HOME)/bin/javadoc
endif

INTERN_MAKE_DEPGEN=$(SCRIPT_DIR)/latex-depgen.py
INTERN_MAKE_FILES=Makefile.files
INTERN_MAKE_DEPS=Makefile.d

## Include dependencies
#DOC_AUTOFIND=$(shell grep -l -m 1 -E '^\s*\\documentclass' *.tex )
DOC_AUTOFIND=$(shell for f in $$(ls *.tex 2> /dev/null ); do \
	awk '/^\s*\\documentclass/ { print FILENAME } /^\s*($$|%)/ {next} {exit}' \
	"$$f"; done )
DOC=$(DOC_AUTOFIND)
DOC_AUTODEP=$(DOC)
-include $(INTERN_MAKE_FILES)
-include $(INTERN_MAKE_DEPS)

## Derived files
DOCUMENTS=$(DOC:.tex=.pdf)

## Images
IMG_ROOT_DIR=$(shell test -d img && echo img)
IMG_STATIC_EXTENSIONS=eps jpg pdf png
IMG_SRC_EXTENSIONS=dia dot java pic plant svg tex
ifeq (x,x$(IMG_ROOT_DIR))
	IMG_FOUND=
	IMG_SRC=
	IMG_GENERATED=
else
	IMG_FOUND=$(sort $(foreach ext, $(IMG_STATIC_EXTENSIONS), \
		$(shell find $(IMG_ROOT_DIR) -name '*.$(ext)')))
	IMG_SRC=$(sort $(foreach ext, $(IMG_SRC_EXTENSIONS), \
		$(shell find $(IMG_ROOT_DIR) -name '*.$(ext)')))
	IMG_GENERATED=$(sort \
		$(filter %.pdf, $(foreach ext, dia dot java pic plant svg tex, \
		$(patsubst %.$(ext),%.pdf, $(IMG_SRC)))) \
		$(filter %.png, $(foreach ext, sh, \
		$(patsubst %.$(ext),%.png, $(IMG_SRC)))) \
		)
endif
IMG_ALL=$(sort $(IMG_FOUND) $(IMG_GENERATED))
IMG_STATIC=$(filter-out $(IMG_GENERATED), $(IMG_ALL))

############
# Commands #
############

# Removes a file and echoes its name if the file existed
define rm-echo # $1: filename
	test ! -f "$(1)" || (\
		echo Remove: "$(1)"; \
		$(RM) "$(1)"; \
	)
endef
define rm-echo-dir # $1: dirname
	test ! -d "$(1)" || (\
		echo Remove directory: "$(1)"; \
		$(RM) -r "$(1)"; \
	)
endef
# Compiles a tex file into a pdf file
define pdf-latex # $1: tex file
	pdflatex $(PDF_LATEX_FLAGS) -output-directory "$(dir $(1))" \
		"$(1)" $(PDF_LATEX_REDIRECT) || ( \
		$(RM) "$(1:.tex=.pdf)" && false)
endef
# LaTeX recompile rule
define pdf-latex-recompile # $1: tex file
	grep -i -E '(There were undefined references|rerun to get)' \
		"$*.log" $(NULL_OUTPUT)
endef
# Makes the bibliography file ($1: bib file)
pdf-bibtex=bibtex "$(1:.bib=)" $(PDF_LATEX_REDIRECT)
# Makes the index file ($1: idx file)
pdf-makeindex=makeindex "$(1)" $(PDF_LATEX_REDIRECT)
# Makes the glossaries ($1: glo file)
pdf-makeglossaries=makeglossaries "$(1:.glo=)" $(PDF_LATEX_REDIRECT)
# Opens a pdf file ($1: pdf file)
pdf-viewer=$(VIEWER) "$(1)" $(PDF_LATEX_REDIRECT)
# LaTeXmk ($1: tex file)
define pdf-latexmk # $1: tex file
	( cd "$(dir $(1))" && ( \
	$(RM) "$(notdir $(1:.tex=.fdb_latexmk))"; \
	"$(LATEXMK)" $(LATEXMK_FLAGS) \
		-pdf -dvi- -ps- -gg "$(notdir $(1))" $(PDF_LATEX_REDIRECT) || ( \
		$(RM) "$(notdir $(1:.tex=.pdf))" && false) \
	))
endef
define pdf-latexmk-clean # $1: tex file
	"$(LATEXMK)" $(LATEXMK_FLAGS) \
		-output-directory="$(dir $(1))" \
		-c "$(1)" $(NULL_OUTPUT)
endef
# Converts an SVG file into another format ($1: svg file; $2: destination)
ifeq (x,x$(shell which inkscape 2> /dev/null))
	svg-convert=convert "$(1)" "$(2)"
else
	svg-convert=inkscape "--export-$(subst .,,$(suffix $(2)))=$(2)" "$(1)"
endif

## Environment options
NULL_OUTPUT=> /dev/null 2> /dev/null
PDF_LATEX_COMMON_FLAGS=-shell-escape
LATEXMK_COMMON_FLAGS=-r "$(abspath $(SCRIPT_DIR)/latexmkrc)"
ifneq (xno,x$(VERBOSE))
	PDF_LATEX_FLAGS=$(PDF_LATEX_COMMON_FLAGS)
	PDF_LATEX_REDIRECT=
	LATEXMK_FLAGS=$(LATEXMK_COMMON_FLAGS)
else
	PDF_LATEX_FLAGS=$(PDF_LATEX_COMMON_FLAGS) -interaction batchmode
	PDF_LATEX_REDIRECT=$(NULL_OUTPUT) < /dev/null
	LATEXMK_FLAGS=$(LATEXMK_COMMON_FLAGS) -silent
endif
PDF_IMAGE_DENSITY=600

## Colors
COLOR_MSG=0;36m
MSG_BEGIN=echo -e "\033[$(COLOR_MSG)
MSG_END=\033[0m"

################
# Main targets #
################

help:
	@$(MSG_BEGIN)#########################$(MSG_END)
	@$(MSG_BEGIN)# Makefile (LaTeX) help #$(MSG_END)
	@$(MSG_BEGIN)#########################$(MSG_END)
	@echo "all: compiles all and then cleans"
	@echo "clean: cleans after a compilation"
	@echo "clean-all: same as distclean but removes also backup files"
	@echo "compile: compiles the documents and the images"
	@echo "depend: regenerates the Makefile.d"
	@echo "distclean: removes all the generated files"
	@echo "export: exports the pdfs to a directory"
	@echo "help: this message"
	@echo "help-transformations: prints the transformations"
	@echo "list: list all considered files"
	@$(MSG_BEGIN) Type specific rules $(MSG_END)
	@echo "images: compiles the images"
	@echo "images-clean: removes temporary files after compilation"
	@echo "images-distclean: removes compiled images"
	@echo "latex: compiles the documents"
	@echo "latex-clean: removes temporary files after compilation"
	@echo "latex-distclean: removes the compiled documents"
	@$(MSG_BEGIN) Generic rules $(MSG_END)
	@echo "debug-%: shows the value of a variable"
	@echo "%.pdf.view: compiles and opens a pdf file"
	@echo "%.tex.clean: cleans temporary files after compilation"
	@$(MSG_BEGIN) Other $(MSG_END)
	@echo "Use VERBOSE=1 for verbose output"

help-transformations:
	@$(MSG_BEGIN) File transformations $(MSG_END)
	@echo "dia -> {eps,pdf,png} (using dia)"
	@echo "dot -> {eps,pdf,png} (using graphviz)"
	@echo "eps -> pdf (using epspdf)"
	@echo "java -> dot (using UmlGraph)"
	@echo "pdf -> png (using imagemagick)"
	@echo "pic -> svg (using plotutils)"
	@echo "plant -> {png,svg} (using plantuml)"
	@echo "svg -> {eps,pdf,png} (using inkscape or imagemagick)"
	@echo "tex -> pdf (using pdflatex)"

debug-%:
	@echo "$*=$($*)"

depend:
	$(RM) $(INTERN_MAKE_DEPS)
	$(MAKE) FORCE

$(INTERN_MAKE_DEPS): $(INTERN_MAKE_DEPGEN) \
	$(shell test -f "$(INTERN_MAKE_FILES)" && echo "$(INTERN_MAKE_FILES)" )
	@$(MSG_BEGIN) Dependency generation... $(MSG_END)
ifeq (x,x$(DOC_AUTODEP))
	echo "# Empty dependency file" > $@
else
	$(PYTHON) $(INTERN_MAKE_DEPGEN) $(DOC_AUTODEP) > $@
endif

###################
# Compiling LaTeX #
###################

latex: $(DOCUMENTS)

%.pdf.view: %.pdf
	$(call pdf-viewer,$*.pdf)

.tex.pdf:
ifeq (x,x$(LATEXMK))
	@$(MSG_BEGIN) LaTeX compile: $* $(MSG_END)
	$(call pdf-latex,$<)
	test ! -s "$*.aux" \
		|| ! grep -E '\\(cit|bib)' "$*.aux" $(NULL_OUTPUT) \
		|| ($(MAKE) "$*.bbl"; echo "rerun to get the bibliography" >> "$*.log")
	test ! -s "$*.idx" \
		|| ($(MAKE) "$*.ind"; echo "rerun to get the index" >> "$*.log")
	!( test -s "$*.glo" || test -s "$*.acn" ) \
		|| ($(MAKE) "$*.glg"; echo "rerun to get the glossaries" >> "$*.log")
	!($(call pdf-latex-recompile,$<)) || ( \
	   $(MSG_BEGIN) LaTeX recompile: $* $(MSG_END); \
	   $(call pdf-latex,$<); \
   	   !($(call pdf-latex-recompile,$<)) || ( \
	   	   $(MSG_BEGIN) LaTeX recompile: $* $(MSG_END); \
	   	   $(call pdf-latex,$<); \
   	   ) \
	)
else
	@$(MSG_BEGIN) LaTeXmk: $* $(MSG_END)
	$(call pdf-latexmk,$<)
endif

.aux.bbl:
	@$(MSG_BEGIN) BibTeX compile: $* $(MSG_END)
	$(call pdf-bibtex,$<)

.idx.ind:
	@$(MSG_BEGIN) makeindex: $* $(MSG_END)
	$(call pdf-makeindex,$<)

%.glg: %.aux %.glo
	@$(MSG_BEGIN) makeglossaries: $* $(MSG_END)
	$(call pdf-makeglossaries,$*)

%.tex.clean:
ifneq (x,x$(LATEXMK))
	$(call pdf-latexmk-clean,$*.tex)
else
	$(RM) $(foreach e,\
		acn acr alg aux bbl blg fax glg glo gls idx ilg ind ist \
		lof log loh loi lot nav out snm tns toc vrb \
		run.xml *.gnuplot *.table \
		,$*.$(e)) $*-blx.bib
endif

latex-clean: $(DOC:.tex=.tex.clean)
	$(RM) *.aux

latex-distclean: latex-clean
	$(foreach f,$(DOCUMENTS),$(call rm-echo,$(f));)

####################
# Image generation #
####################

images: $(IMG_ALL)

%.eps %.pdf %.png: %.dia
	@$(MSG_BEGIN) Generating $@ from dia $(MSG_END)
	( cd "$(dir $<)" && $(DIA) "--export=$(notdir $@)" "$(notdir $<)" )

%.eps %.pdf %.png: %.dot
	@$(MSG_BEGIN) Generating $@ from dot $(MSG_END)
	( cd "$(dir $<)" && $(GRAPHVIZ_DOT) -T$(subst .,,$(suffix $@)) \
		-o "$(notdir $@)" "$(notdir $<)" )

.eps.pdf:
	@$(MSG_BEGIN) Generating $@ from pdf $< $(MSG_END)
	epspdf "$<" "$@"

.java.dot:
	@$(MSG_BEGIN) Generating $@ from java $(MSG_END)
	$(JAVADOC) -docletpath "$(UMLGRAPH_JAR)" \
		-doclet org.umlgraph.doclet.UmlGraph \
		-output "$@" $(UMLGRAPH_ARG) "$<"

.pdf.png:
	@$(MSG_BEGIN) Generating $@ from pdf $(MSG_END)
	convert -density $(PDF_IMAGE_DENSITY)x$(PDF_IMAGE_DENSITY) "$<" "$@"

%.png %.svg %.txt: %.plant
	@$(MSG_BEGIN) Generating $@ from plant $(MSG_END)
	cat "$<" | $(JAVA) -jar $(PLANTUML_JAR) \
		-t$(subst .,,$(suffix $@)) -pipe > "$@"

%.svg: %.pic
	@$(MSG_BEGIN) Generating $@ from pic $(MSG_END)
	( cd "$(SCRIPT_DIR)" && pic2plot -T$(subst .,,$(suffix $@)) \
		"$(abspath $<)" > "$(abspath $@)" )

%.eps %.pdf %.png: %.svg
	@$(MSG_BEGIN) Generating $@ from svg $(MSG_END)
	$(call svg-convert,$<,$@)

images-clean:
	$(foreach f, $(filter %.tex, $(IMG_SRC)), \
		$(MAKE) "$(f).clean"; )
ifneq (x,x$(IMG_ROOT_DIR))
	find "$(IMG_ROOT_DIR)" -name "*-eps-converted-to.pdf" | xargs $(RM)
endif

images-distclean: images-clean
	$(foreach f,$(IMG_GENERATED),$(call rm-echo,$(f));)

###########
# General #
###########

compile_clean: compile
	@$(MSG_BEGIN) Cleaning... $(MSG_END)
	$(MAKE) clean

compile: images latex
	@$(MSG_BEGIN) All the files has been compiled. $(MSG_END)

clean: images-clean latex-clean

distclean: images-distclean latex-distclean
ifneq (x,x$(EXPORT_DIR))
	$(call rm-echo-dir,"$(EXPORT_DIR)")
endif
	$(RM) $(INTERN_MAKE_DEPS)

clean-all: distclean
	$(RM) *~
ifneq (x,x$(IMG_ROOT_DIR))
	$(RM) $(IMG_ROOT_DIR)/*~
endif

list:
	@echo "# PDF files"
	@$(foreach f, $(DOCUMENTS), echo "$f";)
	@echo "# Generated images"
	@$(foreach f, $(IMG_GENERATED), echo "$f";)
	@echo "# Static images"
	@$(foreach f, $(IMG_STATIC), echo "$f";)

export: compile
ifeq (x,x$(EXPORT_DIR))
	$(error EXPORT_DIR is not defined!)
else
	test -d "$(EXPORT_DIR)" || mkdir -p "$(EXPORT_DIR)"
	$(foreach f,$(DOCUMENTS),cp "$(f)" "$(EXPORT_DIR)/$(notdir $(f))";)
	@$(MSG_BEGIN) Files exported to '$(EXPORT_DIR)' $(MSG_END)
endif

###########################
# Options and conventions #
###########################

FORCE: ; @true
.PHONY: all clean clean-all compile depend distclean export \
	help help-transformations \
	images images-clean images-distclean \
	latex latex-clean latex-distclean \
	list
.SUFFIXES: .aux .bib .bbl .dia .dot \
	.eps .glo .glg .idx .ind .java \
	.pdf .plant .pic .png .svg .tex .txt
