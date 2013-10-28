import os
import sys
sys.path.insert(0, os.path.split(__file__)[0])

__all__ = [ 'basic_test', 'ss_test', 'cli_test', 's10_test', 's11_test', 's12_test', 'rabbitmq_test', 'stompserver_test', 'misc_test' ]

if sys.hexversion >= 0x03000000:
    __all__.append('p3_nonascii_test')
else:
    __all__.append('p2_nonascii_test')