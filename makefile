IDENT := tellmewhen
IDENTC := $(IDENT)c
IDENTD := $(IDENT)d
INSTALL_PROGRAM := install
INSTALL_DATA := install -m 644

prefix := /usr/local
datarootdir := $(prefix)/share
exec_prefix := $(prefix)
datadir := $(datarootdir)/$(IDENT)
bindir := $(exec_prefix)/bin
docdir := $(datarootdir)/doc/$(IDENT)
python_lib := $(shell ./get_python_lib "$(DESTDIR)$(prefix)")

.PHONY: all clean distclean install uninstall

all:
	./setup build

clean:
	$(RM) -r build

distclean: clean
	@ ./configure reverse
	find tellmewhen -type d -name '__pycache__' | xargs $(RM) -r

install:
	@ # executable
	./set_prefix "$(prefix)"
	mkdir -p "$(DESTDIR)$(bindir)"
	$(INSTALL_PROGRAM) "$(IDENTC)" "$(DESTDIR)$(bindir)/$(IDENTC)"
	$(INSTALL_PROGRAM) ".$(IDENTD).tmp" "$(DESTDIR)$(bindir)/$(IDENTD)"
	$(RM) ".$(IDENTD).tmp"
	@ # package
	./setup install --prefix="$(DESTDIR)$(prefix)"
	@ # readme
	mkdir -p "$(DESTDIR)$(docdir)/"
	$(INSTALL_DATA) README "$(DESTDIR)$(docdir)/"
	$(INSTALL_DATA) config.sample.json "$(DESTDIR)$(docdir)/"

uninstall:
	@ # executable
	$(RM) "$(DESTDIR)$(bindir)/$(IDENTC)" "$(DESTDIR)$(bindir)/$(IDENTD)"
	$(RM) -r "$(DESTDIR)$(datadir)"
	@ # package
	$(RM) -r "$(python_lib)/$(IDENT)" "$(python_lib)/$(IDENT)"-*.egg-info
	@ # readme
	$(RM) -r "$(DESTDIR)$(docdir)/"
