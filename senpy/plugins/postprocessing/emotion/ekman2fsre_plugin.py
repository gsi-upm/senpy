from typing import *
from senpy.ns import emoml
from senpy.plugins.postprocessing.emotion.centroids import CentroidConversion


class Ekman2FSRE(CentroidConversion):
    ''' Plugin to convert emotion sets from Ekman to VAD '''
    version: str = '0.2'
    # No need to specify doesConversion because centroids.py adds it automatically from centroids_direction
    neutralValue: float = 5.0
    centroids: Dict = {
            'anger': {
                'A': 6.95,
                'D': 5.1,
                'V': 2.7,
                'S': 5.0,
                },
            'disgust': {
                'A': 5.3,
                'D': 8.05,
                'V': 2.7,
                'S': 5.0,
                },
            'fear': {
                'A': 6.5,
                'D': 3.6,
                'V': 3.2,
                'S': 5.0,
                },
            'happiness':{
                'A': 7.22,
                'D': 6.28,
                'V': 8.6,
                'S': 5.0,
                },
            'sadness': {
                'A': 5.21,
                'D': 2.82,
                'V': 2.21,
                'S': 5.0 ,
                },
            'surprise': {
                'A': 5.0,
                'D': 5.0,
                'V': 5.0,
                'S': 10.0,
                }
    }
    centroids_direction: tuple[str, str] = ('emoml:big6', 'emoml:fsre-dimensions')
    aliases: Dict[str, str] = { # These are aliases for any key in the centroid, to avoid repeating a long name several times
                               'A': emoml['emoml:fsre-dimensions_arousal'],
                               'V': emoml['emoml:fsre-dimensions_valence'],
                               'D': emoml['emoml:fsre-dimensions_potency'],
                               'S': emoml['emoml:fsre-dimensions_unpredictability'],
                               'anger': emoml['emoml:big6anger'],
                               'disgust': emoml['emoml:big6disgust'],
                               'fear': emoml['emoml:big6fear'],
                               'happiness': emoml['emoml:big6happiness'],
                               'sadness': emoml['emoml:big6sadness'],
                               'surprise': emoml['emoml:big6surprise'],
                               }
