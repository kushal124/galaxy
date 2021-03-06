"""API for searching the toolshed repositories"""
from galaxy import exceptions
from galaxy import eggs
from galaxy import util
from galaxy.web import _future_expose_api_raw_anonymous_and_sessionless as expose_api_raw_anonymous_and_sessionless
from galaxy.web.base.controller import BaseAPIController
from galaxy.webapps.tool_shed.search.repo_search import RepoSearch
from galaxy.web import url_for
import json

import logging
log = logging.getLogger( __name__ )


class SearchController ( BaseAPIController ):

    @expose_api_raw_anonymous_and_sessionless
    def search( self, trans, search_term, **kwd ):
        """ 
        Perform a search over the Whoosh index. 
        The index has to be pre-created with build_ts_whoosh_index.sh.
        TS config option toolshed_search_on has to be turned on and
        toolshed_whoosh_index_dir has to be specified and existing.

        :param search_term:
        :param page:
        :param jsonp:
        :param callback:

        :returns dict:
        """
        if not self.app.config.toolshed_search_on:
            raise exceptions.ConfigDoesNotAllowException( 'Searching the TS through the API is turned off for this instance.' )
        if not self.app.config.toolshed_whoosh_index_dir:
            raise exceptions.ConfigDoesNotAllowException( 'There is no directory for the search index specified. Please ontact the administrator.' )
        search_term = search_term.strip()
        if len( search_term ) < 3:
            raise exceptions.RequestParameterInvalidException( 'The search term has to be at least 3 characters long.' )

        page = kwd.get( 'page', 1 )
        return_jsonp = util.asbool( kwd.get( 'jsonp', False ) )
        callback = kwd.get( 'callback', 'callback' )

        repo_search = RepoSearch()
        results = repo_search.search( trans, search_term, page )
        results[ 'hostname' ] = url_for( '/', qualified = True )

        if return_jsonp:
            response = '%s(%s);' % ( callback, json.dumps( results ) )
        else:
            response = json.dumps( results )
        return response
