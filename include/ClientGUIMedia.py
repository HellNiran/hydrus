from . import HydrusConstants as HC
from . import ClientConstants as CC
from . import ClientCaches
from . import ClientData
from . import ClientDragDrop
from . import ClientFiles
from . import ClientGUICanvas
from . import ClientGUIDialogs
from . import ClientGUIDialogsManage
from . import ClientGUIDialogsQuick
from . import ClientGUIDuplicates
from . import ClientGUIExport
from . import ClientGUIFunctions
from . import ClientGUIMenus
from . import ClientGUIScrolledPanels
from . import ClientGUIScrolledPanelsEdit
from . import ClientGUIScrolledPanelsManagement
from . import ClientGUIScrolledPanelsReview
from . import ClientGUIShortcuts
from . import ClientGUITags
from . import ClientGUITopLevelWindows
from . import ClientMedia
from . import ClientPaths
from . import ClientSearch
from . import ClientTags
from . import ClientThreading
import collections
from . import HydrusExceptions
from . import HydrusNetwork
from . import HydrusPaths
from . import HydrusSerialisable
from . import HydrusTags
from . import HydrusThreading
import itertools
import json
import os
import random
import threading
import time
import traceback
import yaml
from . import QtPorting as QP
from . import HydrusData
from . import HydrusGlobals as HG
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW
from qtpy import QtGui as QG
from . import QtPorting as QP

def CopyMediaURLs( medias ):
    
    urls = set()
    
    for media in medias:
        
        media_urls = media.GetLocationsManager().GetURLs()
        
        urls.update( media_urls )
        
    
    urls = list( urls )
    
    urls.sort()
    
    urls_string = os.linesep.join( urls )
    
    HG.client_controller.pub( 'clipboard', 'text', urls_string )
    
def CopyMediaURLClassURLs( medias, url_class ):
    
    urls = set()
    
    for media in medias:
        
        media_urls = media.GetLocationsManager().GetURLs()
        
        for url in media_urls:
            
            if url_class.Matches( url ):
                
                urls.add( url )
                
            
        
    
    urls = list( urls )
    
    urls.sort()
    
    urls_string = os.linesep.join( urls )
    
    HG.client_controller.pub( 'clipboard', 'text', urls_string )
    
def DoOpenKnownURLFromShortcut( win, media ):
    
    urls = media.GetLocationsManager().GetURLs()
    
    matched_labels_and_urls = []
    unmatched_urls = []
    
    if len( urls ) > 0:
        
        for url in urls:
            
            url_class = HG.client_controller.network_engine.domain_manager.GetURLClass( url )
            
            if url_class is None:
                
                unmatched_urls.append( url )
                
            else:
                
                label = url_class.GetName() + ': ' + url
                
                matched_labels_and_urls.append( ( label, url ) )
                
            
        
        matched_labels_and_urls.sort()
        unmatched_urls.sort()
        
    
    if len( matched_labels_and_urls ) == 0:
        
        return
        
    elif len( matched_labels_and_urls ) == 1:
        
        url = matched_labels_and_urls[0][1]
        
    else:
        
        matched_labels_and_urls.extend( ( url, url ) for url in unmatched_urls )
        
        try:
            
            url = ClientGUIDialogsQuick.SelectFromList( win, 'Select which URL', matched_labels_and_urls, sort_tuples = False )
            
        except HydrusExceptions.CancelledException:
            
            return
            
        
    
    ClientPaths.LaunchURLInWebBrowser( url )
    
def OpenURLs( urls ):
    
    urls = list( urls )
    
    urls.sort()
    
    if len( urls ) > 1:
        
        message = 'Open the {} URLs in your web browser?'.format( len( urls ) )
        
        if len( urls ) > 10:
            
            message += ' This will take some time.'
            
        
        result = ClientGUIDialogsQuick.GetYesNo( HG.client_controller.gui, message )
        
        if result != QW.QDialog.Accepted:
            
            return
            
        
    
    def do_it( urls ):
        
        job_key = None
        
        num_urls = len( urls )
        
        if num_urls > 5:
            
            job_key = ClientThreading.JobKey( pausable = True, cancellable = True )
            
            job_key.SetVariable( 'popup_title', 'Opening URLs' )
            
            HG.client_controller.pub( 'message', job_key )
            
        
        try:
            
            for ( i, url ) in enumerate( urls ):
                
                if job_key is not None:
                    
                    ( i_paused, should_quit ) = job_key.WaitIfNeeded()
                    
                    if should_quit:
                        
                        return
                        
                    
                    job_key.SetVariable( 'popup_text_1', HydrusData.ConvertValueRangeToPrettyString( i + 1, num_urls ) )
                    job_key.SetVariable( 'popup_gauge_1', ( i + 1, num_urls ) )
                    
                
                ClientPaths.LaunchURLInWebBrowser( url )
                
                time.sleep( 1 )
                
            
        finally:
            
            if job_key is not None:
                
                job_key.Finish()
                
                job_key.Delete( 1 )
                
            
        
    
    HG.client_controller.CallToThread( do_it, urls )
    
def OpenMediaURLs( medias ):
    
    urls = set()
    
    for media in medias:
        
        media_urls = media.GetLocationsManager().GetURLs()
        
        urls.update( media_urls )
        
    
    OpenURLs( urls )
    
def OpenMediaURLClassURLs( medias, url_class ):
    
    urls = set()
    
    for media in medias:
        
        media_urls = media.GetLocationsManager().GetURLs()
        
        for url in media_urls:
            
            if url_class.Matches( url ):
                
                urls.add( url )
                
            
        
    
    OpenURLs( urls )
    
def AddFileViewingStatsMenu( menu, focus_media ):
    
    view_style = HG.client_controller.new_options.GetInteger( 'file_viewing_stats_menu_display' )
    
    if view_style == CC.FILE_VIEWING_STATS_MENU_DISPLAY_NONE:
        
        return
        
    
    fvsm = focus_media.GetFileViewingStatsManager()
    
    if view_style == CC.FILE_VIEWING_STATS_MENU_DISPLAY_MEDIA_AND_PREVIEW_SUMMED:
        
        combined_line = fvsm.GetPrettyCombinedLine()
        
        ClientGUIMenus.AppendMenuLabel( menu, combined_line )
        
    else:
        
        media_line = fvsm.GetPrettyMediaLine()
        preview_line = fvsm.GetPrettyPreviewLine()
        
        if view_style == CC.FILE_VIEWING_STATS_MENU_DISPLAY_MEDIA_ONLY:
            
            ClientGUIMenus.AppendMenuLabel( menu, media_line )
            
        elif view_style == CC.FILE_VIEWING_STATS_MENU_DISPLAY_MEDIA_AND_PREVIEW_IN_SUBMENU:
            
            submenu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuLabel( submenu, preview_line )
            
            ClientGUIMenus.AppendMenu( menu, submenu, media_line )
            
        elif view_style == CC.FILE_VIEWING_STATS_MENU_DISPLAY_MEDIA_AND_PREVIEW_STACKED:
            
            ClientGUIMenus.AppendMenuLabel( menu, media_line )
            ClientGUIMenus.AppendMenuLabel( menu, preview_line )
            
        
    
def AddKnownURLsViewCopyMenu( win, menu, focus_media, selected_media = None ):
    
    # figure out which urls this focused file has
    
    focus_urls = focus_media.GetLocationsManager().GetURLs()
    
    focus_matched_labels_and_urls = []
    focus_unmatched_urls = []
    focus_labels_and_urls = []
    
    if len( focus_urls ) > 0:
        
        for url in focus_urls:
            
            url_class = HG.client_controller.network_engine.domain_manager.GetURLClass( url )
            
            if url_class is None:
                
                focus_unmatched_urls.append( url )
                
            else:
                
                label = url_class.GetName() + ': ' + url
                
                focus_matched_labels_and_urls.append( ( label, url ) )
                
            
        
        focus_matched_labels_and_urls.sort()
        focus_unmatched_urls.sort()
        
        focus_labels_and_urls = list( focus_matched_labels_and_urls )
        
        focus_labels_and_urls.extend( ( ( url, url ) for url in focus_unmatched_urls ) )
        
    
    # figure out which urls these selected files have
    
    selected_media_url_classes = set()
    multiple_or_unmatching_selection_url_classes = False
    
    if selected_media is not None and len( selected_media ) > 1:
        
        selected_media = ClientMedia.FlattenMedia( selected_media )
        
        SAMPLE_SIZE = 256
        
        if len( selected_media ) > SAMPLE_SIZE:
            
            selected_media_sample = random.sample( selected_media, SAMPLE_SIZE )
            
        else:
            
            selected_media_sample = selected_media
            
        
        for media in selected_media_sample:
            
            media_urls = media.GetLocationsManager().GetURLs()
            
            for url in media_urls:
                
                url_class = HG.client_controller.network_engine.domain_manager.GetURLClass( url )
                
                if url_class is None:
                    
                    multiple_or_unmatching_selection_url_classes = True
                    
                else:
                    
                    selected_media_url_classes.add( url_class )
                    
                
            
        
        if len( selected_media_url_classes ) > 1:
            
            multiple_or_unmatching_selection_url_classes = True
            
        
    
    if len( focus_labels_and_urls ) > 0 or len( selected_media_url_classes ) > 0 or multiple_or_unmatching_selection_url_classes:
        
        urls_menu = QW.QMenu( menu )
        
        urls_visit_menu = QW.QMenu( urls_menu )
        urls_copy_menu = QW.QMenu( urls_menu )
        
        # copy each this file's urls (of a particular type)
        
        if len( focus_labels_and_urls ) > 0:
            
            for ( label, url ) in focus_labels_and_urls:
                
                ClientGUIMenus.AppendMenuItem( urls_visit_menu, label, 'Open this url in your web browser.', ClientPaths.LaunchURLInWebBrowser, url )
                ClientGUIMenus.AppendMenuItem( urls_copy_menu, label, 'Copy this url to your clipboard.', HG.client_controller.pub, 'clipboard', 'text', url )
                
            
        
        # copy this file's urls
        
        there_are_focus_url_classes_to_action = len( focus_matched_labels_and_urls ) > 1
        multiple_or_unmatching_focus_url_classes = len( focus_unmatched_urls ) > 0 and len( focus_labels_and_urls ) > 1 # if there are unmatched urls and more than one thing total
        
        if there_are_focus_url_classes_to_action or multiple_or_unmatching_focus_url_classes:
            
            ClientGUIMenus.AppendSeparator( urls_visit_menu )
            ClientGUIMenus.AppendSeparator( urls_copy_menu )
            
        
        if there_are_focus_url_classes_to_action:
            
            urls = [ url for ( label, url ) in focus_matched_labels_and_urls ]
            
            label = 'open this file\'s ' + HydrusData.ToHumanInt( len( urls ) ) + ' recognised urls in your web browser'
            
            ClientGUIMenus.AppendMenuItem( urls_visit_menu, label, 'Open these urls in your web browser.', OpenURLs, urls )
            
            urls_string = os.linesep.join( urls )
            
            label = 'copy this file\'s ' + HydrusData.ToHumanInt( len( urls ) ) + ' recognised urls to your clipboard'
            
            ClientGUIMenus.AppendMenuItem( urls_copy_menu, label, 'Copy these urls to your clipboard.', HG.client_controller.pub, 'clipboard', 'text', urls_string )
            
        
        if multiple_or_unmatching_focus_url_classes:
            
            urls = [ url for ( label, url ) in focus_labels_and_urls ]
            
            label = 'open this file\'s ' + HydrusData.ToHumanInt( len( urls ) ) + ' urls in your web browser'
            
            ClientGUIMenus.AppendMenuItem( urls_visit_menu, label, 'Open these urls in your web browser.', OpenURLs, urls )
            
            urls_string = os.linesep.join( urls )
            
            label = 'copy this file\'s ' + HydrusData.ToHumanInt( len( urls ) ) + ' urls to your clipboard'
            
            ClientGUIMenus.AppendMenuItem( urls_copy_menu, label, 'Copy this url to your clipboard.', HG.client_controller.pub, 'clipboard', 'text', urls_string )
            
        
        # now by url match type
        
        there_are_selection_url_classes_to_action = len( selected_media_url_classes ) > 0
        
        if there_are_selection_url_classes_to_action or multiple_or_unmatching_selection_url_classes:
            
            ClientGUIMenus.AppendSeparator( urls_visit_menu )
            ClientGUIMenus.AppendSeparator( urls_copy_menu )
            
        
        if there_are_selection_url_classes_to_action:
            
            selected_media_url_classes = list( selected_media_url_classes )
            
            selected_media_url_classes.sort( key = lambda url_class: url_class.GetName() )
            
            for url_class in selected_media_url_classes:
                
                label = 'open files\' ' + url_class.GetName() + ' urls in your web browser'
                
                ClientGUIMenus.AppendMenuItem( urls_visit_menu, label, 'Open this url class in your web browser for all files.', OpenMediaURLClassURLs, selected_media, url_class )
                
                label = 'copy files\' ' + url_class.GetName() + ' urls'
                
                ClientGUIMenus.AppendMenuItem( urls_copy_menu, label, 'Copy this url class for all files.', CopyMediaURLClassURLs, selected_media, url_class )
                
            
        
        # now everything
        
        if multiple_or_unmatching_selection_url_classes:
            
            label = 'open all files\' urls'
            
            ClientGUIMenus.AppendMenuItem( urls_visit_menu, label, 'Open urls in your web browser for all files.', OpenMediaURLs, selected_media )
            
            label = 'copy all files\' urls'
            
            ClientGUIMenus.AppendMenuItem( urls_copy_menu, label, 'Copy urls for all files.', CopyMediaURLs, selected_media )
            
        
        #
        
        ClientGUIMenus.AppendMenu( urls_menu, urls_visit_menu, 'open' )
        ClientGUIMenus.AppendMenu( urls_menu, urls_copy_menu, 'copy' )
        
        ClientGUIMenus.AppendMenu( menu, urls_menu, 'known urls' )
        
    
def AddServiceKeyLabelsToMenu( menu, service_keys, phrase ):
    
    services_manager = HG.client_controller.services_manager
    
    if len( service_keys ) == 1:
        
        ( service_key, ) = service_keys
        
        name = services_manager.GetName( service_key )
        
        label = phrase + ' ' + name
        
        ClientGUIMenus.AppendMenuLabel( menu, label )
        
    else:
        
        submenu = QW.QMenu( menu )
        
        for service_key in service_keys:
            
            name = services_manager.GetName( service_key )
            
            ClientGUIMenus.AppendMenuLabel( submenu, name )
            
        
        ClientGUIMenus.AppendMenu( menu, submenu, phrase + '\u2026' )
        
    
def AddServiceKeysToMenu( event_handler, menu, service_keys, phrase, description, callable ):
    
    services_manager = HG.client_controller.services_manager
    
    if len( service_keys ) == 1:
        
        ( service_key, ) = service_keys
        
        name = services_manager.GetName( service_key )
        
        label = phrase + ' ' + name
        
        ClientGUIMenus.AppendMenuItem( menu, label, description, callable, service_key )
        
    else:
        
        submenu = QW.QMenu( menu )
        
        for service_key in service_keys: 
            
            name = services_manager.GetName( service_key )
            
            ClientGUIMenus.AppendMenuItem( submenu, name, description, callable, service_key )
            
        
        ClientGUIMenus.AppendMenu( menu, submenu, phrase + '\u2026' )
        
    
