import logging
import sys
from config import settings

log_level = {
	"debug": logging.DEBUG,
	"info": logging.INFO,
	"warning": logging.WARNING,
	"error": logging.ERROR
}

logger = logging.getLogger(__name__)
logger.setLevel(log_level[settings.log_level])

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
	'%(asctime)s - %(name)s - %(levelname)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)