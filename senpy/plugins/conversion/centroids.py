from senpy.plugins import EmotionConversionPlugin
from senpy.models import EmotionSet, Emotion, Error

import logging
logger = logging.getLogger(__name__)


class CentroidConversion(EmotionConversionPlugin):
    def __init__(self, info):
        if 'centroids' not in info:
            raise Error('Centroid conversion plugins should provide '
                        'the centroids in their senpy file')
        if 'onyx:doesConversion' not in info:
            if 'centroids_direction' not in info:
                raise Error('Please, provide centroids direction')

            cf, ct = info['centroids_direction']
            info['onyx:doesConversion'] = [{
                'onyx:conversionFrom': cf,
                'onyx:conversionTo': ct
            }, {
                'onyx:conversionFrom': ct,
                'onyx:conversionTo': cf
            }]

        if 'aliases' in info:
            aliases = info['aliases']
            ncentroids = {}
            for k1, v1 in info['centroids'].items():
                nv1 = {}
                for k2, v2 in v1.items():
                    nv1[aliases.get(k2, k2)] = v2
                ncentroids[aliases.get(k1, k1)] = nv1
            info['centroids'] = ncentroids
        super(CentroidConversion, self).__init__(info)

    def _forward_conversion(self, original):
        """Sum the VAD value of all categories found."""
        res = Emotion()
        for e in original.onyx__hasEmotion:
            category = e.onyx__hasEmotionCategory
            if category in self.centroids:
                for dim, value in self.centroids[category].items():
                    try:
                        res[dim] += value
                    except Exception:
                        res[dim] = value
        return res

    def _backwards_conversion(self, original):
        """Find the closest category"""
        dimensions = list(self.centroids.values())[0]

        def distance(e1, e2):
            return sum((e1[k] - e2.get(k, 0)) for k in dimensions)

        emotion = ''
        mindistance = 10000000000000000000000.0
        for state in self.centroids:
            d = distance(self.centroids[state], original)
            if d < mindistance:
                mindistance = d
                emotion = state
        result = Emotion(onyx__hasEmotionCategory=emotion)
        return result

    def convert(self, emotionSet, fromModel, toModel, params):

        cf, ct = self.centroids_direction
        logger.debug(
            '{}\n{}\n{}\n{}'.format(emotionSet, fromModel, toModel, params))
        e = EmotionSet()
        if fromModel == cf and toModel == ct:
            e.onyx__hasEmotion.append(self._forward_conversion(emotionSet))
        elif fromModel == ct and toModel == cf:
            for i in emotionSet.onyx__hasEmotion:
                e.onyx__hasEmotion.append(self._backwards_conversion(i))
        else:
            raise Error('EMOTION MODEL NOT KNOWN')
        yield e
