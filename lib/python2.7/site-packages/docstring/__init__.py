"""
A module that enables generating HTML documentation out of docstrings.
Currently it is used for annotating django/tornado api endpoints.
"""
__title__ = 'docstring'
__version__ = '0.1.2.4'
__build__ = 0x001401
__author__ = 'Eytan Daniyalzade'
__license__ = 'ISC'

from utils import Endpoint
from utils import get_api_doc
