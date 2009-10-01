from distutils.core import setup, Command
import stomp

class TestCommand(Command):
    user_options = [ ('test=', 't', 'specific test to run') ]

    def initialize_options(self):
        self.test = 'basic'

    def finalize_options(self):
        pass

    def run(self):
        exec('import test.%s' % self.test)

setup(
    name = 'stomp.py',
    version = stomp.__version__,
    description = 'Stomp ',
    license = 'Apache',
    url = 'http://www.briggs.net.nz/log/projects/stomp.py',
    author = 'Jason R Briggs',
    author_email =  'jasonrbriggs@gmail.com',
    platforms = ['any'],
    packages = ['test','stomp'],
    cmdclass = { 'test' : TestCommand }
)
