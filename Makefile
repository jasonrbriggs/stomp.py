PYTHON:=`which python`
DESTDIR=/
PROJECT=stomp.py
PYTHON_VERSION_MAJOR:=$(shell $(PYTHON) -c "import sys;print(sys.version_info[0])")
PLATFORM := $(shell uname)

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
	$(PYTHON) setup.py test --test=cli_ssl_test,multicast_test,ssl_test,ssl_sni_test
	#$(PYTHON) setup.py test --test=cli_ssl_test,multicast_test,ssl_test,local_test

travistests:
	$(PYTHON) setup.py test --test=basic_test,nonascii_test,ss_test,cli_test,s10_test,s11_test,s12_test,rabbitmq_test,stompserver_test,misc_test,transport_test,utils_test,multicast_test
	$(PYTHON) setup.py piptest

travistests-py2:
	$(PYTHON) setup.py test --test=p2_backward_test

travistests-py3:
	$(PYTHON) setup.py test --test=p3_backward_test

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
ifeq ($(PLATFORM),Linux)
	$(MAKE) -f $(CURDIR)/debian/rules clean
endif
	$(PYTHON) setup.py clean
	rm -rf build/ MANIFEST dist/
	find . -name '*.pyc' -delete

release:
	$(PYTHON) setup.py clean install sdist bdist_wheel upload

docker-image:
	cd docker; \
	docker build -t stomppy .

run-docker:
	cd docker; \
	docker run -it stomppy