class MediaPanel( ClientMedia.ListeningMediaList, QW.QScrollArea ):
    
    def __init__( self, parent, page_key, file_service_key, media_results ):
        
        QW.QScrollArea.__init__( self, parent )
        
        self.setFrameStyle( QW.QFrame.Panel | QW.QFrame.Sunken )
        self.setLineWidth( 2 )
        
        self.resize( QC.QSize( 20, 20 ) )
        self.setWidget( QW.QWidget() )
        self.setWidgetResizable( True )
        
        ClientMedia.ListeningMediaList.__init__( self, file_service_key, media_results )
        
        self._UpdateBackgroundColour()
        
        self.verticalScrollBar().setSingleStep( 50 )
        
        self._page_key = page_key
        
        self._focused_media = None
        self._next_best_media_after_focused_media_removed = None
        self._shift_focused_media = None
        
        HG.client_controller.sub( self, 'AddMediaResults', 'add_media_results' )
        HG.client_controller.sub( self, 'SetFocusedMedia', 'set_focus' )
        HG.client_controller.sub( self, 'Collect', 'collect_media' )
        HG.client_controller.sub( self, 'Sort', 'sort_media' )
        HG.client_controller.sub( self, 'FileDumped', 'file_dumped' )
        HG.client_controller.sub( self, 'RemoveMedia', 'remove_media' )
        HG.client_controller.sub( self, '_UpdateBackgroundColour', 'notify_new_colourset' )
        HG.client_controller.sub( self, 'SelectByTags', 'select_files_with_tags' )
        
        self._due_a_forced_selection_pub = False
        
        self._PublishSelectionChange( force_reload = True )
        
        self._my_shortcut_handler = ClientGUIShortcuts.ShortcutsHandler( self, [ 'media' ] )
        
    
    def __bool__( self ):
        
        return QP.isValid( self )
    
        
    def _Archive( self ):
        
        hashes = self._GetSelectedHashes( discriminant = CC.DISCRIMINANT_INBOX )
        
        if len( hashes ) > 0:
            
            if HC.options[ 'confirm_archive' ]:
                
                if len( hashes ) > 1:
                    
                    message = 'Archive ' + HydrusData.ToHumanInt( len( hashes ) ) + ' files?'
                    
                    result = ClientGUIDialogsQuick.GetYesNo( self, message )
                    
                    if result != QW.QDialog.Accepted:
                        
                        return
                        
                    
                
            
            HG.client_controller.Write( 'content_updates', { CC.COMBINED_LOCAL_FILE_SERVICE_KEY : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_ARCHIVE, hashes ) ] } )
            
        
    
    def _ArchiveDeleteFilter( self ):
        
        if len( self._selected_media ) == 0:
            
            media_results = self.GenerateMediaResults( discriminant = CC.DISCRIMINANT_LOCAL_BUT_NOT_IN_TRASH, selected_media = set( self._sorted_media ), for_media_viewer = True )
            
        else:
            
            media_results = self.GenerateMediaResults( discriminant = CC.DISCRIMINANT_LOCAL_BUT_NOT_IN_TRASH, selected_media = set( self._selected_media ), for_media_viewer = True )
            
        
        if len( media_results ) > 0:
            
            canvas_frame = ClientGUICanvas.CanvasFrame( self.window() )
            
            canvas_window = ClientGUICanvas.CanvasMediaListFilterArchiveDelete( canvas_frame, self._page_key, media_results )
            
            canvas_frame.SetCanvas( canvas_window )
            
        
    
    def _CopyBMPToClipboard( self ):
        
        if self._focused_media is not None:
            
            media = self._focused_media.GetDisplayMedia()
            
            if media.GetMime() in HC.IMAGES:
                
                HG.client_controller.pub( 'clipboard', 'bmp', media )
                
            else:
                
                QW.QMessageBox.critical( self, 'Error', 'Sorry, cannot take bmps of anything but static images right now!' )
                
            
        
    
    def _CopyFilesToClipboard( self ):
        
        client_files_manager = HG.client_controller.client_files_manager
        
        media = self._GetSelectedFlatMedia( discriminant = CC.DISCRIMINANT_LOCAL )
        
        paths = []
        
        for m in media:
            
            hash = m.GetHash()
            mime = m.GetMime()
            
            path = client_files_manager.GetFilePath( hash, mime, check_file_exists = False )
            
            paths.append( path )
            
        
        HG.client_controller.pub( 'clipboard', 'paths', paths )
        
    
    def _CopyHashToClipboard( self, hash_type ):
        
        display_media = self._focused_media.GetDisplayMedia()
        
        sha256_hash = display_media.GetHash()
        
        if hash_type == 'sha256':
            
            hex_hash = sha256_hash.hex()
            
        else:
            
            if display_media.GetLocationsManager().IsLocal():
                
                ( other_hash, ) = HG.client_controller.Read( 'file_hashes', ( sha256_hash, ), 'sha256', hash_type )
                
                hex_hash = other_hash.hex()
                
            else:
                
                QW.QMessageBox.critical( self, 'Error', 'Unfortunately, you do not have that file in your database, so its non-sha256 hashes are unknown.' )
                
                return
                
            
        
        HG.client_controller.pub( 'clipboard', 'text', hex_hash )
        
    
    def _CopyHashesToClipboard( self, hash_type ):
        
        if hash_type == 'sha256':
            
            hex_hashes = os.linesep.join( [ hash.hex() for hash in self._GetSelectedHashes( ordered = True ) ] )
            
        else:
            
            sha256_hashes = self._GetSelectedHashes( discriminant = CC.DISCRIMINANT_LOCAL, ordered = True )
            
            if len( sha256_hashes ) > 0:
                
                other_hashes = HG.client_controller.Read( 'file_hashes', sha256_hashes, 'sha256', hash_type )
                
                hex_hashes = os.linesep.join( [ other_hash.hex() for other_hash in other_hashes ] )
                
            else:
                
                QW.QMessageBox.critical( self, 'Error', 'Unfortunately, none of those files are in your database, so their non-sha256 hashes are unknown.' )
                
                return
                
            
        
        HG.client_controller.pub( 'clipboard', 'text', hex_hashes )
        
    
    def _CopyPathToClipboard( self ):
        
        display_media = self._focused_media.GetDisplayMedia()
        
        client_files_manager = HG.client_controller.client_files_manager
        
        path = client_files_manager.GetFilePath( display_media.GetHash(), display_media.GetMime() )
        
        HG.client_controller.pub( 'clipboard', 'text', path )
        
    
    def _CopyPathsToClipboard( self ):
        
        media_results = self.GenerateMediaResults( discriminant = CC.DISCRIMINANT_LOCAL, selected_media = set( self._selected_media ) )
        
        client_files_manager = HG.client_controller.client_files_manager
        
        paths = []
        
        for media_result in media_results:
            
            paths.append( client_files_manager.GetFilePath( media_result.GetHash(), media_result.GetMime(), check_file_exists = False ) )
            
        
        text = os.linesep.join( paths )
        
        HG.client_controller.pub( 'clipboard', 'text', text )
        
    
    def _CopyServiceFilenameToClipboard( self, service_key ):
        
        display_media = self._focused_media.GetDisplayMedia()
        
        hash = display_media.GetHash()
        
        ( filename, ) = HG.client_controller.Read( 'service_filenames', service_key, { hash } )
        
        service = HG.client_controller.services_manager.GetService( service_key )
        
        if service.GetServiceType() == HC.IPFS:
            
            multihash_prefix = service.GetMultihashPrefix()
            
            filename = multihash_prefix + filename
            
        
        HG.client_controller.pub( 'clipboard', 'text', filename )
        
    
    def _CopyServiceFilenamesToClipboard( self, service_key ):
        
        prefix = ''
        
        service = HG.client_controller.services_manager.GetService( service_key )
        
        if service.GetServiceType() == HC.IPFS:
            
            prefix = service.GetMultihashPrefix()
            
        
        hashes = self._GetSelectedHashes( has_location = service_key )
        
        if len( hashes ) > 0:
            
            filenames = [ prefix + filename for filename in HG.client_controller.Read( 'service_filenames', service_key, hashes ) ]
            
            if len( filenames ) > 0:
                
                copy_string = os.linesep.join( filenames )
                
                HG.client_controller.pub( 'clipboard', 'text', copy_string )
                
            else:
                
                HydrusData.ShowText( 'Could not find any service filenames for that selection!' )
                
            
        else:
            
            HydrusData.ShowText( 'Could not find any files with the requested service!' )
            
        
    
    def _Delete( self, file_service_key = None ):
        
        if file_service_key is None or file_service_key in ( CC.LOCAL_FILE_SERVICE_KEY, CC.TRASH_SERVICE_KEY ):
            
            default_reason = 'Deleted from Media Page.'
            
        else:
            
            default_reason = 'admin'
            
        
        try:
            
            ( involves_physical_delete, jobs ) = ClientGUIDialogsQuick.GetDeleteFilesJobs( self, self._selected_media, default_reason, suggested_file_service_key = file_service_key )
            
        except HydrusExceptions.CancelledException:
            
            return
            
        
        if involves_physical_delete:
            
            self._SetFocusedMedia( None )
            
        
        def do_it( jobs ):
            
            for service_keys_to_content_updates in jobs:
                
                HG.client_controller.WriteSynchronous( 'content_updates', service_keys_to_content_updates )
                
            
        
        HG.client_controller.CallToThread( do_it, jobs )
        
    
    def _DeselectSelect( self, media_to_deselect, media_to_select ):
        
        if len( media_to_deselect ) > 0:
            
            for m in media_to_deselect: m.Deselect()
            
            self._RedrawMedia( media_to_deselect )
            
            self._selected_media.difference_update( media_to_deselect )
            
        
        if len( media_to_select ) > 0:
            
            for m in media_to_select: m.Select()
            
            self._RedrawMedia( media_to_select )
            
            self._selected_media.update( media_to_select )
            
        
        self._PublishSelectionChange()
        
    
    def _DownloadSelected( self ):
        
        hashes = self._GetSelectedHashes( discriminant = CC.DISCRIMINANT_NOT_LOCAL )
        
        self._DownloadHashes( hashes )
        
    
    def _DownloadHashes( self, hashes ):
        
        HG.client_controller.quick_download_manager.DownloadFiles( hashes )
        
    
    def _EditDuplicateActionOptions( self, duplicate_type ):
        
        new_options = HG.client_controller.new_options
        
        duplicate_action_options = new_options.GetDuplicateActionOptions( duplicate_type )
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit duplicate merge options' ) as dlg_2:
            
            panel = ClientGUIScrolledPanelsEdit.EditDuplicateActionOptionsPanel( dlg_2, duplicate_type, duplicate_action_options )
            
            dlg_2.SetPanel( panel )
            
            if dlg_2.exec() == QW.QDialog.Accepted:
                
                duplicate_action_options = panel.GetValue()
                
                new_options.SetDuplicateActionOptions( duplicate_type, duplicate_action_options )
                
            
        
    
    def _ExportFiles( self, do_export_and_then_quit = False ):
        
        if len( self._selected_media ) > 0:
            
            flat_media = []
            
            for media in self._sorted_media:
                
                if media in self._selected_media:
                    
                    if media.IsCollection():
                        
                        flat_media.extend( media.GetFlatMedia() )
                        
                    else:
                        
                        flat_media.append( media )
                        
                    
                
            
            frame = ClientGUITopLevelWindows.FrameThatTakesScrollablePanel( self, 'export files' )
            
            panel = ClientGUIExport.ReviewExportFilesPanel( frame, flat_media, do_export_and_then_quit = do_export_and_then_quit )
            
            frame.SetPanel( panel )
            
        
    
    def _FullScreen( self, first_media = None ):
        
        if self._focused_media is not None:
            
            display_media = self._focused_media.GetDisplayMedia()
            
            new_options = HG.client_controller.new_options
            
            ( media_show_action, media_start_paused, media_start_with_embed ) = new_options.GetMediaShowAction( display_media.GetMime() )
            
            if media_show_action == CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY:
                
                hash = display_media.GetHash()
                mime = display_media.GetMime()
                
                client_files_manager = HG.client_controller.client_files_manager
                
                path = client_files_manager.GetFilePath( hash, mime )
                
                new_options = HG.client_controller.new_options
                
                launch_path = new_options.GetMimeLaunch( mime )
                
                HydrusPaths.LaunchFile( path, launch_path )
                
                return
                
            elif media_show_action == CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW:
                
                return
                
            
        
        media_results = self.GenerateMediaResults( discriminant = CC.DISCRIMINANT_LOCAL, for_media_viewer = True )
        
        if len( media_results ) > 0:
            
            if first_media is None and self._focused_media is not None: first_media = self._focused_media
            
            if first_media is not None and first_media.GetLocationsManager().IsLocal(): first_hash = first_media.GetDisplayMedia().GetHash()
            else: first_hash = None
            
            canvas_frame = ClientGUICanvas.CanvasFrame( self.window() )
            
            canvas_window = ClientGUICanvas.CanvasMediaListBrowser( canvas_frame, self._page_key, media_results, first_hash )
            
            canvas_frame.SetCanvas( canvas_window )
            
        
    
    def _GetNumSelected( self ):
        
        return sum( [ media.GetNumFiles() for media in self._selected_media ] )
        
    
    def _GetPrettyStatus( self ):
        
        num_files = len( self._hashes )
        
        num_selected = self._GetNumSelected()
        
        ( num_files_descriptor, selected_files_descriptor ) = self._GetSortedSelectedMimeDescriptors()
        
        if num_files == 1:
            
            num_files_string = '1 ' + num_files_descriptor
            
        else:
            
            num_files_string = HydrusData.ToHumanInt( num_files ) + ' ' + num_files_descriptor + 's'
            
        
        s = num_files_string # 23 files
        
        if num_selected == 0:
            
            if num_files > 0:
                
                pretty_total_size = self._GetPrettyTotalSize()
                
                s += ' - totalling ' + pretty_total_size
                
            
        else:
            
            s += ' - '
            
            if num_selected == 1 or selected_files_descriptor == num_files_descriptor:
                
                selected_files_string = HydrusData.ToHumanInt( num_selected )
                
            else:
                
                selected_files_string = HydrusData.ToHumanInt( num_selected ) + ' ' + selected_files_descriptor + 's'
                
            
            if num_selected == 1: # 23 files - 1 video selected, file_info
                
                ( selected_media, ) = self._selected_media
                
                s += selected_files_string + ' selected, ' + ', '.join( selected_media.GetPrettyInfoLines() )
                
            else: # 23 files - 5 selected, selection_info
                
                num_inbox = sum( ( media.GetNumInbox() for media in self._selected_media ) )
                
                if num_inbox == num_selected:
                    
                    inbox_phrase = 'all in inbox, '
                    
                elif num_inbox == 0:
                    
                    inbox_phrase = 'all archived, '
                    
                else:
                    
                    inbox_phrase = HydrusData.ToHumanInt( num_inbox ) + ' in inbox and ' + HydrusData.ToHumanInt( num_selected - num_inbox ) + ' archived, '
                    
                
                pretty_total_size = self._GetPrettyTotalSize( only_selected = True )
                
                s += selected_files_string + ' selected, ' + inbox_phrase + 'totalling ' + pretty_total_size
                
            
        
        return s
        
    
    def _GetPrettyTotalSize( self, only_selected = False ):
        
        if only_selected:
            
            media_source = self._selected_media
            
        else:
            
            media_source = self._sorted_media
            
        
        total_size = sum( [ media.GetSize() for media in media_source ] )
        
        unknown_size = False in ( media.IsSizeDefinite() for media in media_source )
        
        if total_size == 0:
            
            if unknown_size:
                
                return 'unknown size'
                
            else:
                
                return HydrusData.ToHumanBytes( 0 )
                
            
        else:
            
            if unknown_size:
                
                return HydrusData.ToHumanBytes( total_size ) + ' + some unknown size'
                
            else:
                
                return HydrusData.ToHumanBytes( total_size )
                
            
        
    
    def _GetSelectedHashes( self, has_location = None, discriminant = None, not_uploaded_to = None, ordered = False ):
        
        if ordered:
            
            result = []
            
            for media in self._sorted_media:
                
                if media in self._selected_media:
                    
                    result.extend( media.GetHashes( has_location, discriminant, not_uploaded_to, ordered ) )
                    
                
            
        else:
            
            result = set()
            
            for media in self._selected_media:
                
                result.update( media.GetHashes( has_location, discriminant, not_uploaded_to, ordered ) )
                
            
        
        return result
        
    
    def _GetSelectedCollections( self ):
        
        sorted_selected_collections = [ media for media in self._sorted_media if media.IsCollection() and media in self._selected_media ]
        
        return sorted_selected_collections
        

    def _GetSelectedFlatMedia( self, has_location = None, discriminant = None, not_uploaded_to = None ):
        
        # this now always delivers sorted results
        
        sorted_selected_media = [ media for media in self._sorted_media if media in self._selected_media ]
        
        flat_media = ClientMedia.FlattenMedia( sorted_selected_media )
        
        flat_media = [ media for media in flat_media if media.MatchesDiscriminant( has_location = has_location, discriminant = discriminant, not_uploaded_to = not_uploaded_to ) ]
        
        return flat_media
        
    
    def _GetSimilarTo( self, max_hamming ):
        
        hashes = set()
        
        media = self._GetSelectedFlatMedia()
        
        for m in media:
            
            if m.GetMime() in HC.MIMES_WE_CAN_PHASH:
                
                hashes.add( m.GetHash() )
                
            
        
        if len( hashes ) > 0:
            
            initial_predicates = [ ClientSearch.Predicate( HC.PREDICATE_TYPE_SYSTEM_SIMILAR_TO, ( tuple( hashes ), max_hamming ) ) ]
            
            HG.client_controller.pub( 'new_page_query', CC.LOCAL_FILE_SERVICE_KEY, initial_predicates = initial_predicates )
            
        
    
    def _GetSortedSelectedMimeDescriptors( self ):
        
        def GetDescriptor( classes ):
            
            if len( classes ) == 0:
                
                return 'file'
                
            
            if len( classes ) == 1:
                
                ( mime, ) = classes
                
                return HC.mime_string_lookup[ mime ]
                
            
            if len( classes.difference( HC.IMAGES ) ) == 0:
                
                return 'image'
                
            elif len( classes.difference( HC.ANIMATIONS ) ) == 0:
                
                return 'animation'
                
            elif len( classes.difference( HC.VIDEO ) ) == 0:
                
                return 'video'
                
            elif len( classes.difference( HC.AUDIO ) ) == 0:
                
                return 'audio file'
                
            else:
                
                return 'file'
                
            
        
        if len( self._sorted_media ) > 1000:
            
            sorted_mime_descriptor = 'file'
            
        else:
            
            sorted_mimes = { media.GetMime() for media in self._sorted_media }
            
            sorted_mime_descriptor = GetDescriptor( sorted_mimes )
            
        
        if len( self._selected_media ) > 1000:
            
            selected_mime_descriptor = 'file'
            
        else:
            
            selected_mimes = { media.GetMime() for media in self._selected_media }
            
            selected_mime_descriptor = GetDescriptor( selected_mimes )
            
        
        return ( sorted_mime_descriptor, selected_mime_descriptor )
        
    
    def _HitMedia( self, media, ctrl, shift ):
        
        if media is None:
            
            if not ctrl and not shift:
                
                self._Select( ClientMedia.FileFilter( ClientMedia.FILE_FILTER_NONE ) )
                self._SetFocusedMedia( None )
                self._shift_focused_media = None
                
            
        else:
            
            if ctrl:
                
                if media.IsSelected():
                    
                    self._DeselectSelect( ( media, ), () )
                    
                    if self._focused_media == media:
                        
                        self._SetFocusedMedia( None )
                        
                    
                    self._shift_focused_media = None
                    
                else:
                    
                    self._DeselectSelect( (), ( media, ) )
                    
                    if self._focused_media is None: self._SetFocusedMedia( media )
                    
                    self._shift_focused_media = media
                    
                
            elif shift and self._shift_focused_media is not None:
                
                start_index = self._sorted_media.index( self._shift_focused_media )
                
                end_index = self._sorted_media.index( media )
                
                if start_index < end_index: media_to_select = set( self._sorted_media[ start_index : end_index + 1 ] )
                else: media_to_select = set( self._sorted_media[ end_index : start_index + 1 ] )
                
                self._DeselectSelect( (), media_to_select )
                
                self._SetFocusedMedia( media )
                
                self._shift_focused_media = media
                
            else:
                
                if not media.IsSelected():
                    
                    self._DeselectSelect( self._selected_media, ( media, ) )
                    
                else:
                    
                    self._PublishSelectionChange()
                    
                
                self._SetFocusedMedia( media )
                self._shift_focused_media = media
                
            
        
    
    def _Inbox( self ):
        
        hashes = self._GetSelectedHashes( discriminant = CC.DISCRIMINANT_ARCHIVE )
        
        if len( hashes ) > 0:
            
            if HC.options[ 'confirm_archive' ]:
                
                if len( hashes ) > 1:
                    
                    message = 'Send {} files to inbox?'.format( HydrusData.ToHumanInt( len( hashes ) ) )
                    
                    result = ClientGUIDialogsQuick.GetYesNo( self, message )
                    
                    if result != QW.QDialog.Accepted:
                        
                        return
                        
                    
                
            
            HG.client_controller.Write( 'content_updates', { CC.COMBINED_LOCAL_FILE_SERVICE_KEY: [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_INBOX, hashes ) ] } )
            
        
    
    def _ManageNotes( self ):
        
        def qt_do_it( media, notes ):
            
            if not self or not QP.isValid( self ):
                
                return
                
            
            title = 'manage notes'
            
            with ClientGUITopLevelWindows.DialogEdit( self, title ) as dlg:
                
                panel = ClientGUIScrolledPanels.EditSingleCtrlPanel( dlg, [ 'manage_file_notes' ] )
                
                control = QW.QPlainTextEdit( panel )
                
                ( width, height ) = ClientGUIFunctions.ConvertTextToPixels( control, ( 80, 14 ) )
                
                control.setMinimumWidth( width )
                control.setMinimumHeight( height )
                
                control.setPlainText( notes )
                
                panel.SetControl( control )
                
                dlg.SetPanel( panel )
                
                QP.CallAfter( control.setFocus, QC.Qt.OtherFocusReason )
                QP.CallAfter( control.moveCursor, QG.QTextCursor.End )
                
                if dlg.exec() == QW.QDialog.Accepted:
                    
                    notes = control.toPlainText()
                    
                    hash = media.GetHash()
                    
                    content_updates = [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_NOTES, HC.CONTENT_UPDATE_SET, ( notes, hash ) ) ]
                    
                    service_keys_to_content_updates = { CC.LOCAL_NOTES_SERVICE_KEY : content_updates }
                    
                    HG.client_controller.Write( 'content_updates', service_keys_to_content_updates )
                    
                
            
            self.setFocus( QC.Qt.OtherFocusReason )
            
        
        def thread_wait( media ):
            
            # if it ultimately makes sense, I can load/cache notes in the media result
            
            notes = HG.client_controller.Read( 'file_notes', media.GetHash() )
            
            QP.CallAfter( qt_do_it, media, notes )
            
        
        if self._focused_media is None:
            
            return
            
        
        HG.client_controller.CallToThread( thread_wait, self._focused_media.GetDisplayMedia() )
        
    
    def _ManageRatings( self ):
        
        if len( self._selected_media ) > 0:
            
            if len( HG.client_controller.services_manager.GetServices( HC.RATINGS_SERVICES ) ) > 0:
                
                flat_media = self._GetSelectedFlatMedia()
                
                with ClientGUIDialogsManage.DialogManageRatings( self, flat_media ) as dlg:
                    
                    dlg.exec()
                    
                
                self.setFocus( QC.Qt.OtherFocusReason )
                
            
        
    
    def _ManageTags( self ):
        
        if len( self._selected_media ) > 0:
            
            num_files = self._GetNumSelected()
            
            title = 'manage tags for ' + HydrusData.ToHumanInt( num_files ) + ' files'
            frame_key = 'manage_tags_dialog'
            
            with ClientGUITopLevelWindows.DialogManage( self, title, frame_key ) as dlg:
                
                panel = ClientGUITags.ManageTagsPanel( dlg, self._file_service_key, self._selected_media )
                
                dlg.SetPanel( panel )
                
                dlg.exec()
                
            
            self.setFocus( QC.Qt.OtherFocusReason )
            
        
    
    def _ManageURLs( self ):
        
        if len( self._selected_media ) > 0:
            
            num_files = self._GetNumSelected()
            
            title = 'manage urls for {} files'.format( num_files )
            
            with ClientGUITopLevelWindows.DialogManage( self, title ) as dlg:
                
                panel = ClientGUIScrolledPanelsManagement.ManageURLsPanel( dlg, self._selected_media )
                
                dlg.SetPanel( panel )
                
                dlg.exec()
                
            
            self.setFocus( QC.Qt.OtherFocusReason )
            
        
    
    def _MediaIsVisible( self, media ):
        
        return True
        
    
    def _ModifyUploaders( self, file_service_key ):
        
        QW.QMessageBox.information( self, 'Information', 'this does not work yet!' )
        
        return
        
        hashes = self._GetSelectedHashes()
        
        if hashes is not None and len( hashes ) > 0:   
            
            contents = [ HydrusNetwork.Content( HC.CONTENT_TYPE_FILES, [ hash ] ) for hash in hashes ]
            
            subject_accounts = 'blah' # fetch subjects from server with the contents
            
            with ClientGUIDialogs.DialogModifyAccounts( self, file_service_key, subject_accounts ) as dlg: dlg.exec()
            
            self.setFocus( QC.Qt.OtherFocusReason )
            
        
    
    def _OpenExternally( self ):
        
        if self._focused_media is not None:
            
            open_externally_media = self._focused_media.GetDisplayMedia()
            
            if open_externally_media.GetLocationsManager().IsLocal():
                
                hash = open_externally_media.GetHash()
                mime = open_externally_media.GetMime()
                
                client_files_manager = HG.client_controller.client_files_manager
                
                path = client_files_manager.GetFilePath( hash, mime )
                
                new_options = HG.client_controller.new_options
                
                launch_path = new_options.GetMimeLaunch( mime )
                
                HydrusPaths.LaunchFile( path, launch_path )
                
                HG.client_controller.pub( 'media_focus_went_to_external_program', self._page_key )
                
            
        
    
    def _OpenFileInWebBrowser( self ):
        
        if self._focused_media is not None:
            
            if self._focused_media.GetLocationsManager().IsLocal():
                
                hash = self._focused_media.GetHash()
                mime = self._focused_media.GetMime()
                
                client_files_manager = HG.client_controller.client_files_manager
                
                path = client_files_manager.GetFilePath( hash, mime )
                
                self._SetFocusedMedia( None )
                
                ClientPaths.LaunchPathInWebBrowser( path )
                
            
        
    
    def _OpenFileLocation( self ):
        
        if self._focused_media is not None:
            
            if self._focused_media.GetLocationsManager().IsLocal():
                
                hash = self._focused_media.GetHash()
                mime = self._focused_media.GetMime()
                
                client_files_manager = HG.client_controller.client_files_manager
                
                path = client_files_manager.GetFilePath( hash, mime )
                
                self._SetFocusedMedia( None )
                
                HydrusPaths.OpenFileLocation( path )
                
            
        
    
    def _OpenKnownURL( self ):
        
        if self._focused_media is not None:
            
            DoOpenKnownURLFromShortcut( self, self._focused_media )
            
        
    
    def _PetitionFiles( self, remote_service_key ):
        
        hashes = self._GetSelectedHashes()
        
        if hashes is not None and len( hashes ) > 0:
            
            remote_service = HG.client_controller.services_manager.GetService( remote_service_key )
            
            service_type = remote_service.GetServiceType()
            
            if service_type == HC.FILE_REPOSITORY:
                
                if len( hashes ) == 1:
                    
                    message = 'Enter a reason for this file to be removed from ' + remote_service.GetName() + '.'
                    
                else:
                    
                    message = 'Enter a reason for these ' + HydrusData.ToHumanInt( len( hashes ) ) + ' files to be removed from ' + remote_service.GetName() + '.'
                    
                
                with ClientGUIDialogs.DialogTextEntry( self, message ) as dlg:
                    
                    if dlg.exec() == QW.QDialog.Accepted:
                        
                        reason = dlg.GetValue()
                        
                        content_update = HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_PETITION, hashes, reason = reason )
                        
                        service_keys_to_content_updates = { remote_service_key : ( content_update, ) }
                        
                        HG.client_controller.Write( 'content_updates', service_keys_to_content_updates )
                        
                    
                
                self.setFocus( QC.Qt.OtherFocusReason )
                
            elif service_type == HC.IPFS:
                
                content_update = HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_PETITION, hashes, reason = 'ipfs' )
                
                service_keys_to_content_updates = { remote_service_key : ( content_update, ) }
                
                HG.client_controller.Write( 'content_updates', service_keys_to_content_updates )
                
            
        
    
    def _PublishSelectionChange( self, force_reload = False ):
        
        if HG.client_controller.gui.IsCurrentPage( self._page_key ):
            
            if len( self._selected_media ) == 0:
                
                tags_media = self._sorted_media
                
            else:
                
                tags_media = self._selected_media
                
            
            force_reload = force_reload or self._due_a_forced_selection_pub
            
            HG.client_controller.pub( 'new_tags_selection', self._page_key, tags_media, force_reload = force_reload )
            HG.client_controller.pub( 'new_page_status', self._page_key, self._GetPrettyStatus() )
            
            if force_reload:
                
                self._due_a_forced_selection_pub = False
                
            
        else:
            
            if force_reload:
                
                self._due_a_forced_selection_pub = True
                
            
        
    
    def _PublishSelectionIncrement( self, medias ):
        
        if HG.client_controller.gui.IsCurrentPage( self._page_key ):
            
            HG.client_controller.pub( 'increment_tags_selection', self._page_key, medias )
            HG.client_controller.pub( 'new_page_status', self._page_key, self._GetPrettyStatus() )
            
        else:
            
            self._due_a_forced_selection_pub = True
            
        
    
    def _RecalculateVirtualSize( self ): pass
    
    def _RedrawMedia( self, media ): pass
    
    def _Remove( self, file_filter ):
        
        hashes = self.GetFilteredHashes( file_filter )
        
        if len( hashes ) > 0:
            
            self._RemoveMediaByHashes( hashes )
            
        
    
    def _RegenerateFileData( self, job_type ):
        
        flat_media = self._GetSelectedFlatMedia()
        
        num_files = len( flat_media )
        
        if num_files > 0:
            
            if job_type == ClientFiles.REGENERATE_FILE_DATA_JOB_FILE_METADATA:
                
                text = 'This will reparse the {} selected files\' metadata.'.format( HydrusData.ToHumanInt( num_files ) )
                text += os.linesep * 2
                text += 'If the files were imported before some more recent improvement in the parsing code (such as EXIF rotation or bad video resolution or duration or frame count calculation), this will update them.'
                
            elif job_type == ClientFiles.REGENERATE_FILE_DATA_JOB_FORCE_THUMBNAIL:
                
                text = 'This will force-regenerate the {} selected files\' thumbnails.'.format( HydrusData.ToHumanInt( num_files ) )
                
            elif job_type == ClientFiles.REGENERATE_FILE_DATA_JOB_REFIT_THUMBNAIL:
                
                text = 'This will regenerate the {} selected files\' thumbnails, but only if they are the wrong size.'.format( HydrusData.ToHumanInt( num_files ) )
                
            
            do_it_now = True
            
            if num_files > 50:
                
                text += os.linesep * 2
                text += 'You have selected {} files, so this job may take some time. You can run it all now or schedule it to the overall file maintenance queue for later spread-out processing.'.format( HydrusData.ToHumanInt( num_files ) )
                
                yes_tuples = []
                
                yes_tuples.append( ( 'do it now', 'now' ) )
                yes_tuples.append( ( 'do it later', 'later' ) )
                
                with ClientGUIDialogs.DialogYesYesNo( self, text, yes_tuples = yes_tuples, no_label = 'forget it' ) as dlg:
                    
                    if dlg.exec() == QW.QDialog.Accepted:
                        
                        value = dlg.GetValue()
                        
                        if value == 'now':
                            
                            do_it_now = True
                            
                        elif value == 'later':
                            
                            do_it_now = False
                            
                        else:
                            
                            return
                            
                        
                    else:
                        
                        return
                        
                    
                
            else:
                
                result = ClientGUIDialogsQuick.GetYesNo( self, text )
                
                if result != QW.QDialog.Accepted:
                    
                    return
                    
                
            
            if do_it_now:
                
                self._SetFocusedMedia( None )
                
                time.sleep( 0.1 )
                
                HG.client_controller.CallToThread( HG.client_controller.files_maintenance_manager.RunJobImmediately, flat_media, job_type )
                
            else:
                
                hashes = { media.GetHash() for media in flat_media }
                
                HG.client_controller.CallToThread( HG.client_controller.files_maintenance_manager.ScheduleJob, hashes, job_type )
                
            
        
    
    def _RescindDownloadSelected( self ):
        
        hashes = self._GetSelectedHashes( discriminant = CC.DISCRIMINANT_NOT_LOCAL )
        
        HG.client_controller.Write( 'content_updates', { CC.COMBINED_LOCAL_FILE_SERVICE_KEY : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_RESCIND_PEND, hashes ) ] } )
        
    
    def _RescindPetitionFiles( self, file_service_key ):
        
        hashes = self._GetSelectedHashes()
        
        if hashes is not None and len( hashes ) > 0:   
            
            HG.client_controller.Write( 'content_updates', { file_service_key : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_RESCIND_PETITION, hashes ) ] } )
            
        
    
    def _RescindUploadFiles( self, file_service_key ):
        
        hashes = self._GetSelectedHashes()
        
        if hashes is not None and len( hashes ) > 0:   
            
            HG.client_controller.Write( 'content_updates', { file_service_key : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_RESCIND_PEND, hashes ) ] } )
            
        
    
    def _Select( self, file_filter ):
        
        matching_media = self.GetFilteredMedia( file_filter )
        
        media_to_deselect = self._selected_media.difference( matching_media )
        media_to_select = matching_media.difference( self._selected_media )
        
        move_focus = self._focused_media in media_to_deselect or self._focused_media is None
        
        if move_focus or self._shift_focused_media in media_to_deselect:
            
            self._shift_focused_media = None
            
        
        self._DeselectSelect( media_to_deselect, media_to_select )
        
        if move_focus:
            
            if len( self._selected_media ) == 0:
                
                self._SetFocusedMedia( None )
                
            else:
                
                # let's not focus if one of the selectees is already visible
                
                media_visible = True in ( self._MediaIsVisible( media ) for media in self._selected_media )
                
                if not media_visible:
                    
                    for m in self._sorted_media:
                        
                        if m in self._selected_media:
                            
                            ctrl = False
                            shift = False
                            
                            self._HitMedia( m, ctrl, shift )
                            
                            self._ScrollToMedia( m )
                            
                            break
                            
                        
                    
                
            
        
    
    def _SetCollectionsAsAlternate( self ):
        
        collections = self._GetSelectedCollections()
        
        if len( collections ) > 0:
            
            message = 'Are you sure you want to set files in the selected collections as alternates? Each collection will be considered a separate group of alternates.'
            message += os.linesep * 2
            message += 'Be careful applying this to large groups--any more than a few dozen files, and the client could hang a long time.'
            
            result = ClientGUIDialogsQuick.GetYesNo( self, message )
            
            if result == QW.QDialog.Accepted:
                
                for collection in collections:
                    
                    media_group = collection.GetFlatMedia()
                    
                    self._SetDuplicates( HC.DUPLICATE_ALTERNATE, media_group = media_group, silent = True )
                    
                
            
        
    
    def _SetDuplicates( self, duplicate_type, media_pairs = None, media_group = None, duplicate_action_options = None, silent = False ):
        
        yes_no_text = 'unknown duplicate action'
        
        if duplicate_type == HC.DUPLICATE_POTENTIAL:
            
            yes_no_text = 'queue all possible and valid pair combinations into the duplicate filter'
            
        elif duplicate_action_options is None:
            
            yes_no_text = 'apply "{}"'.format( HC.duplicate_type_string_lookup[ duplicate_type ] )
            
            if duplicate_type in [ HC.DUPLICATE_BETTER, HC.DUPLICATE_SAME_QUALITY ] or ( HG.client_controller.new_options.GetBoolean( 'advanced_mode' ) and duplicate_type == HC.DUPLICATE_ALTERNATE ):
                
                yes_no_text += ' (with default duplicate metadata merge options)'
                
                new_options = HG.client_controller.new_options
                
                duplicate_action_options = new_options.GetDuplicateActionOptions( duplicate_type )
                
            
        else:
            
            yes_no_text = 'apply "{}" (with custom duplicate metadata merge options)'.format( HC.duplicate_type_string_lookup[ duplicate_type ] )
            
        
        file_deletion_reason = 'Deleted from duplicate action on Media Page ({}).'.format( yes_no_text )
        
        if media_pairs is None:
            
            if media_group is None:
                
                flat_media = self._GetSelectedFlatMedia()
                
            else:
                
                flat_media = ClientMedia.FlattenMedia( media_group )
                
            
            if len( flat_media ) < 2:
                
                return False
                
            
            if duplicate_type in ( HC.DUPLICATE_FALSE_POSITIVE, HC.DUPLICATE_ALTERNATE, HC.DUPLICATE_POTENTIAL ):
                
                media_pairs = list( itertools.combinations( flat_media, 2 ) )
                
            else:
                
                first_media = flat_media[0]
                
                media_pairs = [ ( first_media, other_media ) for other_media in flat_media if other_media != first_media ]
                
            
        
        if len( media_pairs ) == 0:
            
            return False
            
        
        if not silent:
            
            yes_label = 'yes'
            no_label = 'no'
            
            if len( media_pairs ) > 100 and duplicate_type in ( HC.DUPLICATE_FALSE_POSITIVE, HC.DUPLICATE_ALTERNATE ):
                
                if duplicate_type == HC.DUPLICATE_FALSE_POSITIVE:
                    
                    message = 'False positive records are complicated, and setting that relationship for many files at once is likely a mistake.'
                    message += os.linesep * 2
                    message += 'Are you sure all of these files are all potential duplicates and that they are all false positive matches with each other? If not, I recommend you step back for now.'
                    
                    yes_label = 'I know what I am doing'
                    no_label = 'step back for now'
                    
                elif duplicate_type == HC.DUPLICATE_ALTERNATE:
                    
                    message = 'Are you certain all these files are alternates with every other member of the selection, and that none are duplicates?'
                    message += os.linesep * 2
                    message += 'If some of them may be duplicates, I recommend you either deselect the possible duplicates and try again, or just leave this group to be processed in the normal duplicate filter.'
                    
                    yes_label = 'they are all alternates'
                    no_label = 'some may be duplicates'
                    
                
            else:
                
                message = 'Are you sure you want to ' + yes_no_text + ' for the selected files?'
                
            
            result = ClientGUIDialogsQuick.GetYesNo( self, message, yes_label = yes_label, no_label = no_label )
            
            if result != QW.QDialog.Accepted:
                
                return False
                
            
        
        pair_info = []
        
        for ( first_media, second_media ) in media_pairs:
            
            first_hash = first_media.GetHash()
            second_hash = second_media.GetHash()
            
            if duplicate_action_options is None:
                
                service_keys_to_content_updates = {}
                
            else:
                
                service_keys_to_content_updates = duplicate_action_options.ProcessPairIntoContentUpdates( first_media, second_media, file_deletion_reason = file_deletion_reason )
                
            
            pair_info.append( ( duplicate_type, first_hash, second_hash, service_keys_to_content_updates ) )
            
        
        if len( pair_info ) > 0:
            
            HG.client_controller.WriteSynchronous( 'duplicate_pair_status', pair_info )
            
            return True
            
        
        return False
        
    
    def _SetDuplicatesCustom( self ):
        
        duplicate_types = [ HC.DUPLICATE_BETTER, HC.DUPLICATE_SAME_QUALITY ]
        
        if HG.client_controller.new_options.GetBoolean( 'advanced_mode' ):
            
            duplicate_types.append( HC.DUPLICATE_ALTERNATE )
            
        
        choice_tuples = [ ( HC.duplicate_type_string_lookup[ duplicate_type ], duplicate_type ) for duplicate_type in duplicate_types ]
        
        try:
            
            duplicate_type = ClientGUIDialogsQuick.SelectFromList( self, 'select duplicate type', choice_tuples )
            
        except HydrusExceptions.CancelledException:
            
            return
            
        
        new_options = HG.client_controller.new_options
        
        duplicate_action_options = new_options.GetDuplicateActionOptions( duplicate_type )
        
        with ClientGUITopLevelWindows.DialogEdit( self, 'edit duplicate merge options' ) as dlg:
            
            panel = ClientGUIScrolledPanelsEdit.EditDuplicateActionOptionsPanel( dlg, duplicate_type, duplicate_action_options, for_custom_action = True )
            
            dlg.SetPanel( panel )
            
            if dlg.exec() == QW.QDialog.Accepted:
                
                duplicate_action_options = panel.GetValue()
                
                self._SetDuplicates( duplicate_type, duplicate_action_options = duplicate_action_options )
                
            
        
    
    def _SetDuplicatesFocusedBetter( self, duplicate_action_options = None ):
        
        flat_media = self._GetSelectedFlatMedia()
        
        if self._focused_media is None:
            
            QW.QMessageBox.warning( self, 'Warning', 'No file is focused, so cannot set the focused file as better!' )
            
            return
            
        
        focused_hash = self._focused_media.GetDisplayMedia().GetHash()
        
        ( better_media, ) = [ media for media in flat_media if media.GetHash() == focused_hash ]
        
        worse_flat_media = [ media for media in flat_media if media.GetHash() != focused_hash ]
        
        media_pairs = [ ( better_media, worse_media ) for worse_media in worse_flat_media ]
        
        self._SetDuplicates( HC.DUPLICATE_BETTER, media_pairs = media_pairs )
        
    
    def _SetDuplicatesFocusedKing( self ):
        
        if self._focused_media is None:
            
            QW.QMessageBox.warning( self, 'Warning', 'No file is focused, so cannot set the focused file as king!' )
            
            return
            
        
        focused_hash = self._focused_media.GetDisplayMedia().GetHash()
        
        HG.client_controller.WriteSynchronous( 'duplicate_set_king', focused_hash )
        
    
    def _SetDuplicatesPotential( self ):
        
        media_group = self._GetSelectedFlatMedia()
        
        self._SetDuplicates( HC.DUPLICATE_POTENTIAL, media_group = media_group )
        
    
    def _SetFocusedMedia( self, media ):
        
        if media is None and self._focused_media is not None:
            
            next_best_media = self._focused_media
            
            i = self._sorted_media.index( next_best_media )
            
            while next_best_media in self._selected_media:
                
                if i == 0:
                    
                    next_best_media = None
                    
                    break
                    
                
                i -= 1
                
                next_best_media = self._sorted_media[ i ]
                
            
            self._next_best_media_after_focused_media_removed = next_best_media
            
        else:
            
            self._next_best_media_after_focused_media_removed = None
            
        
        self._focused_media = media
        
        if self._focused_media is None:
            
            publish_media = None
            
        else:
            
            publish_media = self._focused_media.GetDisplayMedia()
            
        
        HG.client_controller.pub( 'preview_changed', self._page_key, publish_media )
        
    
    def _ScrollToMedia( self, media ):
        
        pass
        
    
    def _ShareOnLocalBooru( self ):
        
        if len( self._selected_media ) > 0:
            
            share_key = HydrusData.GenerateKey()
            
            name = ''
            text = ''
            timeout = HydrusData.GetNow() + 60 * 60 * 24
            hashes = self._GetSelectedHashes()
            
            with ClientGUIDialogs.DialogInputLocalBooruShare( self, share_key, name, text, timeout, hashes, new_share = True ) as dlg:
                
                if dlg.exec() == QW.QDialog.Accepted:
                    
                    ( share_key, name, text, timeout, hashes ) = dlg.GetInfo()
                    
                    info = {}
                    
                    info[ 'name' ] = name
                    info[ 'text' ] = text
                    info[ 'timeout' ] = timeout
                    info[ 'hashes' ] = hashes
                    
                    HG.client_controller.Write( 'local_booru_share', share_key, info )
                    
                
            
            self.setFocus( QC.Qt.OtherFocusReason )
            
        
    
    def _ShowDuplicatesInNewPage( self, hash, duplicate_type ):
        
        hashes = HG.client_controller.Read( 'file_duplicate_hashes', self._file_service_key, hash, duplicate_type )
        
        if hashes is not None and len( hashes ) > 0:
            
            HG.client_controller.pub( 'new_page_query', self._file_service_key, initial_hashes = hashes )
            
        
    
    def _ShowSelectionInNewPage( self ):
        
        hashes = self._GetSelectedHashes( ordered = True )
        
        if hashes is not None and len( hashes ) > 0:
            
            HG.client_controller.pub( 'new_page_query', self._file_service_key, initial_hashes = hashes )
            
        
    
    def _Undelete( self ):
        
        hashes = self._GetSelectedHashes( has_location = CC.TRASH_SERVICE_KEY )
        
        num_to_undelete = len( hashes )
        
        if num_to_undelete > 0:
            
            do_it = False
            
            if not HC.options[ 'confirm_trash' ]:
                
                do_it = True
                
            else:
                
                if num_to_undelete == 1:
                    
                    message = 'Are you sure you want to undelete this file?'
                    
                else:
                    
                    message = 'Are you sure you want to undelete these ' + HydrusData.ToHumanInt( num_to_undelete ) + ' files?'
                    
                
                result = ClientGUIDialogsQuick.GetYesNo( self, message )
                
                if result == QW.QDialog.Accepted:
                    
                    do_it = True
                    
                
            
            if do_it:
                
                HG.client_controller.Write( 'content_updates', { CC.TRASH_SERVICE_KEY : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_UNDELETE, hashes ) ] } )
                
            
        
    
    def _UpdateBackgroundColour( self ):
        
        self.widget().update()
        
    
    def _UploadDirectory( self, file_service_key ):
        
        hashes = self._GetSelectedHashes()
        
        if hashes is not None and len( hashes ) > 0:
            
            ipfs_service = HG.client_controller.services_manager.GetService( file_service_key )
            
        
        with ClientGUIDialogs.DialogTextEntry( self, 'Enter a note to describe this directory.' ) as dlg:
            
            if dlg.exec() == QW.QDialog.Accepted:
                
                note = dlg.GetValue()
                
                HG.client_controller.CallToThread( ipfs_service.PinDirectory, hashes, note )
                
            
        
    
    def _UploadFiles( self, file_service_key ):
        
        hashes = self._GetSelectedHashes( not_uploaded_to = file_service_key )
        
        if hashes is not None and len( hashes ) > 0:   
            
            HG.client_controller.Write( 'content_updates', { file_service_key : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_PEND, hashes ) ] } )
            
        
    
    def AddMediaResults( self, page_key, media_results ):
        
        if page_key == self._page_key:
            
            HG.client_controller.pub( 'refresh_page_name', self._page_key )
            
            return ClientMedia.ListeningMediaList.AddMediaResults( self, media_results )
            
        
    
    def ClearPageKey( self ):
        
        self._page_key = 'dead media panel page key'
        
    
    def Collect( self, page_key, media_collect = None ):
        
        if page_key == self._page_key:
            
            self._Select( ClientMedia.FileFilter( ClientMedia.FILE_FILTER_NONE ) )
            
            ClientMedia.ListeningMediaList.Collect( self, media_collect )
            
            self._RecalculateVirtualSize()
            
            # no refresh needed since the sort call that always comes after will do it
            
        
    
    def FileDumped( self, page_key, hash, status ):
        
        if page_key == self._page_key:
            
            media = self._GetMedia( { hash } )
            
            for m in media: m.Dumped( status )
            
            self._RedrawMedia( media )
            
        
    
    def PageHidden( self ):
        
        HG.client_controller.pub( 'preview_changed', self._page_key, None )
        
    
    def PageShown( self ):
        
        if self._focused_media is None:
            
            publish_media = None
            
        else:
            
            publish_media = self._focused_media.GetDisplayMedia()
            
        
        HG.client_controller.pub( 'preview_changed', self._page_key, publish_media )
        
        self._PublishSelectionChange()
        
    
    def ProcessApplicationCommand( self, command ):
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'copy_bmp':
                
                self._CopyBMPToClipboard()
                
            elif action == 'copy_file':
                
                self._CopyFilesToClipboard()
                
            elif action == 'copy_path':
                
                self._CopyPathsToClipboard()
                
            elif action == 'copy_sha256_hash':
                
                self._CopyHashesToClipboard( 'sha256' )
                
            elif action == 'duplicate_media_clear_focused_false_positives':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.ClearFalsePositives( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_clear_false_positives':
                
                hashes = self._GetSelectedHashes()
                
                if len( hashes ) > 0:
                    
                    ClientGUIDuplicates.ClearFalsePositives( self, hashes )
                    
                
            elif action == 'duplicate_media_dissolve_focused_alternate_group':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.DissolveAlternateGroup( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_dissolve_alternate_group':
                
                hashes = self._GetSelectedHashes()
                
                if len( hashes ) > 0:
                    
                    ClientGUIDuplicates.DissolveAlternateGroup( self, hashes )
                    
                
            elif action == 'duplicate_media_dissolve_focused_duplicate_group':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.DissolveDuplicateGroup( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_dissolve_duplicate_group':
                
                hashes = self._GetSelectedHashes()
                
                if len( hashes ) > 0:
                    
                    ClientGUIDuplicates.DissolveDuplicateGroup( self, hashes )
                    
                
            elif action == 'duplicate_media_remove_focused_from_alternate_group':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.RemoveFromAlternateGroup( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_remove_focused_from_duplicate_group':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.RemoveFromDuplicateGroup( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_reset_focused_potential_search':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.ResetPotentialSearch( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_reset_potential_search':
                
                hashes = self._GetSelectedHashes()
                
                if len( hashes ) > 0:
                    
                    ClientGUIDuplicates.ResetPotentialSearch( self, hashes )
                    
                
            elif action == 'duplicate_media_remove_focused_potentials':
                
                if self._focused_media is not None:
                    
                    hash = self._focused_media.GetDisplayMedia().GetHash()
                    
                    ClientGUIDuplicates.RemovePotentials( self, ( hash, ) )
                    
                
            elif action == 'duplicate_media_remove_potentials':
                
                hashes = self._GetSelectedHashes()
                
                if len( hashes ) > 0:
                    
                    ClientGUIDuplicates.RemovePotentials( self, hashes )
                    
                
            elif action == 'duplicate_media_set_alternate':
                
                self._SetDuplicates( HC.DUPLICATE_ALTERNATE )
                
            elif action == 'duplicate_media_set_alternate_collections':
                
                self._SetCollectionsAsAlternate()
                
            elif action == 'duplicate_media_set_custom':
                
                self._SetDuplicatesCustom()
                
            elif action == 'duplicate_media_set_focused_better':
                
                self._SetDuplicatesFocusedBetter()
                
            elif action == 'duplicate_media_set_focused_king':
                
                self._SetDuplicatesFocusedKing()
                
            elif action == 'duplicate_media_set_potential':
                
                self._SetDuplicatesPotential()
                
            elif action == 'duplicate_media_set_same_quality':
                
                self._SetDuplicates( HC.DUPLICATE_SAME_QUALITY )
                
            elif action == 'export_files':
                
                self._ExportFiles()
                
            elif action == 'export_files_quick_auto_export':
                
                self._ExportFiles( do_export_and_then_quit = True )
                
            elif action == 'manage_file_ratings':
                
                self._ManageRatings()
                
            elif action == 'manage_file_tags':
                
                self._ManageTags()
                
            elif action == 'manage_file_urls':
                
                self._ManageURLs()
                
            elif action == 'manage_file_notes':
                
                self._ManageNotes()
                
            elif action == 'open_known_url':
                
                self._OpenKnownURL()
                
            elif action == 'archive_file':
                
                self._Archive()
                
            elif action == 'delete_file':
                
                self._Delete()
                
            elif action == 'inbox_file':
                
                self._Inbox()
                
            elif action == 'remove_file_from_view':
                
                self._Remove( ClientMedia.FileFilter( ClientMedia.FILE_FILTER_SELECTED ) )
                
            elif action == 'get_similar_to_exact':
                
                self._GetSimilarTo( HC.HAMMING_EXACT_MATCH )
                
            elif action == 'get_similar_to_very_similar':
                
                self._GetSimilarTo( HC.HAMMING_VERY_SIMILAR )
                
            elif action == 'get_similar_to_similar':
                
                self._GetSimilarTo( HC.HAMMING_SIMILAR )
                
            elif action == 'get_similar_to_speculative':
                
                self._GetSimilarTo( HC.HAMMING_SPECULATIVE )
                
            elif action == 'open_file_in_external_program':
                
                self._OpenExternally()
                
            elif action == 'open_selection_in_new_page':
                
                self._ShowSelectionInNewPage()
                
            elif action == 'launch_the_archive_delete_filter':
                
                self._ArchiveDeleteFilter()
                
            else:
                
                command_processed = False
                
            
        elif command_type == CC.APPLICATION_COMMAND_TYPE_CONTENT:
            
            command_processed = ClientGUIFunctions.ApplyContentApplicationCommandToMedia( self, command, self._GetSelectedFlatMedia() )
            
        else:
            
            command_processed = False
            
        
        return command_processed
        
    
    def ProcessContentUpdates( self, service_keys_to_content_updates ):
        
        ClientMedia.ListeningMediaList.ProcessContentUpdates( self, service_keys_to_content_updates )
        
        we_were_file_or_tag_affected = False
        
        for ( service_key, content_updates ) in list(service_keys_to_content_updates.items()):
            
            for content_update in content_updates:
                
                hashes = content_update.GetHashes()
                
                if self._HasHashes( hashes ):
                    
                    affected_media = self._GetMedia( hashes )
                    
                    self._RedrawMedia( affected_media )
                    
                    if content_update.GetDataType() in ( HC.CONTENT_TYPE_FILES, HC.CONTENT_TYPE_MAPPINGS ):
                        
                        we_were_file_or_tag_affected = True
                        
                    
                
            
        
        if we_were_file_or_tag_affected:
            
            self._PublishSelectionChange( force_reload = True )
            
        
    
    def ProcessServiceUpdates( self, service_keys_to_service_updates ):
        
        ClientMedia.ListeningMediaList.ProcessServiceUpdates( self, service_keys_to_service_updates )
        
        for ( service_key, service_updates ) in list(service_keys_to_service_updates.items()):
            
            for service_update in service_updates:
                
                ( action, row ) = service_update.ToTuple()
                
                if action in ( HC.SERVICE_UPDATE_DELETE_PENDING, HC.SERVICE_UPDATE_RESET ):
                    
                    self._RecalculateVirtualSize()
                    
                
                self._PublishSelectionChange( force_reload = True )
                
            
        
    
    def RemoveMedia( self, page_key, hashes ):
        
        if page_key == self._page_key:
            
            self._RemoveMediaByHashes( hashes )
            
        
    
    def SelectByTags( self, page_key, and_or_or, tags ):
        
        if page_key == self._page_key:
            
            self._Select( ClientMedia.FileFilter( ClientMedia.FILE_FILTER_TAGS, ( and_or_or, tags ) ) )
            
        
    
    def SetDuplicateStatusForAll( self, duplicate_type ):
        
        media_group = ClientMedia.FlattenMedia( self._sorted_media )
        
        return self._SetDuplicates( duplicate_type, media_group = media_group )
        
    
    def SetFocusedMedia( self, page_key, media ):
        
        pass
        
    
    def Sort( self, page_key, media_sort = None ):
        
        if page_key == self._page_key:
            
            ClientMedia.ListeningMediaList.Sort( self, media_sort )
            
        
    
class MediaPanelLoading( MediaPanel ):
    
    def __init__( self, parent, page_key, file_service_key ):
        
        self._current = None
        self._max = None
        
        MediaPanel.__init__( self, parent, page_key, file_service_key, [] )
        
        HG.client_controller.sub( self, 'SetNumQueryResults', 'set_num_query_results' )
        
    
    def _GetPrettyStatus( self ):
        
        s = 'Loading\u2026'
        
        if self._current is not None:
            
            s += ' ' + HydrusData.ToHumanInt( self._current )
            
            if self._max is not None:
                
                s += ' of ' + HydrusData.ToHumanInt( self._max )
                
            
        
        return s
        
    
    def GetSortedMedia( self ):
        
        return []
        
    
    def SetNumQueryResults( self, page_key, num_current, num_max ):
        
        if page_key == self._page_key:
            
            self._current = num_current
            
            self._max = num_max
            
            self._PublishSelectionChange()
            
        
    
class MediaPanelThumbnails( MediaPanel ):
    
    def __init__( self, parent, page_key, file_service_key, media_results ):
        
        self._clean_canvas_pages = {}
        self._dirty_canvas_pages = []
        self._num_rows_per_canvas_page = 1
        self._num_rows_per_actual_page = 1
        
        MediaPanel.__init__( self, parent, page_key, file_service_key, media_results )
        
        self._last_client_size = ( 20, 20 )
        self._num_columns = 1
        
        self._drag_init_coordinates = None
        self._thumbnails_being_faded_in = {}
        self._hashes_faded = set()
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        thumbnail_scroll_rate = float( HG.client_controller.new_options.GetString( 'thumbnail_scroll_rate' ) )
        
        self.setWidget( MediaPanelThumbnails._InnerWidget( self ) )
        self.setWidgetResizable( True )
        
        self.verticalScrollBar().setSingleStep( int( round( thumbnail_span_height * thumbnail_scroll_rate ) ) )
        
        self._widget_event_filter = QP.WidgetEventFilter( self.widget() )
        self._widget_event_filter.EVT_LEFT_DCLICK( self.EventMouseFullScreen )
        self._widget_event_filter.EVT_MIDDLE_DOWN( self.EventMouseFullScreen )
        
        # notice this is on widget, not myself. fails to set up scrollbars if just moved up
        self._widget_event_filter.EVT_SIZE( self.EventResize )
        
        self._widget_event_filter.EVT_KEY_DOWN( self.EventKeyDown )
        
        self.widget().setMinimumSize( 50, 50 )
        
        self.RefreshAcceleratorTable()
        
        self._UpdateScrollBars()
        
        HG.client_controller.sub( self, 'MaintainPageCache', 'memory_maintenance_pulse' )
        HG.client_controller.sub( self, 'NotifyNewFileInfo', 'new_file_info' )
        HG.client_controller.sub( self, 'NewThumbnails', 'new_thumbnails' )
        HG.client_controller.sub( self, 'ThumbnailsReset', 'notify_complete_thumbnail_reset' )
        HG.client_controller.sub( self, 'RedrawAllThumbnails', 'refresh_all_tag_presentation_gui' )
        HG.client_controller.sub( self, 'RefreshAcceleratorTable', 'notify_new_options' )
        HG.client_controller.sub( self, 'WaterfallThumbnails', 'waterfall_thumbnails' )
        
    
    def _CalculateVisiblePageIndices( self ):
        
        y_start = self._GetYStart()
        
        earliest_y = y_start
        
        ( client_width, client_height ) = QP.ScrollAreaVisibleRect( self ).size().toTuple()
        
        last_y = earliest_y + client_height
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        page_height = self._num_rows_per_canvas_page * thumbnail_span_height
        
        first_visible_page_index = earliest_y // page_height
        
        last_visible_page_index = last_y // page_height
        
        page_indices = list( range( first_visible_page_index, last_visible_page_index + 1 ) )
        
        return page_indices
        
    
    def _CreateNewDirtyPage( self ):
        
        ( client_width, client_height ) = self.size().toTuple()
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        self._dirty_canvas_pages.append( HG.client_controller.bitmap_manager.GetQtImage( client_width, self._num_rows_per_canvas_page * thumbnail_span_height, 32 ) )
        
    
    def _DeleteAllDirtyPages( self ):
        
        self._dirty_canvas_pages = []
        
    
    def _DirtyAllPages( self ):
        
        clean_indices = list(self._clean_canvas_pages.keys())
        
        for clean_index in clean_indices:
            
            self._DirtyPage( clean_index )
            
        
    
    def _DirtyPage( self, clean_index ):

        canvas_page = self._clean_canvas_pages[ clean_index ]
        
        del self._clean_canvas_pages[ clean_index ]
        
        thumbnails = [ thumbnail for ( thumbnail_index, thumbnail ) in self._GetThumbnailsFromPageIndex( clean_index ) ]
        
        if len( thumbnails ) > 0:
            
            HG.client_controller.GetCache( 'thumbnail' ).CancelWaterfall( self._page_key, thumbnails )
            
        
        self._dirty_canvas_pages.append( canvas_page )
        
    
    def _DrawCanvasPage( self, page_index, canvas_page ):
        
        ( bmp_width, bmp_height ) = canvas_page.size().toTuple()
        
        painter = QG.QPainter( canvas_page )
        
        new_options = HG.client_controller.new_options
        
        bg_colour = HG.client_controller.new_options.GetColour( CC.COLOUR_THUMBGRID_BACKGROUND )
        
        if HG.thumbnail_debug_mode and page_index % 2 == 0:
            
            bg_colour = ClientData.GetLighterDarkerColour( bg_colour )
            
        
        if new_options.GetNoneableString( 'media_background_bmp_path' ) is not None:

            comp_mode = painter.compositionMode()
            
            painter.setCompositionMode( QG.QPainter.CompositionMode_Source )
            
            painter.setBackground( QG.QBrush( QC.Qt.transparent ) )

            painter.eraseRect( painter.viewport() )

            painter.setCompositionMode( comp_mode )
            
        else: 
        
            painter.setBackground( QG.QBrush( bg_colour ) )

            painter.eraseRect( painter.viewport() )
        
        #
        
        page_thumbnails = self._GetThumbnailsFromPageIndex( page_index )
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        thumbnails_to_render_later = []
        
        thumbnail_cache = HG.client_controller.GetCache( 'thumbnail' )
        
        thumbnail_margin = HG.client_controller.new_options.GetInteger( 'thumbnail_margin' )
        
        for ( thumbnail_index, thumbnail ) in page_thumbnails:
            
            hash = thumbnail.GetDisplayMedia().GetHash()
            
            if hash in self._hashes_faded and thumbnail_cache.HasThumbnailCached( thumbnail ):
                
                self._StopFading( hash )
                
                thumbnail_col = thumbnail_index % self._num_columns
                
                thumbnail_row = thumbnail_index // self._num_columns
                
                x = thumbnail_col * thumbnail_span_width + thumbnail_margin
                
                y = ( thumbnail_row - ( page_index * self._num_rows_per_canvas_page ) ) * thumbnail_span_height + thumbnail_margin
                
                painter.drawImage( x, y, thumbnail.GetQtImage() )
                
            else:
                
                thumbnails_to_render_later.append( thumbnail )
                
            
        
        if len( thumbnails_to_render_later ) > 0:
            
            HG.client_controller.GetCache( 'thumbnail' ).Waterfall( self._page_key, thumbnails_to_render_later )
            
        
    
    def _FadeThumbnails( self, thumbnails ):
        
        if len( thumbnails ) == 0:
            
            return
            
        
        self._hashes_faded.update( ( thumbnail.GetDisplayMedia().GetHash() for thumbnail in thumbnails ) )
        
        if not HG.client_controller.gui.IsCurrentPage( self._page_key ):
            
            self._DirtyAllPages()
            
            return
            
        
        now_precise = HydrusData.GetNowPrecise()
        
        for thumbnail in thumbnails:
            
            try:
                
                thumbnail_index = self._sorted_media.index( thumbnail )
                
            except HydrusExceptions.DataMissing:
                
                # probably means a collect happened during an ongoing waterfall or whatever
                
                return
                
            
            if self._GetPageIndexFromThumbnailIndex( thumbnail_index ) not in self._clean_canvas_pages:
                
                continue
                
            
            hash = thumbnail.GetDisplayMedia().GetHash()
            
            self._StopFading( hash )
            
            bmp = thumbnail.GetQtImage()
            
            alpha_bmp = QP.AdjustOpacity( bmp, 0.20 )
            
            self._thumbnails_being_faded_in[ hash ] = ( bmp, alpha_bmp, thumbnail_index, thumbnail, now_precise, 0 )
            
        
        HG.client_controller.gui.RegisterAnimationUpdateWindow( self )
        
    
    def _GenerateMediaCollection( self, media_results ):
        
        return ThumbnailMediaCollection( self._file_service_key, media_results )
        
    
    def _GenerateMediaSingleton( self, media_result ):
        
        return ThumbnailMediaSingleton( self._file_service_key, media_result )
        
    
    def _GetMediaCoordinates( self, media ):
        
        try: index = self._sorted_media.index( media )
        except: return ( -1, -1 )
        
        row = index // self._num_columns
        column = index % self._num_columns
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        thumbnail_margin = HG.client_controller.new_options.GetInteger( 'thumbnail_margin' )
        
        ( x, y ) = ( column * thumbnail_span_width + thumbnail_margin, row * thumbnail_span_height + thumbnail_margin )
        
        return ( x, y )
        
    
    def _GetPageIndexFromThumbnailIndex( self, thumbnail_index ):
        
        thumbnails_per_page = self._num_columns * self._num_rows_per_canvas_page
        
        page_index = thumbnail_index // thumbnails_per_page
        
        return page_index
        
    
    def _GetThumbnailSpanDimensions( self ):
        
        thumbnail_border = HG.client_controller.new_options.GetInteger( 'thumbnail_border' )
        thumbnail_margin = HG.client_controller.new_options.GetInteger( 'thumbnail_margin' )
        
        return ClientData.AddPaddingToDimensions( HC.options[ 'thumbnail_dimensions' ], ( thumbnail_border + thumbnail_margin ) * 2 )
        
    
    def _GetThumbnailUnderMouse( self, mouse_event ):
        
        x = mouse_event.pos().x()
        y = mouse_event.pos().y()
        
        ( t_span_x, t_span_y ) = self._GetThumbnailSpanDimensions()
        
        x_mod = x % t_span_x
        y_mod = y % t_span_y
        
        thumbnail_margin = HG.client_controller.new_options.GetInteger( 'thumbnail_margin' )
        
        if x_mod <= thumbnail_margin or y_mod <= thumbnail_margin or x_mod > t_span_x - thumbnail_margin or y_mod > t_span_y - thumbnail_margin:
            
            return None
            
        
        column_index = x // t_span_x
        row_index = y // t_span_y
        
        if column_index >= self._num_columns: return None
        
        thumbnail_index = self._num_columns * row_index + column_index
        
        if thumbnail_index >= len( self._sorted_media ): return None
        
        return self._sorted_media[ thumbnail_index ]
        
    
    def _GetThumbnailsFromPageIndex( self, page_index ):
        
        num_thumbnails_per_page = self._num_columns * self._num_rows_per_canvas_page
        
        start_index = num_thumbnails_per_page * page_index
        
        if start_index <= len( self._sorted_media ):
            
            end_index = min( len( self._sorted_media ), start_index + num_thumbnails_per_page )
            
            thumbnails = [ ( index, self._sorted_media[ index ] ) for index in range( start_index, end_index ) ]
            
        else:
            
            thumbnails = []
            
        
        return thumbnails
        
    
    def _GetYStart( self ):
        
        visible_rect = QP.ScrollAreaVisibleRect( self )
        
        visible_rect_y = visible_rect.y()
        
        visible_rect_height = visible_rect.height()
        
        my_virtual_size = self.widget().size()
        
        my_virtual_height = my_virtual_size.height()
        
        max_y = my_virtual_height - visible_rect_height
        
        y_start = max( 0, visible_rect_y )
        
        y_start = min( y_start, max_y )
        
        return y_start
        
    
    def _MediaIsInCleanPage( self, thumbnail ):
        
        try:
            
            index = self._sorted_media.index( thumbnail )
            
        except HydrusExceptions.DataMissing:
            
            return False
            
        
        if self._GetPageIndexFromThumbnailIndex( index ) in self._clean_canvas_pages:
            
            return True
            
        else:
            
            return False
            
        
    
    def _MediaIsVisible( self, media ):
        
        if media is not None:
            
            ( x, y ) = self._GetMediaCoordinates( media )
            
            visible_rect = QP.ScrollAreaVisibleRect( self )
            
            visible_rect_y = visible_rect.y()
            
            visible_rect_height = visible_rect.height()
            
            ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
            
            bottom_edge_below_top_of_view = visible_rect_y < y + thumbnail_span_height
            top_edge_above_bottom_of_view = y < visible_rect_y + visible_rect_height
            
            is_visible = bottom_edge_below_top_of_view and top_edge_above_bottom_of_view
            
            return is_visible
            
        
        return True
        
    
    def _MoveFocusedThumbnail( self, rows, columns, shift ):
        
        if self._focused_media is not None:
            
            media_to_use = self._focused_media
            
        elif self._next_best_media_after_focused_media_removed is not None:
            
            media_to_use = self._next_best_media_after_focused_media_removed
            
            if columns == -1: # treat it as if the focused area is between this and the next
                
                columns = 0
                
            
        elif len( self._sorted_media ) > 0:
            
            media_to_use = self._sorted_media[ 0 ]
            
        else:
            
            media_to_use = None
            
        
        if media_to_use is not None:
            
            current_position = self._sorted_media.index( media_to_use )
            
            new_position = current_position + columns + ( self._num_columns * rows )
            
            if new_position < 0:
                
                new_position = 0
                
            elif new_position > len( self._sorted_media ) - 1:
                
                new_position = len( self._sorted_media ) - 1
                
            
            new_media = self._sorted_media[ new_position ]
            
            self._HitMedia( new_media, False, shift )
            
            self._ScrollToMedia( new_media )
            
        
        
    
    def _RecalculateVirtualSize( self, called_from_resize_event = False ):
        
        ( client_width, client_height ) = QP.ScrollAreaVisibleRect( self ).size().toTuple()
        
        if client_width > 0 and client_height > 0:
            
            ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
            
            num_media = len( self._sorted_media )
            
            num_rows = max( 1, num_media // self._num_columns )
            
            if num_media % self._num_columns > 0:
                
                num_rows += 1
                
            
            virtual_width = client_width
            
            virtual_height = num_rows * thumbnail_span_height
            
            yUnit = self.verticalScrollBar().singleStep()
            
            excess = virtual_height % yUnit
            
            if excess > 0: # we want virtual height to fit exactly into scroll units, even if that puts some padding below bottom row
                
                top_up = yUnit - excess
                
                virtual_height += top_up
                
            
            virtual_height = max( virtual_height, client_height )
            
            if ( virtual_width, virtual_height ) != self.widget().size().toTuple():
                
                self.widget().resize( QC.QSize( virtual_width, virtual_height ) )
                
                if not called_from_resize_event:
                    
                    self._UpdateScrollBars() # would lead to infinite recursion if called from a resize event
                    
                
            
            return ( virtual_width, virtual_height )
            
        
        return ( 0, 0 )
        
    
    def _RedrawMedia( self, thumbnails ):
        
        visible_thumbnails = [ thumbnail for thumbnail in thumbnails if self._MediaIsInCleanPage( thumbnail ) ]
        
        thumbnail_cache = HG.client_controller.GetCache( 'thumbnail' )
        
        thumbnails_to_render_now = []
        thumbnails_to_render_later = []
        
        for thumbnail in visible_thumbnails:
            
            if thumbnail_cache.HasThumbnailCached( thumbnail ):
                
                thumbnails_to_render_now.append( thumbnail )
                
            else:
                
                thumbnails_to_render_later.append( thumbnail )
                
            
        
        if len( thumbnails_to_render_now ) > 0:
            
            self._FadeThumbnails( thumbnails_to_render_now )
            
        
        if len( thumbnails_to_render_later ) > 0:
            
            HG.client_controller.GetCache( 'thumbnail' ).Waterfall( self._page_key, thumbnails_to_render_later )
            
        
    
    def _ReinitialisePageCacheIfNeeded( self ):
        
        old_num_rows = self._num_rows_per_canvas_page
        old_num_columns = self._num_columns
        
        ( old_client_width, old_client_height ) = self._last_client_size
        
        ( client_width, client_height ) = QP.ScrollAreaVisibleRect( self ).size().toTuple()
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        num_rows = ( client_height // thumbnail_span_height )
        
        self._num_rows_per_actual_page = max( 1, num_rows )
        self._num_rows_per_canvas_page = max( 1, num_rows // 2 )
        
        self._num_columns = max( 1, client_width // thumbnail_span_width )
        
        client_dimensions_changed = old_client_width != client_width or old_client_height != client_height
        thumb_layout_changed = old_num_columns != self._num_columns or old_num_rows != self._num_rows_per_canvas_page
        
        if client_dimensions_changed or thumb_layout_changed:
            
            width_got_bigger = old_client_width < client_width
            
            if thumb_layout_changed or width_got_bigger:
                
                self._DirtyAllPages()
                
                self._DeleteAllDirtyPages()
                
            
            self.widget().update()
            
        
    
    def _RemoveMediaDirectly( self, singleton_media, collected_media ):
        
        if self._focused_media is not None:
            
            if self._focused_media in singleton_media or self._focused_media in collected_media:
                
                self._SetFocusedMedia( None )
                
            
        
        MediaPanel._RemoveMediaDirectly( self, singleton_media, collected_media )
        
        self._selected_media.difference_update( singleton_media )
        self._selected_media.difference_update( collected_media )
        
        self._shift_focused_media = None
        
        self._RecalculateVirtualSize()
        
        self._DirtyAllPages()
        
        self._PublishSelectionChange()
        
        HG.client_controller.pub( 'refresh_page_name', self._page_key )
        
        self.widget().update()
        
    
    def _ScrollEnd( self, shift = False ):
        
        if len( self._sorted_media ) > 0:
            
            end_media = self._sorted_media[ -1 ]
            
            self._HitMedia( end_media, False, shift )
            
            self._ScrollToMedia( end_media )
            
        
    
    def _ScrollHome( self, shift = False ):
        
        if len( self._sorted_media ) > 0:
            
            home_media = self._sorted_media[ 0 ]
            
            self._HitMedia( home_media, False, shift )
            
            self._ScrollToMedia( home_media )
            
        
    
    def _ScrollToMedia( self, media ):
        
        if media is not None:
            
            ( x, y ) = self._GetMediaCoordinates( media )
            
            visible_rect = QP.ScrollAreaVisibleRect( self )
            
            visible_rect_y = visible_rect.y()
            
            visible_rect_height = visible_rect.height()
            
            ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
            
            new_options = HG.client_controller.new_options
            
            percent_visible = new_options.GetInteger( 'thumbnail_visibility_scroll_percent' ) / 100
            
            if y < visible_rect_y:
                
                self.ensureVisible( 0, y, 0, 0 )
                
            elif y > visible_rect_y + visible_rect_height - ( thumbnail_span_height * percent_visible ):
                
                self.ensureVisible( 0, y + thumbnail_span_height )
                
            
        
    
    def _StopFading( self, hash ):
        
        if hash in self._thumbnails_being_faded_in:
            
            ( bmp, alpha_bmp, thumbnail_index, thumbnail, animation_started, num_frames ) = self._thumbnails_being_faded_in[ hash ]
            
            del self._thumbnails_being_faded_in[ hash ]
            
        
    
    def _UpdateBackgroundColour( self ):
        
        MediaPanel._UpdateBackgroundColour( self )
    
        self._DirtyAllPages()
        
        self._DeleteAllDirtyPages()
        
        self.widget().update()
        
    
    def _UpdateScrollBars( self ):

        # The following call is officially a no-op since this property is already true, but it also triggers an update
        # of the scroll area's scrollbars which we need.
        # We need this since we are intercepting & doing work in resize events which causes
        # event propagation between the scroll area and the scrolled widget to not work properly (since we are suppressing resize events of the scrolled widget - otherwise we would get an infinite loop).
        # Probably the best would be to change how this work and not intercept any resize events.
        # Originally this was wx event handling which got ported to Qt more or less unchanged, hence the hackiness.
        
        self.setWidgetResizable( True )
        
    
    def AddMediaResults( self, page_key, media_results ):
        
        if page_key == self._page_key:
            
            thumbnails = MediaPanel.AddMediaResults( self, page_key, media_results )
            
            if len( thumbnails ) > 0:
                
                self._RecalculateVirtualSize()
                
                HG.client_controller.GetCache( 'thumbnail' ).Waterfall( self._page_key, thumbnails )
                
                if len( self._selected_media ) == 0:
                    
                    self._PublishSelectionIncrement( thumbnails )
                    
                
            
        
    
    def mouseMoveEvent( self, event ):
        
        if event.buttons() & QC.Qt.LeftButton:
            
            we_started_dragging_on_this_panel = self._drag_init_coordinates is not None
            
            if we_started_dragging_on_this_panel:
                
                ( old_x, old_y ) = self._drag_init_coordinates.toTuple()
                
                ( x, y ) = QG.QCursor.pos().toTuple()
                
                ( delta_x, delta_y ) = ( x - old_x, y - old_y )
                
                if abs( delta_x ) > 10 or abs( delta_y ) > 10:
                    
                    media = self._GetSelectedFlatMedia( discriminant = CC.DISCRIMINANT_LOCAL )
                    
                    if len( media ) > 0:
                        
                        alt_down = event.modifiers() & QC.Qt.AltModifier
                        
                        result = ClientDragDrop.DoFileExportDragDrop( self, self._page_key, media, alt_down )
                        
                        if result not in ( QC.Qt.IgnoreAction, ):
                            
                            HG.client_controller.pub( 'media_focus_went_to_external_program', self._page_key )
                            
                        
                    
                
            
        else:
            
            self._drag_init_coordinates = None
            
        
        event.ignore()
        
    
    def EventKeyDown( self, event ):
        
        # accelerator tables can't handle escape key in windows, gg
        
        if event.key() == QC.Qt.Key_Escape:
            
            self._Select( ClientMedia.FileFilter( ClientMedia.FILE_FILTER_NONE ) )
            
        elif event.key() in ( QC.Qt.Key_PageUp, QC.Qt.Key_PageDown ):
            
            if event.key() == QC.Qt.Key_PageUp:
                
                direction = -1
                
            elif event.key() == QC.Qt.Key_PageDown:
                
                direction = 1
                
            
            shift = event.modifiers() & QC.Qt.ShiftModifier
            
            self._MoveFocusedThumbnail( self._num_rows_per_actual_page * direction, 0, shift )
            
        else:
            
            return True # was: event.ignore()
            
        
    
    def EventMouseFullScreen( self, event ):
        
        t = self._GetThumbnailUnderMouse( event )
        
        if t is not None:
            
            locations_manager = t.GetLocationsManager()
            
            if locations_manager.IsLocal():
                
                self._FullScreen( t )
                
            elif len( locations_manager.GetCurrentRemote() ) > 0:
                
                self._DownloadHashes( t.GetHashes() )
                
            
        
    
    def showEvent( self, event ):
        
        self._UpdateScrollBars()
        
    
    class _InnerWidget( QW.QWidget ):
        
        def __init__( self, parent ):
            
            QW.QWidget.__init__( self, parent )
            
            self._parent = parent
            
        
        def mousePressEvent( self, event ):
            
            self._parent._drag_init_coordinates = QG.QCursor.pos()
            
            thumb = self._parent._GetThumbnailUnderMouse( event )
            
            right_on_whitespace = event.button() == QC.Qt.RightButton and thumb is None
            
            if not right_on_whitespace:
                
                self._parent._HitMedia( thumb, event.modifiers() & QC.Qt.ControlModifier, event.modifiers() & QC.Qt.ShiftModifier )
                
            
            # this specifically does not scroll to media, as for clicking (esp. double-clicking attempts), the scroll can be jarring
            
        
        def paintEvent( self, event ):
            
            painter = QG.QPainter( self )
            
            ( thumbnail_span_width, thumbnail_span_height ) = self._parent._GetThumbnailSpanDimensions()
            
            page_height = self._parent._num_rows_per_canvas_page * thumbnail_span_height
            
            page_indices_to_display = self._parent._CalculateVisiblePageIndices()
            
            earliest_page_index_to_display = min( page_indices_to_display )
            last_page_index_to_display = max( page_indices_to_display )
            
            page_indices_to_draw = list( page_indices_to_display )
            
            if earliest_page_index_to_display > 0:
                
                page_indices_to_draw.append( earliest_page_index_to_display - 1 )
                
            
            page_indices_to_draw.append( last_page_index_to_display + 1 )
            
            page_indices_to_draw.sort()
            
            potential_clean_indices_to_steal = [ page_index for page_index in list(self._parent._clean_canvas_pages.keys()) if page_index not in page_indices_to_draw ]
            
            random.shuffle( potential_clean_indices_to_steal )
            
            y_start = self._parent._GetYStart()
            
            earliest_y = y_start
            
            bg_colour = HG.client_controller.new_options.GetColour( CC.COLOUR_THUMBGRID_BACKGROUND )
            
            painter.setBackground( QG.QBrush( bg_colour ) )
            
            painter.eraseRect( painter.viewport() )
            
            background_pixmap = HG.client_controller.bitmap_manager.GetMediaBackgroundPixmap()
            
            if background_pixmap is not None:
                
                # if instead of size we go bottomRight, that works to keep scrolling, but the scrolling doesn't cause a full refresh _or something_
                ( client_x, client_y ) = QP.ScrollAreaVisibleRect( self._parent ).size().toTuple()
                
                ( background_bmp_width, background_bmp_height ) = background_pixmap.size().toTuple()
                
                painter.drawPixmap( client_x - background_bmp_width, client_y - background_bmp_height, background_pixmap )
                
            
            for page_index in page_indices_to_draw:
                
                if page_index not in self._parent._clean_canvas_pages:
                    
                    if len( self._parent._dirty_canvas_pages ) == 0:
                        
                        if len( potential_clean_indices_to_steal ) > 0:
                            
                            index_to_steal = potential_clean_indices_to_steal.pop()
                            
                            self._parent._DirtyPage( index_to_steal )
                            
                        else:
                            
                            self._parent._CreateNewDirtyPage()
                            
                        
                    
                    canvas_page = self._parent._dirty_canvas_pages.pop()
                    
                    self._parent._DrawCanvasPage( page_index, canvas_page )
                    
                    self._parent._clean_canvas_pages[ page_index ] = canvas_page
                    
                
                if page_index in page_indices_to_display:
                    
                    canvas_page = self._parent._clean_canvas_pages[ page_index ]
                    
                    page_virtual_y = page_height * page_index
                    
                    painter.drawImage( 0, page_virtual_y, canvas_page )
                    
                
            
        
    
    def EventResize( self, event ):
        
        self._ReinitialisePageCacheIfNeeded()
        
        self._RecalculateVirtualSize( called_from_resize_event = True )
        
        self._last_client_size = QP.ScrollAreaVisibleRect( self ).size().toTuple()
        
    
    def mouseReleaseEvent( self, event ):
        
        if event.button() != QC.Qt.RightButton:
            
            QW.QScrollArea.mouseReleaseEvent( self, event )
            
            return
            
        
        new_options = HG.client_controller.new_options
        
        advanced_mode = new_options.GetBoolean( 'advanced_mode' )
        
        services_manager = HG.client_controller.services_manager
        
        all_locations_managers = [ media.GetLocationsManager() for media in ClientMedia.FlattenMedia( self._sorted_media ) ]
        selected_locations_managers = [ media.GetLocationsManager() for media in ClientMedia.FlattenMedia( self._selected_media ) ]
        
        selection_has_local = True in ( locations_manager.IsLocal() for locations_manager in selected_locations_managers )
        selection_has_local_file_domain = True in ( CC.LOCAL_FILE_SERVICE_KEY in locations_manager.GetCurrent() for locations_manager in selected_locations_managers )
        selection_has_trash = True in ( CC.TRASH_SERVICE_KEY in locations_manager.GetCurrent() for locations_manager in selected_locations_managers )
        selection_has_inbox = True in ( media.HasInbox() for media in self._selected_media )
        selection_has_archive = True in ( media.HasArchive() for media in self._selected_media )
        
        all_file_domains = HydrusData.MassUnion( locations_manager.GetCurrent() for locations_manager in all_locations_managers )
        all_specific_file_domains = all_file_domains.difference( { CC.COMBINED_FILE_SERVICE_KEY, CC.COMBINED_LOCAL_FILE_SERVICE_KEY } )
        all_local_file_domains = services_manager.Filter( all_specific_file_domains, ( HC.LOCAL_FILE_DOMAIN, ) )
        all_file_repos = services_manager.Filter( all_specific_file_domains, ( HC.FILE_REPOSITORY, ) )
        
        has_local = True in ( locations_manager.IsLocal() for locations_manager in all_locations_managers )
        has_remote = True in ( locations_manager.IsRemote() for locations_manager in all_locations_managers )
        
        num_files = self.GetNumFiles()
        num_selected = self._GetNumSelected()
        num_inbox = self.GetNumInbox()
        num_archive = self.GetNumArchive()
        
        media_has_inbox = num_inbox > 0
        media_has_archive = num_archive > 0
        
        menu = QW.QMenu( self.window() )
        
        if self._focused_media is not None:
            
            # variables
            
            multiple_selected = num_selected > 1
            
            collections_selected = True in ( media.IsCollection() for media in self._selected_media )
            
            services_manager = HG.client_controller.services_manager
            
            services = services_manager.GetServices()
            
            service_keys_to_names = { service.GetServiceKey() : service.GetName() for service in services }
            
            tag_repositories = [ service for service in services if service.GetServiceType() == HC.TAG_REPOSITORY ]
            
            file_repositories = [ service for service in services if service.GetServiceType() == HC.FILE_REPOSITORY ]
            
            ipfs_services = [ service for service in services if service.GetServiceType() == HC.IPFS ]
            
            local_ratings_services = [ service for service in services if service.GetServiceType() in ( HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ) ]
            
            local_booru_service = [ service for service in services if service.GetServiceType() == HC.LOCAL_BOORU ][0]
            
            local_booru_is_running = local_booru_service.GetPort() is not None
            
            i_can_post_ratings = len( local_ratings_services ) > 0
            
            focused_is_local = CC.COMBINED_LOCAL_FILE_SERVICE_KEY in self._focused_media.GetLocationsManager().GetCurrent()
            
            file_service_keys = { repository.GetServiceKey() for repository in file_repositories }
            upload_permission_file_service_keys = { repository.GetServiceKey() for repository in file_repositories if repository.HasPermission( HC.CONTENT_TYPE_FILES, HC.PERMISSION_ACTION_CREATE ) }
            petition_resolve_permission_file_service_keys = { repository.GetServiceKey() for repository in file_repositories if repository.HasPermission( HC.CONTENT_TYPE_FILES, HC.PERMISSION_ACTION_OVERRULE ) }
            petition_permission_file_service_keys = { repository.GetServiceKey() for repository in file_repositories if repository.HasPermission( HC.CONTENT_TYPE_FILES, HC.PERMISSION_ACTION_PETITION ) } - petition_resolve_permission_file_service_keys
            user_manage_permission_file_service_keys = { repository.GetServiceKey() for repository in file_repositories if repository.HasPermission( HC.CONTENT_TYPE_ACCOUNTS, HC.PERMISSION_ACTION_OVERRULE ) }
            ipfs_service_keys = { service.GetServiceKey() for service in ipfs_services }
            
            focused_is_ipfs = True in ( service_key in ipfs_service_keys for service_key in self._focused_media.GetLocationsManager().GetCurrentRemote() )
            
            if multiple_selected:
                
                download_phrase = 'download all possible selected'
                rescind_download_phrase = 'cancel downloads for all possible selected'
                upload_phrase = 'upload all possible selected to'
                rescind_upload_phrase = 'rescind pending selected uploads to'
                petition_phrase = 'petition all possible selected for removal from'
                rescind_petition_phrase = 'rescind selected petitions for'
                remote_delete_phrase = 'delete all possible selected from'
                modify_account_phrase = 'modify the accounts that uploaded selected to'
                
                pin_phrase = 'pin all to'
                rescind_pin_phrase = 'rescind pin to'
                unpin_phrase = 'unpin all from'
                rescind_unpin_phrase = 'rescind unpin from'
                
                archive_phrase = 'archive selected'
                inbox_phrase = 'return selected to inbox'
                local_delete_phrase = 'delete selected'
                trash_delete_phrase = 'delete selected from trash now'
                undelete_phrase = 'undelete selected'
                export_phrase = 'files'
                copy_phrase = 'files'
                
            else:
                
                download_phrase = 'download'
                rescind_download_phrase = 'cancel download'
                upload_phrase = 'upload to'
                rescind_upload_phrase = 'rescind pending upload to'
                petition_phrase = 'petition for removal from'
                rescind_petition_phrase = 'rescind petition for'
                remote_delete_phrase = 'delete from'
                modify_account_phrase = 'modify the account that uploaded this to'
                
                pin_phrase = 'pin to'
                rescind_pin_phrase = 'rescind pin to'
                unpin_phrase = 'unpin from'
                rescind_unpin_phrase = 'rescind unpin from'
                
                archive_phrase = 'archive'
                inbox_phrase = 'return to inbox'
                local_delete_phrase = 'delete'
                trash_delete_phrase = 'delete from trash now'
                undelete_phrase = 'undelete'
                export_phrase = 'file'
                copy_phrase = 'file'
                
            
            # info about the files
            
            groups_of_current_remote_service_keys = [ locations_manager.GetCurrentRemote() for locations_manager in selected_locations_managers ]
            groups_of_pending_remote_service_keys = [ locations_manager.GetPendingRemote() for locations_manager in selected_locations_managers ]
            groups_of_petitioned_remote_service_keys = [ locations_manager.GetPetitionedRemote() for locations_manager in selected_locations_managers ]
            groups_of_deleted_remote_service_keys = [ locations_manager.GetDeletedRemote() for locations_manager in selected_locations_managers ]
            
            current_remote_service_keys = HydrusData.MassUnion( groups_of_current_remote_service_keys )
            pending_remote_service_keys = HydrusData.MassUnion( groups_of_pending_remote_service_keys )
            petitioned_remote_service_keys = HydrusData.MassUnion( groups_of_petitioned_remote_service_keys )
            deleted_remote_service_keys = HydrusData.MassUnion( groups_of_deleted_remote_service_keys )
            
            common_current_remote_service_keys = HydrusData.IntelligentMassIntersect( groups_of_current_remote_service_keys )
            common_pending_remote_service_keys = HydrusData.IntelligentMassIntersect( groups_of_pending_remote_service_keys )
            common_petitioned_remote_service_keys = HydrusData.IntelligentMassIntersect( groups_of_petitioned_remote_service_keys )
            common_deleted_remote_service_keys = HydrusData.IntelligentMassIntersect( groups_of_deleted_remote_service_keys )
            
            disparate_current_remote_service_keys = current_remote_service_keys - common_current_remote_service_keys
            disparate_pending_remote_service_keys = pending_remote_service_keys - common_pending_remote_service_keys
            disparate_petitioned_remote_service_keys = petitioned_remote_service_keys - common_petitioned_remote_service_keys
            disparate_deleted_remote_service_keys = deleted_remote_service_keys - common_deleted_remote_service_keys
            
            some_downloading = True in ( locations_manager.IsDownloading() for locations_manager in selected_locations_managers )
            
            pending_file_service_keys = pending_remote_service_keys.intersection( file_service_keys )
            petitioned_file_service_keys = petitioned_remote_service_keys.intersection( file_service_keys )
            
            common_current_file_service_keys = common_current_remote_service_keys.intersection( file_service_keys )
            common_pending_file_service_keys = common_pending_remote_service_keys.intersection( file_service_keys )
            common_petitioned_file_service_keys = common_petitioned_remote_service_keys.intersection( file_service_keys )
            common_deleted_file_service_keys = common_deleted_remote_service_keys.intersection( file_service_keys )
            
            disparate_current_file_service_keys = disparate_current_remote_service_keys.intersection( file_service_keys )
            disparate_pending_file_service_keys = disparate_pending_remote_service_keys.intersection( file_service_keys )
            disparate_petitioned_file_service_keys = disparate_petitioned_remote_service_keys.intersection( file_service_keys )
            disparate_deleted_file_service_keys = disparate_deleted_remote_service_keys.intersection( file_service_keys )
            
            pending_ipfs_service_keys = pending_remote_service_keys.intersection( ipfs_service_keys )
            petitioned_ipfs_service_keys = petitioned_remote_service_keys.intersection( ipfs_service_keys )
            
            common_current_ipfs_service_keys = common_current_remote_service_keys.intersection( ipfs_service_keys )
            common_pending_ipfs_service_keys = common_pending_file_service_keys.intersection( ipfs_service_keys )
            common_petitioned_ipfs_service_keys = common_petitioned_remote_service_keys.intersection( ipfs_service_keys )
            
            disparate_current_ipfs_service_keys = disparate_current_remote_service_keys.intersection( ipfs_service_keys )
            disparate_pending_ipfs_service_keys = disparate_pending_remote_service_keys.intersection( ipfs_service_keys )
            disparate_petitioned_ipfs_service_keys = disparate_petitioned_remote_service_keys.intersection( ipfs_service_keys )
            
            # valid commands for the files
            
            uploadable_file_service_keys = set()
            
            downloadable_file_service_keys = set()
            
            petitionable_file_service_keys = set()
            
            deletable_file_service_keys = set()
            
            modifyable_file_service_keys = set()
            
            pinnable_ipfs_service_keys = set()
            
            unpinnable_ipfs_service_keys = set()
            
            for locations_manager in selected_locations_managers:
                
                # FILE REPOS
                
                # we can upload (set pending) to a repo_id when we have permission, a file is local, not current, not pending, and either ( not deleted or we_can_overrule )
                
                if locations_manager.IsLocal():
                    
                    uploadable_file_service_keys.update( upload_permission_file_service_keys - locations_manager.GetCurrentRemote() - locations_manager.GetPendingRemote() - ( locations_manager.GetDeletedRemote() - petition_resolve_permission_file_service_keys ) )
                    
                
                # we can download (set pending to local) when we have permission, a file is not local and not already downloading and current
                
                if not locations_manager.IsLocal() and not locations_manager.IsDownloading():
                    
                    downloadable_file_service_keys.update( ipfs_service_keys.union( file_service_keys ) & locations_manager.GetCurrentRemote() )
                    
                
                # we can petition when we have permission and a file is current and it is not already petitioned
                
                petitionable_file_service_keys.update( ( petition_permission_file_service_keys & locations_manager.GetCurrentRemote() ) - locations_manager.GetPetitionedRemote() )
                
                # we can delete remote when we have permission and a file is current and it is not already petitioned
                
                deletable_file_service_keys.update( ( petition_resolve_permission_file_service_keys & locations_manager.GetCurrentRemote() ) - locations_manager.GetPetitionedRemote() )
                
                # we can modify users when we have permission and the file is current or deleted
                
                modifyable_file_service_keys.update( user_manage_permission_file_service_keys & ( locations_manager.GetCurrentRemote() | locations_manager.GetDeletedRemote() ) )
                
                # IPFS
                
                # we can pin if a file is local, not current, not pending
                
                if locations_manager.IsLocal():
                    
                    pinnable_ipfs_service_keys.update( ipfs_service_keys - locations_manager.GetCurrentRemote() - locations_manager.GetPendingRemote() )
                    
                
                # we can unpin a file if it is current and not petitioned
                
                unpinnable_ipfs_service_keys.update( ( ipfs_service_keys & locations_manager.GetCurrentRemote() ) - locations_manager.GetPetitionedRemote() )
                
            
            # do the actual menu
            
            selection_info_menu = QW.QMenu( menu )
            
            if multiple_selected:
                
                selection_info_menu_label = '{} files, {}'.format( HydrusData.ToHumanInt( num_selected ), self._GetPrettyTotalSize( only_selected = True ) )
                
            else:
                
                pretty_info_lines = self._focused_media.GetPrettyInfoLines()
                
                top_line = pretty_info_lines.pop( 0 )
                
                selection_info_menu_label = top_line
                
                for line in pretty_info_lines:
                    
                    ClientGUIMenus.AppendMenuLabel( selection_info_menu, line, line )
                    
                
            
            if len( self._selected_media ) == 1:
                
                AddFileViewingStatsMenu( selection_info_menu, self._focused_media )
                
            
            if len( disparate_current_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_current_file_service_keys, 'some uploaded to' )
                
            
            if multiple_selected and len( common_current_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_current_file_service_keys, 'selected uploaded to' )
                
            
            if len( disparate_pending_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_pending_file_service_keys, 'some pending to' )
                
            
            if len( common_pending_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_pending_file_service_keys, 'pending to' )
                
            
            if len( disparate_petitioned_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_petitioned_file_service_keys, 'some petitioned from' )
                
            
            if len( common_petitioned_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_petitioned_file_service_keys, 'petitioned from' )
                
            
            if len( disparate_deleted_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_deleted_file_service_keys, 'some deleted from' )
                
            
            if len( common_deleted_file_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_deleted_file_service_keys, 'deleted from' )
                
            
            if len( disparate_current_ipfs_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_current_ipfs_service_keys, 'some pinned to' )
                
            
            if multiple_selected and len( common_current_ipfs_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_current_ipfs_service_keys, 'selected pinned to' )
                
            
            if len( disparate_pending_ipfs_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_pending_ipfs_service_keys, 'some to be pinned to' )
                
            
            if len( common_pending_ipfs_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_pending_ipfs_service_keys, 'to be pinned to' )
                
            
            if len( disparate_petitioned_ipfs_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, disparate_petitioned_ipfs_service_keys, 'some to be unpinned from' )
                
            
            if len( common_petitioned_ipfs_service_keys ) > 0:
                
                AddServiceKeyLabelsToMenu( selection_info_menu, common_petitioned_ipfs_service_keys, unpin_phrase )
                
            
            
            if len( selection_info_menu.actions() ) == 0:
                
                selection_info_menu.deleteLater()
                
                ClientGUIMenus.AppendMenuLabel( menu, selection_info_menu_label )
                
            else:
                
                ClientGUIMenus.AppendMenu( menu, selection_info_menu, selection_info_menu_label )
                
            
        
        ClientGUIMenus.AppendSeparator( menu )
        
        ClientGUIMenus.AppendMenuItem( menu, 'refresh', 'Refresh the current search.', HG.client_controller.pub, 'refresh_query', self._page_key )
        
        if len( self._sorted_media ) > 0:
            
            ClientGUIMenus.AppendSeparator( menu )
            
            filter_counts = {}
            
            filter_counts[ ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ALL ) ] = num_files
            filter_counts[ ClientMedia.FileFilter( ClientMedia.FILE_FILTER_INBOX ) ] = num_inbox
            filter_counts[ ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ARCHIVE ) ] = num_archive
            filter_counts[ ClientMedia.FileFilter( ClientMedia.FILE_FILTER_SELECTED ) ] = num_selected
            
            has_local_and_remote = has_local and has_remote
            
            AddSelectMenu( self, menu, filter_counts, all_specific_file_domains, has_local_and_remote )
            AddRemoveMenu( self, menu, filter_counts, all_specific_file_domains, has_local_and_remote )
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if has_local:
                
                ClientGUIMenus.AppendMenuItem( menu, 'archive/delete filter', 'Launch a special media viewer that will quickly archive (left-click) and delete (right-click) the selected media.', self._ArchiveDeleteFilter )
                
            
        
        if self._focused_media is not None:
            
            if selection_has_inbox:
                
                ClientGUIMenus.AppendMenuItem( menu, archive_phrase, 'Archive the selected files.', self._Archive )
                
            
            if selection_has_archive:
                
                ClientGUIMenus.AppendMenuItem( menu, inbox_phrase, 'Put the selected files back in the inbox.', self._Inbox )
                
            
        
        if self._focused_media is not None:
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if selection_has_local_file_domain:
                
                ClientGUIMenus.AppendMenuItem( menu, local_delete_phrase, 'Delete the selected files from \'my files\'.', self._Delete )
                
            
            if selection_has_trash:
                
                ClientGUIMenus.AppendMenuItem( menu, trash_delete_phrase, 'Delete the selected files from the trash, forcing an immediate physical delete from your hard drive.', self._Delete, CC.TRASH_SERVICE_KEY )
                ClientGUIMenus.AppendMenuItem( menu, undelete_phrase, 'Restore the selected files back to \'my files\'.', self._Undelete )
                
            
            #
            
            ClientGUIMenus.AppendSeparator( menu )
            
            manage_menu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'tags', 'Manage tags for the selected files.', self._ManageTags )
            
            if i_can_post_ratings:
                
                ClientGUIMenus.AppendMenuItem( manage_menu, 'ratings', 'Manage ratings for the selected files.', self._ManageRatings )
                
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'urls', 'Manage urls for the selected files.', self._ManageURLs )
            ClientGUIMenus.AppendMenuItem( manage_menu, 'notes', 'Manage notes for the focused file.', self._ManageNotes )
            
            len_interesting_remote_service_keys = 0
            
            len_interesting_remote_service_keys += len( downloadable_file_service_keys )
            len_interesting_remote_service_keys += len( uploadable_file_service_keys )
            len_interesting_remote_service_keys += len( pending_file_service_keys )
            len_interesting_remote_service_keys += len( petitionable_file_service_keys )
            len_interesting_remote_service_keys += len( petitioned_file_service_keys )
            len_interesting_remote_service_keys += len( deletable_file_service_keys )
            len_interesting_remote_service_keys += len( modifyable_file_service_keys )
            len_interesting_remote_service_keys += len( pinnable_ipfs_service_keys )
            len_interesting_remote_service_keys += len( pending_ipfs_service_keys )
            len_interesting_remote_service_keys += len( unpinnable_ipfs_service_keys )
            len_interesting_remote_service_keys += len( petitioned_ipfs_service_keys )
            
            if multiple_selected:
                
                len_interesting_remote_service_keys += len( ipfs_service_keys )
                
            
            if len_interesting_remote_service_keys > 0:
                
                remote_action_menu = QW.QMenu( manage_menu )
                
                if len( downloadable_file_service_keys ) > 0:
                    ClientGUIMenus.AppendMenuItem( remote_action_menu, download_phrase, 'Download all possible selected files.', self._DownloadSelected )
                    
                
                if some_downloading:
                    ClientGUIMenus.AppendMenuItem( remote_action_menu, rescind_download_phrase, 'Stop downloading any of the selected files.', self._RescindDownloadSelected )
                    
                
                if len( uploadable_file_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, uploadable_file_service_keys, upload_phrase, 'Upload all selected files to the file repository.', self._UploadFiles )
                    
                
                if len( pending_file_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, pending_file_service_keys, rescind_upload_phrase, 'Rescind the pending upload to the file repository.', self._RescindUploadFiles )
                    
                
                if len( petitionable_file_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, petitionable_file_service_keys, petition_phrase, 'Petition these files for deletion from the file repository.', self._PetitionFiles )
                    
                
                if len( petitioned_file_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, petitioned_file_service_keys, rescind_petition_phrase, 'Rescind the petition to delete these files from the file repository.', self._RescindPetitionFiles )
                    
                
                if len( deletable_file_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, deletable_file_service_keys, remote_delete_phrase, 'Delete these files from the file repository.', self._Delete )
                    
                
                if len( modifyable_file_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, modifyable_file_service_keys, modify_account_phrase, 'Modify the account(s) that uploaded these files to the file repository.', self._ModifyUploaders )
                    
                
                if len( pinnable_ipfs_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, pinnable_ipfs_service_keys, pin_phrase, 'Pin these files to the ipfs service.', self._UploadFiles )
                    
                
                if len( pending_ipfs_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, pending_ipfs_service_keys, rescind_pin_phrase, 'Rescind the pending pin to the ipfs service.', self._RescindUploadFiles )
                    
                
                if len( unpinnable_ipfs_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, unpinnable_ipfs_service_keys, unpin_phrase, 'Unpin these files from the ipfs service.', self._PetitionFiles )
                    
                
                if len( petitioned_ipfs_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, petitioned_ipfs_service_keys, rescind_unpin_phrase, 'Rescind the pending unpin from the ipfs service.', self._RescindPetitionFiles )
                    
                
                if multiple_selected and len( ipfs_service_keys ) > 0:
                    
                    AddServiceKeysToMenu( self, remote_action_menu, ipfs_service_keys, 'pin new directory to', 'Pin these files as a directory to the ipfs service.', self._UploadDirectory )
                    
                
                ClientGUIMenus.AppendMenu( manage_menu, remote_action_menu, 'remote services' )
                
            
            duplicates_menu = QW.QMenu( manage_menu )
            
            focused_hash = self._focused_media.GetDisplayMedia().GetHash()
            
            if HG.client_controller.DBCurrentlyDoingJob():
                
                file_duplicate_info = None
                
            else:
                
                file_duplicate_info = HG.client_controller.Read( 'file_duplicate_info', self._file_service_key, focused_hash )
                
            
            focus_is_in_duplicate_group = False
            focus_is_in_alternate_group = False
            focus_has_fps = False
            focus_has_potentials = False
            focus_can_be_searched = self._focused_media.GetDisplayMedia().GetMime() in HC.MIMES_WE_CAN_PHASH
            
            if file_duplicate_info is None:
                
                ClientGUIMenus.AppendMenuLabel( duplicates_menu, 'could not fetch file\'s duplicates (db currently locked)' )
                
            else:
                
                file_duplicate_types_to_counts = file_duplicate_info[ 'counts' ]
                
                if len( file_duplicate_types_to_counts ) > 0:
                    
                    duplicates_view_menu = QW.QMenu( duplicates_menu )
                    
                    if HC.DUPLICATE_MEMBER in file_duplicate_types_to_counts:
                        
                        if file_duplicate_info[ 'is_king' ]:
                            
                            ClientGUIMenus.AppendMenuLabel( duplicates_view_menu, 'this is the best quality file of its group' )
                            
                        else:

                            ClientGUIMenus.AppendMenuItem( duplicates_view_menu, 'show the best quality file of this file\'s group', 'Load up a new search with this file\'s best quality duplicate.', self._ShowDuplicatesInNewPage, focused_hash, HC.DUPLICATE_KING )
                            
                        
                        ClientGUIMenus.AppendSeparator( duplicates_view_menu )
                        
                    
                    for duplicate_type in ( HC.DUPLICATE_MEMBER, HC.DUPLICATE_ALTERNATE, HC.DUPLICATE_FALSE_POSITIVE, HC.DUPLICATE_POTENTIAL ):
                        
                        if duplicate_type in file_duplicate_types_to_counts:
                            
                            count = file_duplicate_types_to_counts[ duplicate_type ]
                            
                            if count > 0:
                                
                                label = HydrusData.ToHumanInt( count ) + ' ' + HC.duplicate_type_string_lookup[ duplicate_type ]
                                
                                ClientGUIMenus.AppendMenuItem( duplicates_view_menu, label, 'Show these duplicates in a new page.', self._ShowDuplicatesInNewPage, focused_hash, duplicate_type )
                                
                                if duplicate_type == HC.DUPLICATE_MEMBER:
                                    
                                    focus_is_in_duplicate_group = True
                                    
                                elif duplicate_type == HC.DUPLICATE_ALTERNATE:
                                    
                                    focus_is_in_alternate_group = True
                                    
                                elif duplicate_type == HC.DUPLICATE_FALSE_POSITIVE:
                                    
                                    focus_has_fps = True
                                    
                                elif duplicate_type == HC.DUPLICATE_POTENTIAL:
                                    
                                    focus_has_potentials = True
                                    
                                
                            
                        
                    
                    ClientGUIMenus.AppendMenu( duplicates_menu, duplicates_view_menu, 'view this file\'s relations' )
                    
                
            
            focus_is_definitely_king = file_duplicate_info is not None and file_duplicate_info[ 'is_king' ]
            
            dissolution_actions_available = focus_can_be_searched or focus_is_in_duplicate_group or focus_is_in_alternate_group or focus_has_fps
            
            single_action_available = dissolution_actions_available or not focus_is_definitely_king
            
            if multiple_selected or single_action_available:
                
                duplicates_action_submenu = QW.QMenu( duplicates_menu )
                
                if file_duplicate_info is None:
                    
                    ClientGUIMenus.AppendMenuLabel( duplicates_action_submenu, 'could not fetch info to check for available file actions (db currently locked)' )
                    
                else:
                    
                    if not focus_is_definitely_king:
                        ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, 'set this file as the best quality of its group', 'Set the focused media to be the King of its group.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_focused_king' ) )
                        
                    
                    if dissolution_actions_available:
                        
                        duplicates_single_dissolution_menu = QW.QMenu( duplicates_action_submenu )
                        
                        if focus_can_be_searched:
                            ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'schedule this file to be searched for potentials again', 'Queue this file for another potentials search. Will not remove any existing potentials.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_reset_focused_potential_search' ) )
                            
                        
                        if focus_has_potentials:
                            ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'remove this file\'s potential relationships', 'Clear out this file\'s potential relationships.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_remove_focused_potentials' ) )
                            
                        
                        if focus_is_in_duplicate_group:
                            
                            if not focus_is_definitely_king:
                                ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'remove this file from its duplicate group', 'Extract this file from its duplicate group and reset its search status.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_remove_focused_from_duplicate_group' ) )
                                
                            ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'dissolve this file\'s duplicate group completely', 'Completely eliminate this file\'s duplicate group and reset all files\' search status.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_dissolve_focused_duplicate_group' ) )
                            
                        
                        if focus_is_in_alternate_group:
                            
                            ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'remove this file from its alternate group', 'Extract this file\'s duplicate group from its alternate group and reset the duplicate group\'s search status.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_remove_focused_from_alternate_group' ) )
                            
                            ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'dissolve this file\'s alternate group completely', 'Completely eliminate this file\'s alternate group and all duplicate group members. This resets search status for all involved files.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_dissolve_focused_alternate_group' ) )
                            
                        
                        if focus_has_fps:
                            ClientGUIMenus.AppendMenuItem( duplicates_single_dissolution_menu, 'delete all false-positive relationships this file\'s alternate group has with other groups', 'Clear out all false-positive relationships this file\'s alternates group has with other groups and resets search status.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_clear_focused_false_positives' ) )
                            
                        
                        ClientGUIMenus.AppendMenu( duplicates_action_submenu, duplicates_single_dissolution_menu, 'remove/reset for this file' )
                        
                    
                
                if multiple_selected:
                    
                    ClientGUIMenus.AppendSeparator( duplicates_action_submenu )
                    
                    label = 'set this file as better than the ' + HydrusData.ToHumanInt( num_selected - 1 ) + ' other selected'
                    
                    ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, label, 'Set the focused media to be better than the other selected files.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_focused_better' ) )
                    
                    num_pairs = num_selected * ( num_selected - 1 ) / 2 # com // ations -- n!/2(n-2)!
                    
                    num_pairs_text = HydrusData.ToHumanInt( num_pairs ) + ' pairs'
                    
                    ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, 'set all selected as same quality duplicates', 'Set all the selected files as same quality duplicates.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_same_quality' ) )
                    
                    ClientGUIMenus.AppendSeparator( duplicates_action_submenu )
                    
                    ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, 'set all selected as alternates', 'Set all the selected files as alternates.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_alternate' ) )
                    
                    ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, 'set a relationship with custom metadata merge options', 'Choose which duplicates status to set to this selection and customise non-default duplicate metadata merge options.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_custom' ) )
                    
                    if collections_selected:
                        
                        ClientGUIMenus.AppendSeparator( duplicates_action_submenu )
                        
                        ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, 'set selected collections as groups of alternates', 'Set files in the selection which are collected together as alternates.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_alternate_collections' ) )
                        
                    
                    ClientGUIMenus.AppendSeparator( duplicates_action_submenu )
                    
                    ClientGUIMenus.AppendMenuItem( duplicates_action_submenu, 'set all possible pair combinations as \'potential\' duplicates for the duplicates filter.', 'Queue all these files up in the duplicates filter.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_set_potential' ) )
                    
                    if advanced_mode:
                        
                        ClientGUIMenus.AppendSeparator( duplicates_action_submenu )
                        
                        duplicates_multiple_dissolution_menu = QW.QMenu( duplicates_action_submenu )
                        
                        ClientGUIMenus.AppendMenuItem( duplicates_multiple_dissolution_menu, 'schedule these files to be searched for potentials again', 'Queue these files for another potentials search. Will not remove any existing potentials.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_reset_potential_search' ) )
                        ClientGUIMenus.AppendMenuItem( duplicates_multiple_dissolution_menu, 'remove these files\' potential relationships', 'Clear out these files\' potential relationships.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_remove_potentials' ) )
                        ClientGUIMenus.AppendMenuItem( duplicates_multiple_dissolution_menu, 'dissolve these files\' duplicate groups completely', 'Completely eliminate these files\' duplicate groups and reset all files\' search status.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_dissolve_duplicate_group' ) )
                        ClientGUIMenus.AppendMenuItem( duplicates_multiple_dissolution_menu, 'dissolve these files\' alternate groups completely', 'Completely eliminate these files\' alternate groups and all duplicate group members. This resets search status for all involved files.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_dissolve_alternate_group' ) )
                        ClientGUIMenus.AppendMenuItem( duplicates_multiple_dissolution_menu, 'delete all false-positive relationships these files\' alternate groups have with other groups', 'Clear out all false-positive relationships these files\' alternates groups has with other groups and resets search status.', self.ProcessApplicationCommand, ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'duplicate_media_clear_false_positives' ) )
                        
                        ClientGUIMenus.AppendMenu( duplicates_action_submenu, duplicates_multiple_dissolution_menu, 'remove/reset for all selected' )
                        
                    
                    duplicates_edit_action_submenu = QW.QMenu( duplicates_action_submenu )
                    
                    for duplicate_type in ( HC.DUPLICATE_BETTER, HC.DUPLICATE_SAME_QUALITY ):
                        ClientGUIMenus.AppendMenuItem( duplicates_edit_action_submenu, 'for ' + HC.duplicate_type_string_lookup[duplicate_type], 'Edit what happens when you set this status.', self._EditDuplicateActionOptions, duplicate_type )
                        
                    
                    if HG.client_controller.new_options.GetBoolean( 'advanced_mode' ):
                        ClientGUIMenus.AppendMenuItem( duplicates_edit_action_submenu, 'for ' + HC.duplicate_type_string_lookup[HC.DUPLICATE_ALTERNATE] + ' (advanced!)', 'Edit what happens when you set this status.', self._EditDuplicateActionOptions, HC.DUPLICATE_ALTERNATE )
                        
                    
                    ClientGUIMenus.AppendSeparator( duplicates_action_submenu )
                    
                    ClientGUIMenus.AppendMenu( duplicates_action_submenu, duplicates_edit_action_submenu, 'edit default duplicate metadata merge options' )
                    
                
                ClientGUIMenus.AppendMenu( duplicates_menu, duplicates_action_submenu, 'set relationship' )
                
            
            if self._focused_media.HasImages():
                
                similar_menu = QW.QMenu( duplicates_menu )
                
                ClientGUIMenus.AppendMenuItem( similar_menu, 'exact match', 'Search the database for files that look precisely like those selected.', self._GetSimilarTo, HC.HAMMING_EXACT_MATCH )
                ClientGUIMenus.AppendMenuItem( similar_menu, 'very similar', 'Search the database for files that look just like those selected.', self._GetSimilarTo, HC.HAMMING_VERY_SIMILAR )
                ClientGUIMenus.AppendMenuItem( similar_menu, 'similar', 'Search the database for files that look generally like those selected.', self._GetSimilarTo, HC.HAMMING_SIMILAR )
                ClientGUIMenus.AppendMenuItem( similar_menu, 'speculative', 'Search the database for files that probably look like those selected. This is sometimes useful for symbols with sharp edges or lines.', self._GetSimilarTo, HC.HAMMING_SPECULATIVE )
                
                ClientGUIMenus.AppendMenu( duplicates_menu, similar_menu, 'find similar-looking files' )
                
            
            if len( duplicates_menu.actions() ) == 0:
                
                ClientGUIMenus.AppendMenuLabel( duplicates_menu, 'no file relationships or actions available for this file at present' )
                
            
            ClientGUIMenus.AppendMenu( manage_menu, duplicates_menu, 'file relationships' )
            
            regen_menu = QW.QMenu( manage_menu )
            
            ClientGUIMenus.AppendMenuItem( regen_menu, 'thumbnails, but only if wrong size', 'Regenerate the selected files\' thumbnails, but only if they are the wrong size.', self._RegenerateFileData, ClientFiles.REGENERATE_FILE_DATA_JOB_REFIT_THUMBNAIL )
            ClientGUIMenus.AppendMenuItem( regen_menu, 'thumbnails', 'Regenerate the selected files\'s thumbnails.', self._RegenerateFileData, ClientFiles.REGENERATE_FILE_DATA_JOB_FORCE_THUMBNAIL )
            ClientGUIMenus.AppendMenuItem( regen_menu, 'file metadata', 'Regenerated the selected files\' metadata and thumbnails.', self._RegenerateFileData, ClientFiles.REGENERATE_FILE_DATA_JOB_FILE_METADATA )
            
            ClientGUIMenus.AppendMenu( manage_menu, regen_menu, 'regenerate' )
            
            ClientGUIMenus.AppendMenu( menu, manage_menu, 'manage' )
            
            #
            
            AddKnownURLsViewCopyMenu( self, menu, self._focused_media, selected_media = self._selected_media )
            
            #
            
            open_menu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( open_menu, 'in external program', 'Launch this file with your OS\'s default program for it.', self._OpenExternally )
            ClientGUIMenus.AppendMenuItem( open_menu, 'in a new page', 'Copy your current selection into a simple new page.', self._ShowSelectionInNewPage )
            ClientGUIMenus.AppendMenuItem( open_menu, 'in web browser', 'Show this file in your OS\'s web browser.', self._OpenFileInWebBrowser )
            
            if focused_is_local:
                
                show_open_in_explorer = advanced_mode and not HC.PLATFORM_LINUX
                
                if show_open_in_explorer:
                    
                    ClientGUIMenus.AppendMenuItem( open_menu, 'in file browser', 'Show this file in your OS\'s file browser.', self._OpenFileLocation )
                    
                
            
            ClientGUIMenus.AppendMenu( menu, open_menu, 'open' )
            
            # share
            
            share_menu = QW.QMenu( menu )
            
            #
            
            copy_menu = QW.QMenu( share_menu )
            
            if selection_has_local:
                
                ClientGUIMenus.AppendMenuItem( copy_menu, copy_phrase, 'Copy the selected files to the clipboard.', self._CopyFilesToClipboard )
                
                if advanced_mode:
                    
                    copy_hash_menu = QW.QMenu( copy_menu )
                    
                    ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha256 (hydrus default)', 'Copy the selected file\'s SHA256 hash to the clipboard.', self._CopyHashToClipboard, 'sha256' )
                    ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'md5', 'Copy the selected file\'s MD5 hash to the clipboard.', self._CopyHashToClipboard, 'md5' )
                    ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha1', 'Copy the selected file\'s SHA1 hash to the clipboard.', self._CopyHashToClipboard, 'sha1' )
                    ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha512', 'Copy the selected file\'s SHA512 hash to the clipboard.', self._CopyHashToClipboard, 'sha512' )
                    
                    ClientGUIMenus.AppendMenu( copy_menu, copy_hash_menu, 'hash' )
                    
                    if multiple_selected:
                        
                        copy_hash_menu = QW.QMenu( copy_menu )
                        
                        ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha256 (hydrus default)', 'Copy the selected files\' SHA256 hashes to the clipboard.', self._CopyHashesToClipboard, 'sha256' )
                        ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'md5', 'Copy the selected files\' MD5 hashes to the clipboard.', self._CopyHashesToClipboard, 'md5' )
                        ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha1', 'Copy the selected files\' SHA1 hashes to the clipboard.', self._CopyHashesToClipboard, 'sha1' )
                        ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha512', 'Copy the selected files\' SHA512 hashes to the clipboard.', self._CopyHashesToClipboard, 'sha512' )
                        
                        ClientGUIMenus.AppendMenu( copy_menu, copy_hash_menu, 'hashes' )
                        
                    
                
            else:
                
                if advanced_mode:
                    
                    ClientGUIMenus.AppendMenuItem( copy_menu, 'sha256 hash', 'Copy the selected file\'s SHA256 hash to the clipboard.', self._CopyHashToClipboard, 'sha256' )
                    
                    if multiple_selected:
                        
                        ClientGUIMenus.AppendMenuItem( copy_menu, 'sha256 hashes', 'Copy the selected files\' SHA256 hash to the clipboard.', self._CopyHashesToClipboard, 'sha256' )
                        
                    
                
            
            for ipfs_service_key in self._focused_media.GetLocationsManager().GetCurrentRemote().intersection( ipfs_service_keys ):
                
                name = service_keys_to_names[ ipfs_service_key ]
                
                ClientGUIMenus.AppendMenuItem( copy_menu, name + ' multihash', 'Copy the selected file\'s multihash to the clipboard.', self._CopyServiceFilenameToClipboard, ipfs_service_key )
                
            
            if multiple_selected:
                
                for ipfs_service_key in disparate_current_ipfs_service_keys.union( common_current_ipfs_service_keys ):
                    
                    name = service_keys_to_names[ ipfs_service_key ]
                    
                    ClientGUIMenus.AppendMenuItem( copy_menu, name + ' multihashes', 'Copy the selected files\' multihashes to the clipboard.', self._CopyServiceFilenamesToClipboard, ipfs_service_key )
                    
                
            
            if focused_is_local:
                
                if self._focused_media.GetMime() in HC.IMAGES:
                    
                    ClientGUIMenus.AppendMenuItem( copy_menu, 'image (bitmap)', 'Copy the selected file\'s image data to the clipboard (as a bmp).', self._CopyBMPToClipboard )
                    
                
                ClientGUIMenus.AppendMenuItem( copy_menu, 'path', 'Copy the selected file\'s path to the clipboard.', self._CopyPathToClipboard )
                
            
            if multiple_selected and selection_has_local:
                
                ClientGUIMenus.AppendMenuItem( copy_menu, 'paths', 'Copy the selected files\' paths to the clipboard.', self._CopyPathsToClipboard )
                
            
            ClientGUIMenus.AppendMenu( share_menu, copy_menu, 'copy' )
            
            #
            
            export_menu  = QW.QMenu( share_menu )
            
            ClientGUIMenus.AppendMenuItem( export_menu, export_phrase, 'Export the selected files to an external folder.', self._ExportFiles )
            
            ClientGUIMenus.AppendMenu( share_menu, export_menu, 'export' )
            
            #
            
            if local_booru_is_running:
                
                ClientGUIMenus.AppendMenuItem( share_menu, 'on local booru', 'Share the selected files on your client\'s local booru.', self._ShareOnLocalBooru )
                
            
            #
            
            ClientGUIMenus.AppendMenu( menu, share_menu, 'share' )
            
        
        HG.client_controller.PopupMenu( self, menu )
        
    
    def MaintainPageCache( self ):
        
        if not HG.client_controller.gui.IsCurrentPage( self._page_key ):
            
            self._DirtyAllPages()
            
        
        self._DeleteAllDirtyPages()
        
    
    def NewThumbnails( self, hashes ):
        
        affected_thumbnails = self._GetMedia( hashes )
        
        if len( affected_thumbnails ) > 0:
            
            self._RedrawMedia( affected_thumbnails )
            
        
    
    def NotifyNewFileInfo( self, hashes ):
        
        def qt_do_update( hashes_to_media_results ):
            
            affected_media = self._GetMedia( set( hashes_to_media_results.keys() ) )
            
            for media in affected_media:
                
                media.UpdateFileInfo( hashes_to_media_results )
                
            
            self._RedrawMedia( affected_media )
            
        
        def do_it( win, callable, affected_hashes ):
            
            media_results = HG.client_controller.Read( 'media_results', affected_hashes )
            
            hashes_to_media_results = { media_result.GetHash() : media_result for media_result in media_results }
            
            HG.client_controller.CallLaterQtSafe( win, 0, qt_do_update, hashes_to_media_results )
            
        
        affected_hashes = self._hashes.intersection( hashes )
        
        HG.client_controller.CallToThread( do_it, self, do_it, affected_hashes )
        
    
    def RedrawAllThumbnails( self ):
        
        self._DirtyAllPages()
        
        for m in self._collected_media:
            
            m.RecalcInternals()
            
        
        self.widget().update()
        
    
    def RefreshAcceleratorTable( self ):
        
        if not self or not QP.isValid( self ):
            
            return
        
        # Remove old shortcuts
        for child in self.children():
            
            if isinstance( child, QW.QShortcut ):
                
                child.setParent( None )
                child.deleteLater()
                
            
        
        def ctrl_space_callback( self ):

            if self._focused_media is not None:
                
                self._HitMedia( self._focused_media, True, False )
        
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Home, self._ScrollHome, False ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Home, self._ScrollHome, False ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_End, self._ScrollEnd, False ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_End, self._ScrollEnd, False ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Delete, self._Delete ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Delete, self._Delete ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Return, self._FullScreen ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Enter, self._FullScreen ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Up, self._MoveFocusedThumbnail, -1, 0, False ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Up, self._MoveFocusedThumbnail, -1, 0, False ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Down, self._MoveFocusedThumbnail, 1, 0, False ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Down, self._MoveFocusedThumbnail, 1, 0, False ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Left, self._MoveFocusedThumbnail, 0, -1, False ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Left, self._MoveFocusedThumbnail, 0, -1, False ),
        QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Right, self._MoveFocusedThumbnail, 0, 1, False ),
        QP.AddShortcut( self, QC.Qt.KeypadModifier, QC.Qt.Key_Right, self._MoveFocusedThumbnail, 0, 1, False ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Home, self._ScrollHome, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_Home, self._ScrollHome, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_End, self._ScrollEnd, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_End, self._ScrollEnd, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Delete, self._Undelete ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_Delete, self._Undelete ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Up, self._MoveFocusedThumbnail, -1, 0, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_Up, self._MoveFocusedThumbnail, -1, 0, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Down, self._MoveFocusedThumbnail, 1, 0, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_Down, self._MoveFocusedThumbnail, 1, 0, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Left, self._MoveFocusedThumbnail, 0, -1, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_Left, self._MoveFocusedThumbnail, 0, -1, True ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Right, self._MoveFocusedThumbnail, 0, 1, True  ),
        QP.AddShortcut( self, QC.Qt.ShiftModifier | QC.Qt.KeypadModifier, QC.Qt.Key_Right, self._MoveFocusedThumbnail, 0, 1, True ),
        QP.AddShortcut( self, QC.Qt.ControlModifier, QC.Qt.Key_A, self._Select, ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ALL ) ),
        QP.AddShortcut( self, QC.Qt.ControlModifier, QC.Qt.Key_Space, ctrl_space_callback, self )
        
        if HC.PLATFORM_MACOS:
            
            QP.AddShortcut( self, QC.Qt.NoModifier, QC.Qt.Key_Back, self._Delete )
            QP.AddShortcut( self, QC.Qt.ShiftModifier, QC.Qt.Key_Back, self._Undelete )
            
        
        
    
    def SetFocusedMedia( self, page_key, media ):
        
        MediaPanel.SetFocusedMedia( self, page_key, media )
        
        if page_key == self._page_key:
            
            if media is None:
                
                self._SetFocusedMedia( None )
                
            else:
                
                try:
                    
                    my_media = self._GetMedia( media.GetHashes() )[0]
                    
                    self._HitMedia( my_media, False, False )
                    
                    self._ScrollToMedia( self._focused_media )
                    
                except:
                    
                    pass
                    
                
            
        
    
    def Sort( self, page_key, media_sort = None ):
        
        MediaPanel.Sort( self, page_key, media_sort )
        
        self._DirtyAllPages()
        
        self.widget().update()
        
    
    def ThumbnailsReset( self ):
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        thumbnail_scroll_rate = float( HG.client_controller.new_options.GetString( 'thumbnail_scroll_rate' ) )
        
        self.verticalScrollBar().setSingleStep( int( round( thumbnail_span_height * thumbnail_scroll_rate ) ) )
        
        self._thumbnails_being_faded_in = {}
        self._hashes_faded = set()
        
        self._ReinitialisePageCacheIfNeeded()
        
        self._RecalculateVirtualSize()
        
        self.RedrawAllThumbnails()
        
    
    def TIMERAnimationUpdate( self ):
        
        FRAME_DURATION = 1.0 / 60
        NUM_FRAMES_TO_FILL_IN = 15
        
        loop_started = HydrusData.GetNowPrecise()
        loop_should_break_time = loop_started + ( FRAME_DURATION / 2 )
        
        ( thumbnail_span_width, thumbnail_span_height ) = self._GetThumbnailSpanDimensions()
        
        thumbnail_margin = HG.client_controller.new_options.GetInteger( 'thumbnail_margin' )
        
        hashes = list( self._thumbnails_being_faded_in.keys() )
        
        random.shuffle( hashes )
        
        dcs = {}
        
        y_start = self._GetYStart()
        
        earliest_y = y_start
        
        page_height = self._num_rows_per_canvas_page * thumbnail_span_height
        
        for hash in hashes:
            
            ( original_bmp, alpha_bmp, thumbnail_index, thumbnail, animation_started, num_frames_rendered ) = self._thumbnails_being_faded_in[ hash ]
            
            num_frames_supposed_to_be_rendered = int( ( loop_started - animation_started ) / FRAME_DURATION )
            
            num_frames_to_render = num_frames_supposed_to_be_rendered - num_frames_rendered
            
            if num_frames_to_render == 0:
                
                continue
                
            
            delete_entry = False
            
            try:
                
                expected_thumbnail = self._sorted_media[ thumbnail_index ]
                
            except:
                
                expected_thumbnail = None
                
            
            page_index = self._GetPageIndexFromThumbnailIndex( thumbnail_index )
            
            if expected_thumbnail != thumbnail:
                
                delete_entry = True
                
            elif page_index not in self._clean_canvas_pages:
                
                delete_entry = True
                
            else:
                
                times_to_draw = 1
                
                if num_frames_supposed_to_be_rendered >= NUM_FRAMES_TO_FILL_IN:
                    
                    bmp_to_use = original_bmp
                    
                    delete_entry = True
                    
                else:
                    
                    times_to_draw = num_frames_to_render
                    
                    bmp_to_use = alpha_bmp
                    
                    num_frames_rendered += times_to_draw
                    
                    self._thumbnails_being_faded_in[ hash ] = ( original_bmp, alpha_bmp, thumbnail_index, thumbnail, animation_started, num_frames_rendered )
                    
                
                thumbnail_col = thumbnail_index % self._num_columns
                
                thumbnail_row = thumbnail_index // self._num_columns
                
                x = thumbnail_col * thumbnail_span_width + thumbnail_margin
                
                y = ( thumbnail_row - ( page_index * self._num_rows_per_canvas_page ) ) * thumbnail_span_height + thumbnail_margin
                
                if page_index not in dcs:
                    
                    canvas_page = self._clean_canvas_pages[ page_index ]
                    
                    painter = QG.QPainter( canvas_page )
                    
                    dcs[ page_index ] = painter
                    
                
                painter = dcs[ page_index ]
                
                for i in range( times_to_draw ):
                    
                    painter.drawImage( x, y, bmp_to_use )
                    
                
                #
                
                page_virtual_y = page_height * page_index
                
                self.widget().update( QC.QRect( x, page_virtual_y + y, thumbnail_span_width - thumbnail_margin, thumbnail_span_height - thumbnail_margin ) )
                
            
            if delete_entry:
                
                del self._thumbnails_being_faded_in[ hash ]
                
            
            if HydrusData.TimeHasPassedPrecise( loop_should_break_time ):
                
                break
                
            
        
        if len( self._thumbnails_being_faded_in ) == 0:
            
            HG.client_controller.gui.UnregisterAnimationUpdateWindow( self )
            
        
        
    
    def WaterfallThumbnails( self, page_key, thumbnails ):
        
        if self._page_key == page_key:
            
            self._FadeThumbnails( thumbnails )
            
        
    
