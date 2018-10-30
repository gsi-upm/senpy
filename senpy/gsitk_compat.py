import logging

logger = logging.getLogger(__name__)

MSG = 'GSITK is not (properly) installed.'
IMPORTMSG = '{} Some functions will be unavailable.'.format(MSG)
RUNMSG = '{} Install it to use this function.'.format(MSG)


def raise_exception(*args, **kwargs):
    raise Exception(RUNMSG)


try:
    from gsitk.datasets.datasets import DatasetManager
    from gsitk.evaluation.evaluation import Evaluation as Eval
    from sklearn.pipeline import Pipeline
    import pkg_resources
    GSITK_VERSION = pkg_resources.get_distribution("gsitk").version.split()
    GSITK_AVAILABLE = GSITK_VERSION > (0, 1, 9, 1)  # Earlier versions have a bug
    modules = locals()
except ImportError:
    logger.warning(IMPORTMSG)
    GSITK_AVAILABLE = False
    GSITK_VERSION = ()
    DatasetManager = Eval = Pipeline = raise_exception
