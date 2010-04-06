import os
from distutils.core import setup, Command

import stomp

class TestCommand(Command):
    user_options = [ ('test=', 't', 'specific test to run') ]

    def initialize_options(self):
        self.test = 'basictest'

    def finalize_options(self):
        pass

    def run(self):
        exec('import test.%s' % self.test)

class DoxygenCommand(Command):
    user_options = [ ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('doxygen config.dox')

setup(
    name = 'stomp.py',
    version = "%s.%s" % stomp.__version__,
    description = 'Stomp ',
    license = 'Apache',
    url = 'http://code.google.com/p/stomppy',
    author = 'Jason R Briggs',
    author_email =  'jasonrbriggs@gmail.com',
    platforms = ['any'],
    packages = ['stomp', 'test'],
    cmdclass = { 'test' : TestCommand, 'docs' : DoxygenCommand }
)
