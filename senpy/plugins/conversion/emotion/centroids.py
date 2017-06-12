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

        self.dimensions = set()
        for c in self.centroids.values():
            self.dimensions.update(c.keys())
        self.neutralPoints = self.get("neutralPoints", dict())
        if not self.neutralPoints:
            for i in self.dimensions:
                self.neutralPoints[i] = self.get("neutralValue", 0)

    def _forward_conversion(self, original):
        """Sum the VAD value of all categories found weighted by intensity.
        Intensities are scaled by onyx:maxIntensityValue if it is present, else maxIntensityValue
        is assumed to be one. Emotion entries that do not have onxy:hasEmotionIntensity specified
        are assumed to have maxIntensityValue. Emotion entries that do not have
        onyx:hasEmotionCategory specified are ignored."""
        res = Emotion()
        maxIntensity = float(original.get("onyx:maxIntensityValue", 1))
        for e in original.onyx__hasEmotion:
            category = e.get("onyx:hasEmotionCategory", None)
            if not category:
                continue
            intensity = e.get("onyx:hasEmotionIntensity", maxIntensity) / maxIntensity
            if not intensity:
                continue
            centroid = self.centroids.get(category, None)
            if centroid:
                for dim, value in centroid.items():
                    neutral = self.neutralPoints[dim]
                    if dim not in res:
                        res[dim] = 0
                    res[dim] += (value - neutral) * intensity + neutral
        return res

    def _backwards_conversion(self, original):
        """Find the closest category"""
        centroids = self.centroids
        neutralPoints = self.neutralPoints
        dimensions = self.dimensions

        def distance_k(centroid, original, k):
            # k component of the distance between the value and a given centroid
            return (centroid.get(k, neutralPoints[k]) - original.get(k, neutralPoints[k]))**2

        def distance(centroid):
            return sum(distance_k(centroid, original, k) for k in dimensions)

        emotion = min(centroids, key=lambda x: distance(centroids[x]))

        result = Emotion(onyx__hasEmotionCategory=emotion)
        result.onyx__algorithmConfidence = distance(centroids[emotion])
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
