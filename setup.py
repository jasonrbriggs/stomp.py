#!/usr/bin/env python

from distutils.core import Command
from setuptools import setup
import logging.config
import os
import shutil
import sys
import unittest

try:
    logging.config.fileConfig('stomp.log.conf')
except:
    pass

# Import this after configuring logging
import stomp


class TestCommand(Command):
    user_options = [('test=', 't', 'specific test to run')]

    def initialize_options(self):
        self.test = '*'

    def finalize_options(self):
        pass

    def run(self):
        try:
            import coverage
            cov = coverage.coverage()
            cov.start()
        except ImportError:
            cov = None

        suite = unittest.TestSuite()
        if self.test == '*':
            print('Running all tests')
            tests = stomp.test.__all__
        else:
            tests = self.test.split(',')        
        import stomp.test
        for tst in tests:
            suite.addTests(unittest.TestLoader().loadTestsFromName('stomp.test.%s' % tst))

        runner = unittest.TextTestRunner(verbosity=2)
        res = runner.run(suite)
        if len(res.errors) > 0 or len(res.failures) > 0:
            sys.exit(1)

        if cov:
            cov.stop()
            cov.save()
            cov.html_report(directory='../stomppy-docs/htmlcov')


class TestPipInstallCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
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
    s = []
    for num in stomp.__version__:
        s.append(str(num))
    return '.'.join(s)


setup(
    name='stomp.py',
    version=version(),
    description='Python STOMP client, supporting versions 1.0, 1.1 and 1.2 of the protocol',
    license='Apache',
    url='https://github.com/jasonrbriggs/stomp.py',
    author='Jason R Briggs',
    author_email='jasonrbriggs@gmail.com',
    platforms=['any'],
    packages=['stomp', 'stomp.adapter'],
    cmdclass={'test': TestCommand, 'docs': DoxygenCommand, 'piptest': TestPipInstallCommand},
    scripts=['./scripts/stomp'],
    classifiers=[
         'Development Status :: 5 - Production/Stable',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: Apache Software License',
         'Programming Language :: Python :: 2',
         'Programming Language :: Python :: 3'
    ]
)
