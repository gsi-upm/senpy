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

    from gsitk.datasets.datasets import DatasetManager
    from gsitk.evaluation.evaluation import Evaluation as Eval  # noqa: F401
    from gsitk.evaluation.evaluation import EvalPipeline  # noqa: F401
    from sklearn.pipeline import Pipeline
    modules = locals()
    GSITK_AVAILABLE = True
except (DistributionNotFound, ImportError) as err:
    logger.debug('Error importing GSITK: {}'.format(err))
    logger.warning(IMPORTMSG)
    GSITK_AVAILABLE = False
    GSITK_VERSION = ()
    DatasetManager = Eval = Pipeline = raise_exception
