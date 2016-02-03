__script__ = "crawtext"
__name__ = "crawtext"

import logging
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(file="quickanddirty.log", format=FORMAT, level=logging.INFO)
logger = logging.getLogger(__name__)


