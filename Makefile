######################
## Makefile (LaTeX) ##
######################

all: compile_clean

#########
# Files #
#########

INTERN_MAKE_DEPGEN=script/latex-depgen.py
INTERN_MAKE_FILES=Makefile.files
INTERN_MAKE_DEPS=Makefile.d

include $(INTERN_MAKE_FILES)
-include $(INTERN_MAKE_DEPS)

## Derived files
DOCUMENTS=$(DOC:.tex=.pdf)

## Images
IMG_ROOT_DIR=img
IMG_DYNAMIC_EXT=png
IMG_FOUND=$(sort $(foreach ext, jpg png, \
	$(shell find $(IMG_ROOT_DIR) -name '*.$(ext)')))
IMG_SRC_EXTENSIONS=dia dot pdf sh svg
IMG_SRC=$(sort $(foreach ext, $(IMG_SRC_EXTENSIONS), \
	$(shell find $(IMG_ROOT_DIR) -name '*.$(ext)')))
IMG_GENERATED=$(sort $(filter %.$(IMG_DYNAMIC_EXT), \
	$(forall ext, $(IMG_SRC_EXTENSIONS), \
	$(patsubst %.$(ext),%.$(IMG_DYNAMIC_EXT), $(IMG_SRC)))))
IMG_ALL=$(sort $(IMG_FOUND) $(IMG_GENERATED))
IMG_STATIC=$(filter-out $(IMG_GENERATED), $(IMG_ALL))

## Project properties
ifeq (x,x$(PROJECT_NAME))
$(error PROJECT_NAME is not defined!)
endif

############
# Commands #
############

SHELL=/bin/sh
PYTHON=python
RM=rm -f

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
	pdflatex $(PDF_LATEX_FLAGS) $(1) $(PDF_LATEX_REDIRECT) || ( \
		$(RM) $(1:.tex=.pdf) && false)
endef
# LaTeX recompile rule
define pdf-latex-recompile # $1: tex file
	grep -E '(There were undefined references|rerun to get)' "$*.log" &> /dev/null
endef
# Makes the bibliography file ($1: bib file)
pdf-bibtex=bibtex $(1:.bib=) $(PDF_LATEX_REDIRECT)
# Makes the index file ($1: idx file)
pdf-makeindex=makeindex $(1) $(PDF_LATEX_REDIRECT)
# Opens a pdf file ($1: pdf file)
pdf-viewer=$(VIEWER) $(1) $(PDF_LATEX_REDIRECT)

## Environment options
VERBOSE=no
PDF_LATEX_COMMON_FLAGS=--shell-escape
ifneq (xno,x$(VERBOSE))
	PDF_LATEX_FLAGS=$(PDF_LATEX_COMMON_FLAGS)
	PDF_LATEX_REDIRECT=
else
	PDF_LATEX_FLAGS=$(PDF_LATEX_COMMON_FLAGS) -interaction batch
	PDF_LATEX_REDIRECT=&> /dev/null < /dev/null
endif
RECOMPILE=yes
VIEWER=evince

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
	@echo "all: compiles the documents and the images then cleans"
	@echo "clean: cleans after a compilation"
	@echo "clean-all: same as distclean but removes also backup files"
	@echo "compile: compiles the documents and the images"
	@echo "depend: regenerates the Makefile.d"
	@echo "distclean: removes all the generated files"
	@echo "export: exports the pdfs to a directory"
	@echo "images: compiles the images"
	@echo "images-clean: removes temporary files after compilation"
	@echo "images-distclean: removes compiled images"
	@echo "latex: compiles the documents"
	@echo "latex-clean: removes temporary files after compilation"
	@echo "latex-distclean: removes the compiled documents"
	@echo "list: list all considered files"
	@echo "%.pdf.view: compiles and opens a pdf file"
	@echo "%.tex.clean: cleans temporary files after compilation"
	@$(MSG_BEGIN) File transformations $(MSG_END)
	@echo "tex -> pdf (using pdflatex)"
	@echo "dia -> $(IMG_DYNAMIC_EXT) (using dia)"
	@echo "dot -> $(IMG_DYNAMIC_EXT) (using graphviz)"
	@echo "svg -> $(IMG_DYNAMIC_EXT) (using inkscape or convert)"
	@$(MSG_BEGIN) Environment variables $(MSG_END)
	@echo "RECOMPILE: whether LaTeX files are recompiled"
	@echo "VERBOSE: when set, latex command prints the output"
	@echo "VIEWER: the viewer for PDF files"

