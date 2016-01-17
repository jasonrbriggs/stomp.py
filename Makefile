PYTHON=`which python`
DESTDIR=/
BUILDIR=$(CURDIR)/debian/stomppy
PROJECT=stomp.py
VERSION=3.0.1
PYTHON_VERSION_FULL := $(wordlist 2,4,$(subst ., ,$(shell python --version 2>&1)))
PYTHON_VERSION_MAJOR := $(word 1,${PYTHON_VERSION_FULL})

ifeq ($(PYTHON_VERSION_MAJOR), 3)
travistests: travistests-py3
else
travistests: travistests-py2
endif

all:
	@echo "make source - Create source package"
	@echo "make install - Install on local system"
	@echo "make buildrpm - Generate a rpm package"
	@echo "make builddeb - Generate a deb package"
	@echo "make clean - Get rid of scratch and byte files"

.PHONY: docs

docs:
	cd docs && make html 

source:
	$(PYTHON) setup.py sdist $(COMPILE)

install:
	$(PYTHON) setup.py install --root $(DESTDIR) $(COMPILE)

test: travistests
	$(PYTHON) setup.py test --test=cli_ssl_test,s12_test,stompserver_test,multicast_test,ssl_test,local_test

travistests:
	$(PYTHON) setup.py test --test=basic_test,ss_test,cli_test,s10_test,s11_test,rabbitmq_test,misc_test,transport_test,utils_test
	$(PYTHON) setup.py piptest

travistests-py2:
	$(PYTHON) setup.py test --test=p2_nonascii_test,p2_backward_test
	
travistests-py3:
	$(PYTHON) setup.py test --test=p3_nonascii_test,p3_backward_test

buildrpm:
	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

builddeb:
	# build the source package in the parent directory
	# then rename it to project_version.orig.tar.gz
	$(PYTHON) setup.py sdist $(COMPILE) --dist-dir=../ --prune
	rename -f 's/$(PROJECT)-(.*)\.tar\.gz/$(PROJECT)_$$1\.orig\.tar\.gz/' ../*
	# build the package
	dpkg-buildpackage -i -I -rfakeroot

clean:
	$(PYTHON) setup.py clean
	$(MAKE) -f $(CURDIR)/debian/rules clean
	rm -rf build/ MANIFEST
	find . -name '*.pyc' -delete