def AddRemoveMenu( win: MediaPanel, menu, filter_counts, all_specific_file_domains, has_local_and_remote ):
    
    file_filter_all = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ALL )
    
    if file_filter_all.GetCount( win, filter_counts ) > 0:
        
        remove_menu = QW.QMenu( menu )
        
        #
        
        file_filter_selected = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_SELECTED )
        
        file_filter_inbox = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_INBOX )
        
        file_filter_archive = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ARCHIVE )
        
        file_filter_not_selected = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_NOT_SELECTED )
        
        #
        
        selected_count = file_filter_selected.GetCount( win, filter_counts )
        
        if selected_count > 0 and selected_count < file_filter_all.GetCount( win, filter_counts ):
            
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_selected.ToString( win, filter_counts ), 'Remove all the selected files from the current view.', win._Remove, file_filter_selected )
            
        
        if file_filter_all.GetCount( win, filter_counts ) > 0:
            
            ClientGUIMenus.AppendSeparator( remove_menu )
            
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_all.ToString( win, filter_counts ), 'Remove all the files from the current view.', win._Remove, file_filter_all )
            
        
        if file_filter_inbox.GetCount( win, filter_counts ) > 0 and file_filter_archive.GetCount( win, filter_counts ) > 0:
            
            ClientGUIMenus.AppendSeparator( remove_menu )
            
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_inbox.ToString( win, filter_counts ), 'Remove all the inbox files from the current view.', win._Remove, file_filter_inbox )
            
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_archive.ToString( win, filter_counts ), 'Remove all the archived files from the current view.', win._Remove, file_filter_archive )
            
        
        if len( all_specific_file_domains ) > 1:
            
            ClientGUIMenus.AppendSeparator( remove_menu )
            
            all_specific_file_domains = list( all_specific_file_domains )
            
            if CC.TRASH_SERVICE_KEY in all_specific_file_domains:
                
                all_specific_file_domains.remove( CC.TRASH_SERVICE_KEY )
                all_specific_file_domains.insert( 0, CC.TRASH_SERVICE_KEY )
                
            
            if CC.LOCAL_FILE_SERVICE_KEY in all_specific_file_domains:
                
                all_specific_file_domains.remove( CC.LOCAL_FILE_SERVICE_KEY )
                all_specific_file_domains.insert( 0, CC.LOCAL_FILE_SERVICE_KEY )
                
            
            for file_service_key in all_specific_file_domains:
                
                file_filter = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_FILE_SERVICE, file_service_key )
                
                ClientGUIMenus.AppendMenuItem( remove_menu, file_filter.ToString( win, filter_counts ), 'Remove all the files that are in this file domain.', win._Remove, file_filter )
                
            
        
        if has_local_and_remote:
            
            file_filter_local = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_LOCAL )
            file_filter_remote = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_REMOTE )
            
            ClientGUIMenus.AppendSeparator( remove_menu )
            
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_local.ToString( win, filter_counts ), 'Remove all the files that are in this client.', win._Remove, file_filter_local )
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_remote.ToString( win, filter_counts ), 'Remove all the files that are not in this client.', win._Remove, file_filter_remote )
            
        
        not_selected_count = file_filter_not_selected.GetCount( win, filter_counts )
        
        if not_selected_count > 0 and selected_count > 0:
            
            ClientGUIMenus.AppendSeparator( remove_menu )
            
            ClientGUIMenus.AppendMenuItem( remove_menu, file_filter_not_selected.ToString( win, filter_counts ), 'Remove all the not selected files from the current view.', win._Remove, file_filter_not_selected )
            
        
        ClientGUIMenus.AppendMenu( menu, remove_menu, 'remove' )
        
    
