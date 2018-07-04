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
    GSITK_AVAILABLE = True
    modules = locals()
except ImportError:
    logger.warn(IMPORTMSG)
    GSITK_AVAILABLE = False
    DatasetManager = Eval = Pipeline = raise_exception
