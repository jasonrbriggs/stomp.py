import os
from distutils.core import setup, Command

import unittest

import logging.config
try:
    logging.config.fileConfig('stomp.log.conf')
except:
    pass

import stomp


class TestCommand(Command):
    user_options = [ ('test=', 't', 'specific test to run') ]

    def initialize_options(self):
        self.test = '*'

    def finalize_options(self):
        pass

    def run(self):
        suite = unittest.TestSuite()
        if self.test == '*':
            print('Running all tests')
            import stomp.test
            for tst in stomp.test.__all__:
                suite.addTests(unittest.TestLoader().loadTestsFromName('stomp.test.%s' % tst))
        else:
            suite = unittest.TestLoader().loadTestsFromName('stomp.test.%s' % self.test)
        unittest.TextTestRunner(verbosity=2).run(suite)


class DoxygenCommand(Command):
    user_options = [ ]

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
    name = 'stomp.py',
    version = version(),
    description = 'Python STOMP client, supporting versions 1.0 and 1.1 of the protocol',
    license = 'Apache',
    url = 'https://github.com/jasonrbriggs/stomp.py',
    author = 'Jason R Briggs',
    author_email = 'jasonrbriggs@gmail.com',
    platforms = ['any'],
    packages = ['stomp', 'stomp.adapter'],
    cmdclass = { 'test' : TestCommand, 'docs' : DoxygenCommand },
    scripts = ['./scripts/stomp'],
    classifiers = [
         'Development Status :: 5 - Production/Stable',
         'Intended Audience :: Developers',
         'License :: OSI Approved :: Apache Software License',
         'Programming Language :: Python :: 2',
         'Programming Language :: Python :: 3'
         ]
)