depend:
	$(RM) $(INTERN_MAKE_DEPS)
	$(MAKE) FORCE

$(INTERN_MAKE_DEPS): $(INTERN_MAKE_FILES) $(INTERN_MAKE_DEPGEN)
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
	@$(MSG_BEGIN) LaTeX compile: $* $(MSG_END)
	$(call pdf-latex,$<)
	test ! -f "$*.aux" \
		|| grep -v -E '\\(cit|bib)' "$*.aux" &> /dev/null \
		|| ($(MAKE) "$*.bbl"; echo "rerun to get the bibliography" >> "$*.log")
	test ! -f "$*.idx" \
		|| ($(MAKE) "$*.ind"; echo "rerun to get the index" >> "$*.log")
ifeq (x$(RECOMPILE),xyes)
	! ($(call pdf-latex-recompile,$<)) || ( \
	$(MSG_BEGIN) LaTeX recompile: $* $(MSG_END);\
	$(call pdf-latex,$<); \
	$(call pdf-latex,$<); \
	)
endif

.aux.bbl:
	@$(MSG_BEGIN) BibTeX compile: $* $(MSG_END)
	$(call pdf-bibtex,$<)

.idx.ind:
	@$(MSG_BEGIN) makeindex: $* $(MSG_END)
	$(call pdf-makeindex,$<)

%.tex.clean:
	$(RM) \
		$*.aux $*.bbl $*.blg $*.fax $*.glg $*.glo $*.gls $*.idx \
		$*.ilg $*.ind $*.ist $*.lof $*.log $*.loh $*.loi $*.lot \
		$*.nav $*.out $*.snm $*.tns $*.toc $*.vrb \
		$*.*.gnuplot $*.*.table \
		$*.run.xml $*-blx.bib

latex-clean: $(DOC:.tex=.tex.clean)
	$(RM) *.aux

latex-distclean: latex-clean
	$(foreach f,$(DOCUMENTS),$(call rm-echo,$(f));)

####################
# Image generation #
####################

images: $(IMG_ALL)

.dia.$(IMG_DYNAMIC_EXT):
	@$(MSG_BEGIN) Generating $(IMG_DYNAMIC_EXT) from: $< $(MSG_END)
	( cd $(dir $<) && dia --export=$(notdir $@) $(notdir $<) )

.dot.$(IMG_DYNAMIC_EXT):
	@$(MSG_BEGIN) Generating $(IMG_DYNAMIC_EXT) from: $< $(MSG_END)
	( cd $(dir $<) && dot -T$(IMG_DYNAMIC_EXT) -o $(notdir $@) $(notdir $<) )

.pdf.$(IMG_DYNAMIC_EXT):
	@$(MSG_BEGIN) Generating $(IMG_DYNAMIC_EXT) from: $< $(MSG_END)
	convert -density 600x600 $< $@

.sh.$(IMG_DYNAMIC_EXT):
	@$(MSG_BEGIN) Generating $(IMG_DYNAMIC_EXT) using: $< $(MSG_END)
	( cd $(dir $<) && ./$(notdir $<) $(IMG_DYNAMIC_EXT) > $(notdir $@) )

.svg.$(IMG_DYNAMIC_EXT):
	@$(MSG_BEGIN) Generating $(IMG_DYNAMIC_EXT) from: $< $(MSG_END)
	which inkscape &> /dev/null && ( \
		inkscape --export-$(IMG_DYNAMIC_EXT)=$@ $< \
	) || ( \
		convert $< $@ \
	)

images-clean:

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
	$(RM) *~ $(IMG_ROOT_DIR)/*~

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
	test -d "$(EXPORT_DIR)" || mkdir "$(EXPORT_DIR)"
	$(foreach f,$(DOCUMENTS),cp "$(f)" "$(EXPORT_DIR)/$(notdir $(f))";)
	@$(MSG_BEGIN) Files exported to '$(EXPORT_DIR)' $(MSG_END)
endif

###########################
# Options and conventions #
###########################

FORCE: ; @true
.PHONY: all clean clean-all compile depend distclean export \
	images images-clean images-distclean \
	latex latex-clean latex-distclean \
	list
.SUFFIXES: .aux .bib .bbl .dia .dot .idx .ind .pdf .png .svg .tex
