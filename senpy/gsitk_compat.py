#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import logging
import os

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

    if not os.environ.get('DATA_PATH'):
        os.environ['DATA_PATH'] = os.environ.get('SENPY_DATA', 'senpy_data')

    from gsitk.datasets.datasets import DatasetManager
    from gsitk.evaluation.evaluation import Evaluation as Eval  # noqa: F401
    from gsitk.evaluation.evaluation import EvalPipeline  # noqa: F401
    from sklearn.pipeline import Pipeline
    modules = locals()
    GSITK_AVAILABLE = True
    datasets = {}
    manager = DatasetManager()

    for item in manager.get_datasets():
        for key in item:
            if key in datasets:
                continue
            properties = item[key]
            properties['@id'] = key
            datasets[key] = properties

    def prepare(ds, *args, **kwargs):
        return manager.prepare_datasets(ds, *args, **kwargs)


except (DistributionNotFound, ImportError) as err:
    logger.debug('Error importing GSITK: {}'.format(err))
    logger.warning(IMPORTMSG)
    GSITK_AVAILABLE = False
    GSITK_VERSION = ()
    DatasetManager = Eval = Pipeline = prepare = raise_exception
    datasets = {}
