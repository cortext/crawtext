import os, sys
CRAWTEXT_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
from emails import validate_email
from links import validate_url
from tldextract import tldextract

from utils import FileHelper
