import datetime
from galaxy.web.framework.helpers import time_ago
import galaxy.util.shed_util_common as suc
from galaxy import web, util
from galaxy.web.base.controller import BaseAPIController
from galaxy.web.framework.helpers import is_true

import pkg_resources
pkg_resources.require( "Routes" )
import routes
import logging

log = logging.getLogger( __name__ )

def default_value_mapper( trans, repository_metadata ):
    return { 'id' : trans.security.encode_id( repository_metadata.id ),
             'repository_id' : trans.security.encode_id( repository_metadata.repository_id ),
             'time_last_tested' : time_ago( repository_metadata.time_last_tested ) }

class RepositoryRevisionsController( BaseAPIController ):
    """RESTful controller for interactions with tool shed repository revisions."""
    @web.expose_api
    def index( self, trans, downloadable=True, **kwd ):
        """
        GET /api/repository_revisions
        Displays a collection (list) of repository revisions.
        """
        rval = []
        downloadable = util.string_as_bool( downloadable )
        try:
            query = trans.sa_session.query( trans.app.model.RepositoryMetadata ) \
                                    .filter( trans.app.model.RepositoryMetadata.table.c.downloadable == downloadable ) \
                                    .order_by( trans.app.model.RepositoryMetadata.table.c.repository_id ) \
                                    .all()
            for repository_metadata in query:
                item = repository_metadata.get_api_value( view='collection', value_mapper=default_value_mapper( trans, repository_metadata ) )
                item[ 'url' ] = web.url_for( 'repository_revision', id=trans.security.encode_id( repository_metadata.id ) )
                rval.append( item )
        except Exception, e:
            rval = "Error in the Tool Shed repository_revisions API in index: " + str( e )
            log.error( rval + ": %s" % str( e ) )
            trans.response.status = 500
        return rval
    @web.expose_api
    def show( self, trans, id, **kwd ):
        """
        GET /api/repository_revisions/{encoded_repository_metadata_id}
        Displays information about a repository_metadata record in the Tool Shed.
        """
        try:
            repository_metadata = suc.get_repository_metadata_by_id( trans, id )
            repository_data = repository_metadata.get_api_value( view='element',  value_mapper=default_value_mapper( trans, repository_metadata ) )
            repository_data[ 'contents_url' ] = web.url_for( 'repository_revision_contents', repository_metadata_id=id )
        except Exception, e:
            message = "Error in the Tool Shed repository_revisions API in show: %s" % str( e )
            log.error( message, exc_info=True )
            trans.response.status = 500
            return message
        return repository_data
    @web.expose_api
    def update( self, trans, payload, **kwd ):
        """
        PUT /api/repository_revisions/{encoded_repository_metadata_id}/{payload}
        Updates the value of specified columns of the repository_metadata table based on the key / value pairs in payload.
        """
        repository_metadata_id = kwd.get( 'id', None )
        try:
            repository_metadata = suc.get_repository_metadata_by_id( trans, repository_metadata_id )
            flush_needed = False
            for key, new_value in payload.items():
                if hasattr( repository_metadata, key ):
                    old_value = getattr( repository_metadata, key )
                    setattr( repository_metadata, key, new_value )
                    if key in [ 'tools_functionally_correct', 'time_last_tested' ]:
                        # Automatically update repository_metadata.time_last_tested.
                        repository_metadata.time_last_tested = datetime.datetime.utcnow()
                    flush_needed = True
            if flush_needed:
                trans.sa_session.add( repository_metadata )
                trans.sa_session.flush()
        except Exception, e:
            message = "Error in the Tool Shed repository_revisions API in update: %s" % str( e )
            log.error( message, exc_info=True )
            trans.response.status = 500
            return message
        item = repository_metadata.as_dict( value_mapper=default_value_mapper( trans, repository_metadata ) )
        item[ 'url' ] = web.url_for( 'repository_revision', id=repository_metadata_id )
        return [ item ]