def AddSelectMenu( win: MediaPanel, menu, filter_counts, all_specific_file_domains, has_local_and_remote ):
    
    file_filter_all = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ALL )
    
    if file_filter_all.GetCount( win, filter_counts ) > 0:
        
        select_menu = QW.QMenu( menu )
        
        #
        
        file_filter_inbox = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_INBOX )
        
        file_filter_archive = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_ARCHIVE )
        
        file_filter_not_selected = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_NOT_SELECTED )
        
        file_filter_none = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_NONE )
        
        #
        
        if file_filter_all.GetCount( win, filter_counts ) > 0:
            
            ClientGUIMenus.AppendSeparator( select_menu )
            
            ClientGUIMenus.AppendMenuItem( select_menu, file_filter_all.ToString( win, filter_counts ), 'Select all the files in the current view.', win._Select, file_filter_all )
            
        
        if file_filter_inbox.GetCount( win, filter_counts ) > 0 and file_filter_archive.GetCount( win, filter_counts ) > 0:
            
            ClientGUIMenus.AppendSeparator( select_menu )
            
            ClientGUIMenus.AppendMenuItem( select_menu, file_filter_inbox.ToString( win, filter_counts ), 'Select all the inbox files in the current view.', win._Select, file_filter_inbox )
            
            ClientGUIMenus.AppendMenuItem( select_menu, file_filter_archive.ToString( win, filter_counts ), 'Select all the archived files in the current view.', win._Select, file_filter_archive )
            
        
        if len( all_specific_file_domains ) > 1:
            
            ClientGUIMenus.AppendSeparator( select_menu )
            
            all_specific_file_domains = list( all_specific_file_domains )
            
            if CC.TRASH_SERVICE_KEY in all_specific_file_domains:
                
                all_specific_file_domains.remove( CC.TRASH_SERVICE_KEY )
                all_specific_file_domains.insert( 0, CC.TRASH_SERVICE_KEY )
                
            
            if CC.LOCAL_FILE_SERVICE_KEY in all_specific_file_domains:
                
                all_specific_file_domains.remove( CC.LOCAL_FILE_SERVICE_KEY )
                all_specific_file_domains.insert( 0, CC.LOCAL_FILE_SERVICE_KEY )
                
            
            for file_service_key in all_specific_file_domains:
                
                file_filter = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_FILE_SERVICE, file_service_key )
                
                ClientGUIMenus.AppendMenuItem( select_menu, file_filter.ToString( win, filter_counts ), 'Select all the files in this file domain.', win._Select, file_filter )
                
            
        
        if has_local_and_remote:
            
            file_filter_local = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_LOCAL )
            file_filter_remote = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_REMOTE )
            
            ClientGUIMenus.AppendSeparator( select_menu )
            
            ClientGUIMenus.AppendMenuItem( select_menu, file_filter_local.ToString( win, filter_counts ), 'Remove all the files that are in this client.', win._Select, file_filter_local )
            ClientGUIMenus.AppendMenuItem( select_menu, file_filter_remote.ToString( win, filter_counts ), 'Remove all the files that are not in this client.', win._Select, file_filter_remote )
            
        
        file_filter_selected = ClientMedia.FileFilter( ClientMedia.FILE_FILTER_SELECTED )
        selected_count = file_filter_selected.GetCount( win, filter_counts )
        
        not_selected_count = file_filter_not_selected.GetCount( win, filter_counts )
        
        if selected_count > 0:
            
            if not_selected_count > 0:
                
                ClientGUIMenus.AppendSeparator( select_menu )
                
                ClientGUIMenus.AppendMenuItem( select_menu, file_filter_not_selected.ToString( win, filter_counts ), 'Swap what is and is not selected.', win._Select, file_filter_not_selected )
                
            
            ClientGUIMenus.AppendSeparator( select_menu )
            
            ClientGUIMenus.AppendMenuItem( select_menu, file_filter_none.ToString( win, filter_counts ), 'Deselect everything selected.', win._Select, file_filter_none )
            
        
        ClientGUIMenus.AppendMenu( menu, select_menu, 'select' )
        
    
