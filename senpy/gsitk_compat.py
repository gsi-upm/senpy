import logging

from pkg_resources import parse_version, get_distribution, DistributionNotFound

logger = logging.getLogger(__name__)

MSG = 'GSITK is not (properly) installed.'
IMPORTMSG = '{} Some functions will be unavailable.'.format(MSG)
RUNMSG = '{} Install it to use this function.'.format(MSG)


def raise_exception(*args, **kwargs):
    raise Exception(RUNMSG)


try:
    gsitk_distro = get_distribution("gsitk")
    GSITK_VERSION = parse_version(gsitk_distro.version)
    GSITK_AVAILABLE = GSITK_VERSION > parse_version("0.1.9.1")  # Earlier versions have a bug
except DistributionNotFound:
    GSITK_AVAILABLE = False
    GSITK_VERSION = ()

if GSITK_AVAILABLE:
    from gsitk.datasets.datasets import DatasetManager
    from gsitk.evaluation.evaluation import Evaluation as Eval
    from sklearn.pipeline import Pipeline
    modules = locals()
else:
    logger.warning(IMPORTMSG)
    DatasetManager = Eval = Pipeline = raise_exception
