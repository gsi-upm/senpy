from senpy.plugins import EmotionConversionPlugin
from senpy.models import EmotionSet, Emotion, Error

import logging
logger = logging.getLogger(__name__)


class CentroidConversion(EmotionConversionPlugin):

    def _forward_conversion(self, original):
        """Sum the VAD value of all categories found."""
        res = Emotion()
        for e in original.onyx__hasEmotion:
            category = e.onyx__hasEmotionCategory
            if category in self.centroids:
                for dim, value in self.centroids[category].iteritems():
                    try:
                        res[dim] += value
                    except Exception:
                        res[dim] = value
        return res

    def _backwards_conversion(self, original):
        """Find the closest category"""
        dimensions = list(self.centroids.values())[0]

        def distance(e1, e2):
            return sum((e1[k] - e2.get(self.aliases[k], 0)) for k in dimensions)

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
        logger.debug('{}\n{}\n{}\n{}'.format(emotionSet, fromModel, toModel, params))
        e = EmotionSet()
        if fromModel == cf:
            e.onyx__hasEmotion.append(self._forward_conversion(emotionSet))
        elif fromModel == ct:
            for i in emotionSet.onyx__hasEmotion:
                e.onyx__hasEmotion.append(self._backwards_conversion(i))
        else:
            raise Error('EMOTION MODEL NOT KNOWN')
        yield e
