######################
## Makefile (LaTeX) ##
######################

all: compile_clean

#########
# Files #
#########

SCRIPT_DIR=script
INTERN_MAKE_DEPGEN=$(SCRIPT_DIR)/latex-depgen.py
INTERN_MAKE_FILES=Makefile.files
INTERN_MAKE_DEPS=Makefile.d

include $(INTERN_MAKE_FILES)
-include $(INTERN_MAKE_DEPS)

## Derived files
DOCUMENTS=$(DOC:.tex=.pdf)

## Images
IMG_ROOT_DIR=img
IMG_STATIC_EXTENSIONS=eps jpg pdf png
IMG_FOUND=$(sort $(foreach ext, $(IMG_STATIC_EXTENSIONS), \
	$(shell find $(IMG_ROOT_DIR) -name '*.$(ext)')))
IMG_SRC_EXTENSIONS=dia dot java sh svg tex
IMG_SRC=$(sort $(foreach ext, $(IMG_SRC_EXTENSIONS), \
	$(shell find $(IMG_ROOT_DIR) -name '*.$(ext)')))
IMG_GENERATED=$(sort \
	$(filter %.pdf, $(foreach ext, dia dot java svg tex, \
	$(patsubst %.$(ext),%.pdf, $(IMG_SRC)))) \
	$(filter %.png, $(foreach ext, sh, \
	$(patsubst %.$(ext),%.png, $(IMG_SRC)))) \
	)
IMG_ALL=$(sort $(IMG_FOUND) $(IMG_GENERATED))
IMG_STATIC=$(filter-out $(IMG_GENERATED), $(IMG_ALL))

## Project properties
ifeq (x,x$(PROJECT_NAME))
$(error PROJECT_NAME is not defined!)
endif

############
# Commands #
############

# Variables and commands
PYTHON=python
RM=rm -f
SHELL=/bin/bash
UMLGRAPH_ARG=-private
UMLGRAPH_HOME=$(SCRIPT_DIR)
UMLGRAPH_JAR=$(UMLGRAPH_HOME)/UmlGraph.jar
VERBOSE=no
VIEWER=evince

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
		$(RM) $(1:.tex=.pdf) && false)
endef
# LaTeX recompile rule
define pdf-latex-recompile # $1: tex file
	grep -E '(There were undefined references|rerun to get)' \
		"$*.log" &> /dev/null
endef
# Makes the bibliography file ($1: bib file)
pdf-bibtex=bibtex $(1:.bib=) $(PDF_LATEX_REDIRECT)
# Makes the index file ($1: idx file)
pdf-makeindex=makeindex $(1) $(PDF_LATEX_REDIRECT)
# Opens a pdf file ($1: pdf file)
pdf-viewer=$(VIEWER) $(1) $(PDF_LATEX_REDIRECT)

## Environment options
PDF_LATEX_COMMON_FLAGS=--shell-escape
ifneq (xno,x$(VERBOSE))
	PDF_LATEX_FLAGS=$(PDF_LATEX_COMMON_FLAGS)
	PDF_LATEX_REDIRECT=
else
	PDF_LATEX_FLAGS=$(PDF_LATEX_COMMON_FLAGS) -interaction batch
	PDF_LATEX_REDIRECT=&> /dev/null < /dev/null
endif
RECOMPILE=yes

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
	@echo "dia -> {eps,pdf,png} (using dia)"
	@echo "dot -> {eps,pdf,png} (using graphviz)"
	@echo "eps -> pdf (using epspdf)"
	@echo "java -> dot (using UmlGraph)"
	@echo "pdf -> png (using imagemagick)"
	@echo "pic -> svg (using plotutils)"
	@echo "sh -> png (execute with extension argument and pipe the output)"
	@echo "svg -> {eps,pdf,png} (using inkscape or imagemagick)"
	@echo "tex -> pdf (using pdflatex)"
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
		|| ! grep -E '\\(cit|bib)' "$*.aux" &> /dev/null \
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

%.eps %.pdf %.png: %.dia
	@$(MSG_BEGIN) Generating $@ from dia $(MSG_END)
	( cd $(dir $<) && dia --export=$(notdir $@) $(notdir $<) )

%.eps %.pdf %.png: %.dot
	@$(MSG_BEGIN) Generating $@ from dot $(MSG_END)
	( cd $(dir $<) && dot -T$(subst .,,$(suffix $@)) \
		-o $(notdir $@) $(notdir $<) )

.eps.pdf:
	@$(MSG_BEGIN) Generating $@ from pdf $< $(MSG_END)
	epspdf $< $@

.java.dot:
	@$(MSG_BEGIN) Generating $@ from java $(MSG_END)
	javadoc -docletpath "$(UMLGRAPH_JAR)" \
		-doclet org.umlgraph.doclet.UmlGraph \
		-output "$@" $(UMLGRAPH_ARG) "$<"

.pdf.png:
	@$(MSG_BEGIN) Generating $@ from pdf $(MSG_END)
	convert -density 600x600 $< $@

%.svg: %.pic
	@$(MSG_BEGIN) Generating $@ from pic $(MSG_END)
	( cd $(SCRIPT_DIR) && pic2plot -T$(subst .,,$(suffix $@)) \
		"$(abspath $<)" > "$(abspath $@)" )

.sh.png:
	@$(MSG_BEGIN) Generating $@ from sh $(MSG_END)
	( cd $(dir $<) && ./$(notdir $<) png > $(notdir $@) )

%.eps %.pdf %.png: %.svg
	@$(MSG_BEGIN) Generating $@ from svg $(MSG_END)
	which inkscape &> /dev/null && ( \
		inkscape --export-$(subst .,,$(suffix $@))=$@ $< \
	) || ( \
		convert $< $@ \
	)

images-clean:
	$(foreach f, $(filter %.tex, $(IMG_SRC)), \
		$(MAKE) $(f).clean; )
	find "$(IMG_ROOT_DIR)" -name "*-eps-converted-to.pdf" | xargs $(RM)

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
.SUFFIXES: .aux .bib .bbl .dia .dot \
	.eps .idx .ind .java \
	.pdf .pic .png .svg .tex
