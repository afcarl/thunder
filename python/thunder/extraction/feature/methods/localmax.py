from numpy import cos, sin, pi, array, sqrt

from thunder.extraction.feature.base import FeatureMethod, FeatureAlgorithm
from thunder.extraction.feature.creators import MeanFeatureCreator
from thunder.extraction.source import SourceModel, Source


class LocalMax(FeatureMethod):

    def __init__(self, **kwargs):
        algorithm = LocalMaxFeatureAlgorithm(**kwargs)
        creator = MeanFeatureCreator()
        super(self.__class__, self).__init__(algorithm, creator, **kwargs)


class LocalMaxFeatureAlgorithm(FeatureAlgorithm):
    """
    Find sources by identifying local maxima in an array.

    Will first find source centers, and then automatically define
    a circle around each center using the specified radius and resolution

    Parameters
    ----------
    minDistance : int, optional, default = 10
        Minimum distance between source centers

    maxSources : int, optional, deafut = None
        Maximum number of sources

    radius : scalar, optional, default=5
        Radius of circles defined around centers

    res : scalar, optional, deafult=10
        Number of points to use to define circles around centers
    """
    def __init__(self, minDistance=10, maxSources=None, radius=5, res=10, **extra):
        self.minDistance = minDistance
        if self.minDistance < 1:
            raise Exception("Cannot set minDistance less than 1, got %s" % minDistance)
        self.maxSources = maxSources
        self.radius = radius
        self.res = res

    def extract(self, im):
        """
        Extract sources from an image by finding local maxima.

        Parameters
        ----------
        im : ndarray
            The image or volume

        Returns
        -------
        A SourceModel with circular regions.
        """
        from numpy import ones, concatenate
        from skimage.feature import peak_local_max

        # extract local peaks
        if im.ndim == 2:
            peaks = peak_local_max(im, min_distance=self.minDistance, num_peaks=self.maxSources).tolist()
        else:
            peaks = []
            for i in range(0, im.shape[2]):
                tmp = peak_local_max(im[:, :, i], min_distance=self.minDistance, num_peaks=self.maxSources)
                peaks = peaks.append(concatenate((tmp, ones((len(tmp), 1)) * i), axis=1))

        # estimate circular regions from peak points
        def pointToCircle(center, radius):
            ccol = center[0]
            crow = center[1]
            r2 = radius * radius
            colrange = range(center[0] - radius + 1, center[0] + radius)
            rowrange = range(center[1] - radius + 1, center[1] + radius)
            pts = [[([c, r], radius - sqrt((c - ccol) ** 2 + (r - crow) ** 2))
                    for c in colrange if ((c - ccol) ** 2 + (r - crow) ** 2 < r2)] for r in rowrange]
            pts = concatenate(array(pts))
            k = map(lambda p: p[0], pts)
            v = map(lambda p: p[1], pts)
            return k, v

        sources = [pointToCircle(p, self.radius) for p in peaks]
        return SourceModel([Source(s[0], s[1]) for s in sources])