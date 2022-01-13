import logging

def make_console_logger(level="info") -> logging.Logger:
    """Return a custom logger."""
    logger = logging.getLogger(__package__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(logging.BASIC_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level.upper())
    return logger

logger = make_console_logger(level="debug")

# from distutils.version import LooseVersion

VERSION = "0.1.0"
GIT_VERSION = "undefined"
# import subprocess
# if subprocess.call(
#             ['git', '-C', path, 'status'],
#             stderr=subprocess.STDOUT,
#             stdout=open(os.devnull, 'w')
#         ) == 0:
#     GIT_VERSION = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).strip()