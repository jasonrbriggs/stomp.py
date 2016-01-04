import sys

__all__ = ['basic_test', 'ss_test', 'cli_test', 'cli_ssl_test', 's10_test',
           's11_test', 's12_test', 'rabbitmq_test', 'stompserver_test',
           'misc_test', 'multicast_test', 'ssl_test', 'utils_test',
           'transport_test', 'local_test']

if sys.hexversion >= 0x03000000:
    __all__.append('p3_nonascii_test')
    __all__.append('p3_backward_test')
else:
    __all__.append('p2_nonascii_test')
    __all__.append('p2_backward_test')