class Selectable( object ):
    
    def __init__( self ): self._selected = False
    
    def Deselect( self ): self._selected = False
    
    def IsSelected( self ): return self._selected
    
    def Select( self ): self._selected = True
    
class Thumbnail( Selectable ):
    
    def __init__( self, file_service_key ):
        
        Selectable.__init__( self )
        
        self._dump_status = CC.DUMPER_NOT_DUMPED
        self._file_service_key = file_service_key
        
        self._last_tags = None
        
        self._last_upper_summary = None
        self._last_lower_summary = None
        
    
    def _ScaleUpThumbnailDimensions( self, thumbnail_dimensions, scale_up_dimensions ):
        
        ( thumb_width, thumb_height ) = thumbnail_dimensions
        ( scale_up_width, scale_up_height ) = scale_up_dimensions
        
        # we want to expand the image so that the smallest dimension fills everything
        
        scale_factor = max( scale_up_width / thumb_width, scale_up_height / thumb_height )
        
        destination_width = int( round( thumb_width * scale_factor ) )
        destination_height = int( round( thumb_height * scale_factor ) )
        
        offset_x = ( scale_up_width - destination_width ) // 2
        offset_y = ( scale_up_height - destination_height ) // 2
        
        offset_position = ( offset_x, offset_y )
        destination_dimensions = ( destination_width, destination_height )
        
        return ( offset_position, destination_dimensions )
        
    
    def Dumped( self, dump_status ):
        
        self._dump_status = dump_status
        
    
    def GetQtImage( self ):
        
        inbox = self.HasInbox()
        
        local = self.GetLocationsManager().IsLocal()
        
        thumbnail_hydrus_bmp = HG.client_controller.GetCache( 'thumbnail' ).GetThumbnail( self )
        
        thumbnail_border = HG.client_controller.new_options.GetInteger( 'thumbnail_border' )
        
        ( width, height ) = ClientData.AddPaddingToDimensions( HC.options[ 'thumbnail_dimensions' ], thumbnail_border * 2 )
        
        qt_image = HG.client_controller.bitmap_manager.GetQtImage( width, height, 24 )
        
        painter = QG.QPainter( qt_image )
        
        new_options = HG.client_controller.new_options
        
        if not local:
            
            if self._selected:
                
                background_colour_type = CC.COLOUR_THUMB_BACKGROUND_REMOTE_SELECTED
                
            else:
                
                background_colour_type = CC.COLOUR_THUMB_BACKGROUND_REMOTE
                
            
        else:
            
            if self._selected:
                
                background_colour_type = CC.COLOUR_THUMB_BACKGROUND_SELECTED
                
            else:
                
                background_colour_type = CC.COLOUR_THUMB_BACKGROUND
                
            
        
        painter.setPen( QC.Qt.NoPen )
        
        painter.setBrush( QG.QBrush( new_options.GetColour( background_colour_type ) ) )
        
        painter.drawRect( thumbnail_border, thumbnail_border, width-(thumbnail_border*2), height-(thumbnail_border*2) )
        
        thumbnail_fill = HG.client_controller.new_options.GetBoolean( 'thumbnail_fill' )
        
        ( thumb_width, thumb_height ) = thumbnail_hydrus_bmp.GetSize() 
        
        if thumbnail_fill:
            
            raw_thumbnail_qt_image_original = thumbnail_hydrus_bmp.GetQtImage()
            
            scale_up_dimensions = HC.options[ 'thumbnail_dimensions' ]
            
            ( offset_position, destination_dimensions ) = self._ScaleUpThumbnailDimensions( ( thumb_width, thumb_height ), scale_up_dimensions )
            
            ( destination_width, destination_height ) = destination_dimensions
            
            raw_thumbnail_qt_image = raw_thumbnail_qt_image_original.scaled( destination_width, destination_height, QC.Qt.IgnoreAspectRatio, QC.Qt.SmoothTransformation )
            
            ( x_offset, y_offset ) = offset_position
            
            x_offset += thumbnail_border
            y_offset += thumbnail_border
            
        else:
            
            raw_thumbnail_qt_image = thumbnail_hydrus_bmp.GetQtImage()
            
            x_offset = ( width - thumb_width ) // 2
            
            y_offset = ( height - thumb_height ) // 2
            
        
        painter.drawImage( x_offset, y_offset, raw_thumbnail_qt_image )
        
        TEXT_BORDER = 1
        
        new_options = HG.client_controller.new_options
        
        tags = self.GetTagsManager().GetCurrentAndPending( CC.COMBINED_TAG_SERVICE_KEY, ClientTags.TAG_DISPLAY_SINGLE_MEDIA )
        
        if len( tags ) > 0:
            
            upper_tag_summary_generator = new_options.GetTagSummaryGenerator( 'thumbnail_top' )
            lower_tag_summary_generator = new_options.GetTagSummaryGenerator( 'thumbnail_bottom_right' )
            
            if self._last_tags is not None and self._last_tags == tags:
                
                upper_summary = self._last_upper_summary
                lower_summary = self._last_lower_summary
                
            else:
                
                upper_summary = upper_tag_summary_generator.GenerateSummary( tags )
                
                lower_summary = lower_tag_summary_generator.GenerateSummary( tags )
                
                self._last_tags = set( tags )
                
                self._last_upper_summary = upper_summary
                self._last_lower_summary = lower_summary
                
            
            if len( upper_summary ) > 0 or len( lower_summary ) > 0:
                
                if len( upper_summary ) > 0:
                    
                    text_colour_with_alpha = upper_tag_summary_generator.GetTextColour()
                    
                    painter.setFont( QW.QApplication.font() )
                    
                    background_colour_with_alpha = upper_tag_summary_generator.GetBackgroundColour()
                    
                    painter.setBrush( QG.QBrush( background_colour_with_alpha ) )
                    
                    ( text_width, text_height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, upper_summary ).toTuple()
                    
                    box_x = thumbnail_border
                    box_y = thumbnail_border
                    box_width = width - ( thumbnail_border * 2 )
                    box_height = text_height + 2
                    
                    painter.setPen( QG.QPen( QC.Qt.NoPen ) )
                    
                    painter.drawRect( box_x, box_y, box_width, box_height )
                    
                    text_x = ( width - text_width ) // 2
                    text_y = box_y + TEXT_BORDER
                    
                    painter.setPen( QG.QPen( text_colour_with_alpha ) )
                    
                    QP.DrawText( painter, text_x, text_y, upper_summary )
                    
                
                if len( lower_summary ) > 0:
                    
                    text_colour_with_alpha = lower_tag_summary_generator.GetTextColour()
                    
                    painter.setFont( QW.QApplication.font() )
                    
                    background_colour_with_alpha = lower_tag_summary_generator.GetBackgroundColour()
                    
                    painter.setBrush( QG.QBrush( background_colour_with_alpha ) )
                    
                    ( text_width, text_height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, lower_summary ).toTuple()
                    
                    box_width = text_width + ( TEXT_BORDER * 2 )
                    box_height = text_height + ( TEXT_BORDER * 2 )
                    box_x = width - box_width - thumbnail_border
                    box_y = height - text_height - thumbnail_border
                    
                    painter.setPen( QG.QPen( QC.Qt.NoPen ) )
                    
                    painter.drawRect( box_x, box_y, box_width, box_height )
                    
                    text_x = box_x + TEXT_BORDER
                    text_y = box_y + TEXT_BORDER
                    
                    painter.setPen( QG.QPen( text_colour_with_alpha ) )
                    
                    QP.DrawText( painter, text_x, text_y, lower_summary )
                    
                
            
        
        if thumbnail_border > 0:
            
            if not local:
                
                if self._selected:
                    
                    border_colour_type = CC.COLOUR_THUMB_BORDER_REMOTE_SELECTED
                    
                else:
                    
                    border_colour_type = CC.COLOUR_THUMB_BORDER_REMOTE
                    
                
            else:
                
                if self._selected:
                    
                    border_colour_type = CC.COLOUR_THUMB_BORDER_SELECTED
                    
                else:
                    
                    border_colour_type = CC.COLOUR_THUMB_BORDER
                    
                
            
            # I had a hell of a time getting a transparent box to draw right with a pen border without crazy +1px in the params for reasons I did not understand
            # so I just decided four rects is neater and fine and actually prob faster in some cases
            
            #         _____            ______                              _____            ______      ________________
            # ___________(_)___  _________  /_______   _______ ______      __  /______      ___  /_________  /__  /__  /
            # ___  __ \_  /__  |/_/  _ \_  /__  ___/   __  __ `/  __ \     _  __/  __ \     __  __ \  _ \_  /__  /__  / 
            # __  /_/ /  / __>  < /  __/  / _(__  )    _  /_/ // /_/ /     / /_ / /_/ /     _  / / /  __/  / _  /  /_/  
            # _  .___//_/  /_/|_| \___//_/  /____/     _\__, / \____/      \__/ \____/      /_/ /_/\___//_/  /_/  (_)   
            # /_/                                      /____/                                                            
            
            painter.setBrush( QG.QBrush( new_options.GetColour( border_colour_type ) ) )
            painter.setPen( QG.QPen( QC.Qt.NoPen ) )
            
            rectangles = []
            
            side_height = height - ( thumbnail_border * 2 )
            rectangles.append( QC.QRectF( 0, 0, width, thumbnail_border ) ) # top
            rectangles.append( QC.QRectF( 0, height - thumbnail_border, width, thumbnail_border ) ) # bottom
            rectangles.append( QC.QRectF( 0, thumbnail_border, thumbnail_border, side_height ) ) # left
            rectangles.append( QC.QRectF( width - thumbnail_border, thumbnail_border, thumbnail_border, side_height ) ) # right
            
            painter.drawRects( rectangles )
            
        
        locations_manager = self.GetLocationsManager()
        
        icons_to_draw = []
        
        if locations_manager.IsDownloading():
            
            icons_to_draw.append( CC.GlobalPixmaps.downloading )
            
        
        if CC.TRASH_SERVICE_KEY in locations_manager.GetCurrent() or CC.COMBINED_LOCAL_FILE_SERVICE_KEY in locations_manager.GetDeleted():
            
            icons_to_draw.append( CC.GlobalPixmaps.trash )
            
        
        if inbox:
            
            icons_to_draw.append( CC.GlobalPixmaps.inbox )
            
        
        if len( icons_to_draw ) > 0:
            
            icon_x = -thumbnail_border
            
            for icon in icons_to_draw:
                
                painter.drawPixmap( width + icon_x - 18, thumbnail_border, icon )
                
                icon_x -= 18
                
            
        
        if self.IsCollection():
            
            painter.drawPixmap( 1, height-17, CC.GlobalPixmaps.collection )
            
            num_files_str = HydrusData.ToHumanInt( self.GetNumFiles() )
            
            painter.setFont( QW.QApplication.font() )
            
            ( text_width, text_height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, num_files_str ).toTuple()
            
            painter.setBrush( QG.QBrush( CC.COLOUR_UNSELECTED ) )
            
            painter.setPen( QC.Qt.NoPen )
            
            painter.drawRect( 17, height - text_height - 3, text_width + 2, text_height + 2 )
            
            painter.setPen( QG.QPen( CC.COLOUR_SELECTED_DARK ) )
            
            QP.DrawText( painter, 18, height - text_height - 2, num_files_str )
            
        
        # top left icons
        
        icons_to_draw = []
        
        if self.HasAudio():
            
            icons_to_draw.append( CC.GlobalPixmaps.sound )
            
        elif self.HasDuration():
            
            icons_to_draw.append( CC.GlobalPixmaps.play )
            
        
        services_manager = HG.client_controller.services_manager
        
        current = locations_manager.GetCurrentRemote()
        pending = locations_manager.GetPendingRemote()
        petitioned = locations_manager.GetPetitionedRemote()
        
        current_to_display = current.difference( petitioned )
        
        #
        
        service_types = [ services_manager.GetService( service_key ).GetServiceType() for service_key in current_to_display ]
        
        if HC.FILE_REPOSITORY in service_types:
            
            icons_to_draw.append( CC.GlobalPixmaps.file_repository )
            
        
        if HC.IPFS in service_types:
            
            icons_to_draw.append( CC.GlobalPixmaps.ipfs )
            
        
        #
        
        service_types = [ services_manager.GetService( service_key ).GetServiceType() for service_key in pending ]
        
        if HC.FILE_REPOSITORY in service_types:
            
            icons_to_draw.append( CC.GlobalPixmaps.file_repository_pending )
            
        
        if HC.IPFS in service_types:
            
            icons_to_draw.append( CC.GlobalPixmaps.ipfs_pending )
            
        
        #
        
        service_types = [ services_manager.GetService( service_key ).GetServiceType() for service_key in petitioned ]
        
        if HC.FILE_REPOSITORY in service_types:
            
            icons_to_draw.append( CC.GlobalPixmaps.file_repository_petitioned )
            
        
        if HC.IPFS in service_types:
            
            icons_to_draw.append( CC.GlobalPixmaps.ipfs_petitioned )
            
        
        ICON_MARGIN = 1
        ICON_SPACING = 2
        
        top_left_x = thumbnail_border + ICON_MARGIN
        
        for icon_to_draw in icons_to_draw:
            
            painter.drawPixmap( top_left_x, thumbnail_border + ICON_MARGIN, icon_to_draw )
            
            top_left_x += icon_to_draw.width() + ICON_SPACING
            
        
        return qt_image
        
    
class ThumbnailMediaCollection( Thumbnail, ClientMedia.MediaCollection ):
    
    def __init__( self, file_service_key, media_results ):
        
        ClientMedia.MediaCollection.__init__( self, file_service_key, media_results )
        Thumbnail.__init__( self, file_service_key )
        
    
class ThumbnailMediaSingleton( Thumbnail, ClientMedia.MediaSingleton ):
    
    def __init__( self, file_service_key, media_result ):
        
        ClientMedia.MediaSingleton.__init__( self, media_result )
        Thumbnail.__init__( self, file_service_key )
        
    
