""" Json
"""
import json
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from eea.facetednavigation.caching import ramcache
from eea.facetednavigation.interfaces import ICriteria
from eea.facetednavigation.caching import cacheKeyFacetedNavigation
from eea.facetednavigation.browser.app.query import FacetedQueryHandler
try:
    import Missing
    missing = Missing.Value
except (ImportError, AttributeError):
    missing = None

class App(BrowserView):
    """ App
    """
    def json(self):
        res = {
            'categories': {
                'items': [],
                'properties': {}
            },
            'sources': {
                'items': [],
                'properties': {}
            }
        }

        criteria = ICriteria(self.context)
        for criterion in criteria.values():
            if criterion.index == 'Subject':
                res['categories']['properties']['name'] = criterion.getId()
            elif criterion.index == 'sourceTitle':
                res['sources']['properties']['name'] = criterion.getId()

        ctool = getToolByName(self.context, 'portal_catalog')

        index = ctool.Indexes.get('Subject')
        values = index.uniqueValues()
        res['categories']['items'] = values
        res['categories']['properties']['size'] = len(values)

        index = ctool.Indexes.get('sourceTitle')
        values = index.uniqueValues()
        res['sources']['items'] = values
        res['sources']['properties']['size'] = len(values)

        self.request.response.setHeader('content-type', 'application/json')

        res = json.dumps(res)
        callback = self.request.get('callback', None)
        if not callback:
            return res

        # JSONP
        return callback + u'(' + res + u')'

class Query(FacetedQueryHandler):
    """ Query
    """
    @ramcache(cacheKeyFacetedNavigation, dependencies=['eea.facetednavigation'])
    def __call__(self, *args, **kwargs):
        batch = self.query(**kwargs)

        res = {
            'items': [],
            'properties': {
                'size': batch.size,
                'pages': batch.sequence_length,
                'first': batch.first,
                'last': batch.last,
            }
        }

        for brain in batch:
            url = brain.getURL()
            sourceUrl = brain.sourceUrl
            sourceUrl = url if sourceUrl is missing else sourceUrl
            hasImage = brain.hasImage
            hasImage = False if hasImage is missing else hasImage
            thumbnail = url + '/' + 'image_preview' if hasImage else ''

            item = {
                'title': brain.Title,
                'description': brain.Description,
                'url': url,
                'thumbnail': thumbnail,
                'original': sourceUrl,
                'date': brain.EffectiveDate,
                'source': brain.sourceTitle,
            }
            res['items'].append(item)

        self.request.response.setHeader('content-type', 'application/json')
        res = json.dumps(res)
        callback = self.request.get('callback', None)
        if not callback:
            return res

        # JSONP
        return callback + u'(' + res + u')'
