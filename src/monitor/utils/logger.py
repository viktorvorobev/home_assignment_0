import logging
import sys

logging.basicConfig(stream=sys.stdout,
                    format='[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)',
                    level=logging.INFO)

logger = logging.getLogger()
