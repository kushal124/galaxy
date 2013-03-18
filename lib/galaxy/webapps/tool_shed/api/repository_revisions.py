import datetime
from galaxy.web.framework.helpers import time_ago
import tool_shed.util.shed_util_common as suc
from tool_shed.util import metadata_util
from galaxy import web, util
from galaxy.model.orm import and_, or_
from galaxy.web.base.controller import BaseAPIController
from galaxy.web.framework.helpers import is_true

import pkg_resources
pkg_resources.require( "Routes" )
import routes
import logging

log = logging.getLogger( __name__ )

def default_value_mapper( trans, repository_metadata ):
    value_mapper = { 'id' : trans.security.encode_id( repository_metadata.id ),
                     'repository_id' : trans.security.encode_id( repository_metadata.repository_id ) }
    if repository_metadata.time_last_tested:
        value_mapper[ 'time_last_tested' ] = time_ago( repository_metadata.time_last_tested )
    return value_mapper

class RepositoryRevisionsController( BaseAPIController ):
    """RESTful controller for interactions with tool shed repository revisions."""
    @web.expose_api
    def index( self, trans, **kwd ):
        """
        GET /api/repository_revisions
        Displays a collection (list) of repository revisions.
        """
        rval = []
        # Build up an anded clause list of filters.
        clause_list = []
        # Filter by downloadable if received.
        downloadable =  kwd.get( 'downloadable', None )
        if downloadable is not None:
            clause_list.append( trans.model.RepositoryMetadata.table.c.downloadable == util.string_as_bool( downloadable ) )
        # Filter by malicious if received.
        malicious =  kwd.get( 'malicious', None )
        if malicious is not None:
            clause_list.append( trans.model.RepositoryMetadata.table.c.malicious == util.string_as_bool( malicious ) )
        # Filter by tools_functionally_correct if received.
        tools_functionally_correct = kwd.get( 'tools_functionally_correct', None )
        if tools_functionally_correct is not None:
            clause_list.append( trans.model.RepositoryMetadata.table.c.tools_functionally_correct == util.string_as_bool( tools_functionally_correct ) )
        # Filter by do_not_test if received.
        do_not_test = kwd.get( 'do_not_test', None )
        if do_not_test is not None:
            clause_list.append( trans.model.RepositoryMetadata.table.c.do_not_test == util.string_as_bool( do_not_test ) )
        # Filter by includes_tools if received.
        includes_tools = kwd.get( 'includes_tools', None )
        if includes_tools is not None:
            clause_list.append( trans.model.RepositoryMetadata.table.c.includes_tools == util.string_as_bool( includes_tools ) )
        try:
            query = trans.sa_session.query( trans.app.model.RepositoryMetadata ) \
                                    .filter( and_( *clause_list ) ) \
                                    .order_by( trans.app.model.RepositoryMetadata.table.c.repository_id ) \
                                    .all()
            for repository_metadata in query:
                item = repository_metadata.get_api_value( view='collection',
                                                          value_mapper=default_value_mapper( trans, repository_metadata ) )
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
            repository_metadata = metadata_util.get_repository_metadata_by_id( trans, id )
            repository_data = repository_metadata.get_api_value( view='element',
                                                                 value_mapper=default_value_mapper( trans, repository_metadata ) )
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
            repository_metadata = metadata_util.get_repository_metadata_by_id( trans, repository_metadata_id )
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