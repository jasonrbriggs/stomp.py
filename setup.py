#!/usr/bin/env python

from distutils.core import Command
from setuptools import setup
import glob
import platform
import io
from logging import config
import os
import shutil
import sys
import unittest


config.fileConfig('stomp.log.conf')

from stomp import logging


with io.open('README.rst', 'rt', encoding='utf8') as f:
    long_description = f.read()


class TestCommand(Command):
    user_options = [('test=', 't', 'specific test to run')]

    def initialize_options(self):
        self.test = '*'

    def finalize_options(self):
        pass

    def run(self):
        cov_files = glob.glob('.coverage*')

        try:
            import coverage
            omitted_files = [
                '*site-packages*'
            ]
            cov = coverage.Coverage(data_file='.coverage.%s' % (len(cov_files)+1), omit=omitted_files)
            cov.start()
        except ImportError:
            cov = None

        suite = unittest.TestSuite()
        import stomp.test
        if self.test == '*':
            logging.info('Running all tests')
            tests = stomp.test.__all__
        else:
            tests = self.test.split(',')
        for tst in tests:
            suite.addTests(unittest.TestLoader().loadTestsFromName('stomp.test.%s' % tst))

        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)

        if cov:
            cov.stop()
            cov.save()


class TestPipInstallCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if platform.python_implementation() == 'PyPy' and sys.version_info.major == 3 and sys.version_info.minor < 3:
            # spurious failure pypy3 <3.2
            return
        if os.path.exists('tmp'):
            shutil.rmtree('tmp')
        os.mkdir('tmp')

        from virtualenvapi.manage import VirtualEnvironment
        env = VirtualEnvironment('tmp/scratch')
        env.install('stomp.py')


class DoxygenCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('doxygen config.dox')


def version():
    import stomp
    s = []
    for num in stomp.__version__:
        s.append(str(num))
    return '.'.join(s)


setup(
    name='stomp.py',
    version=version(),
    description='Python STOMP client, supporting versions 1.0, 1.1 and 1.2 of the protocol',
    long_description=long_description,
    license='Apache',
    url='https://github.com/jasonrbriggs/stomp.py',
    author='Jason R Briggs',
    author_email='jasonrbriggs@gmail.com',
    platforms=['any'],
    install_requires = ['docopt>=0.6.2'],
    packages=['stomp', 'stomp.adapter'],
    cmdclass={'test': TestCommand, 'docs': DoxygenCommand, 'piptest': TestPipInstallCommand},
    entry_points={
        'console_scripts': [
            'stomp = stomp.__main__:main',
        ],
    },
    python_requires='>=3.4',
    classifiers=[
         'Development Status :: 5 - Production/Stable',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: Apache Software License',
         'Programming Language :: Python :: 3'
    ]
)
