import logging

DEBUG = logging.DEBUG
INFO = logging.INFO

verbose = False

__logger = logging.getLogger("stomp.py")
debug = __logger.debug
info = __logger.info
warning = __logger.warning
error = __logger.error
isEnabledFor = __logger.isEnabledFor
setLevel = __logger.setLevel


def log_to_stdout(verbose_logging=True):
    import sys
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    __logger.addHandler(handler)
    __logger.setLevel(logging.DEBUG)
    global verbose
    verbose = verbose_logging