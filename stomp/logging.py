import logging

DEBUG = logging.DEBUG
INFO = logging.INFO

__logger = logging.getLogger("stomp.py")
debug = __logger.debug
info = __logger.info
warning = __logger.warning
error = __logger.error
isEnabledFor = __logger.isEnabledFor
setLevel = __logger.setLevel
