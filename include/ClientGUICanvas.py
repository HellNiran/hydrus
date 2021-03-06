from . import HydrusConstants as HC
from . import HydrusData
from . import HydrusExceptions
from . import HydrusGlobals as HG
from . import ClientCaches
from . import ClientConstants as CC
from . import ClientData
from . import ClientDuplicates
from . import ClientGUICommon
from . import ClientGUIDialogs
from . import ClientGUIDialogsManage
from . import ClientGUIDialogsQuick
from . import ClientGUIFunctions
from . import ClientGUIHoverFrames
from . import ClientGUIMedia
from . import ClientGUIMediaControls
from . import ClientGUIMenus
from . import ClientGUIMPV
from . import ClientGUIScrolledPanels
from . import ClientGUIScrolledPanelsButtonQuestions
from . import ClientGUIScrolledPanelsEdit
from . import ClientGUIScrolledPanelsManagement
from . import ClientGUIShortcuts
from . import ClientGUITags
from . import ClientGUITopLevelWindows
from . import ClientMedia
from . import ClientPaths
from . import ClientRatings
from . import ClientRendering
from . import ClientSearch
from . import ClientTags
from . import ClientThreading
import gc
from . import HydrusImageHandling
from . import HydrusPaths
from . import HydrusSerialisable
from . import HydrusTags
import os
import time
from . import QtPorting as QP
from qtpy import QtCore as QC
from qtpy import QtWidgets as QW
from qtpy import QtGui as QG
from . import QtPorting as QP

OPEN_EXTERNALLY_BUTTON_SIZE = ( 200, 45 )

def AddAudioVolumeMenu( menu, canvas_type ):
    
    mute_volume_type = None
    volume_volume_type = ClientGUIMediaControls.AUDIO_GLOBAL
    
    if canvas_type == ClientGUICommon.CANVAS_MEDIA_VIEWER:
        
        mute_volume_type = ClientGUIMediaControls.AUDIO_MEDIA_VIEWER
        
        if HG.client_controller.new_options.GetBoolean( 'media_viewer_uses_its_own_audio_volume' ):
            
            volume_volume_type = ClientGUIMediaControls.AUDIO_MEDIA_VIEWER
            
        
    elif canvas_type == ClientGUICommon.CANVAS_PREVIEW:
        
        mute_volume_type = ClientGUIMediaControls.AUDIO_PREVIEW
        
        if HG.client_controller.new_options.GetBoolean( 'preview_uses_its_own_audio_volume' ):
            
            volume_volume_type = ClientGUIMediaControls.AUDIO_PREVIEW
            
        
    
    volume_menu = QW.QMenu( menu )
    
    ( global_mute_option_name, global_volume_option_name ) = ClientGUIMediaControls.volume_types_to_option_names[ ClientGUIMediaControls.AUDIO_GLOBAL ]
    
    if HG.client_controller.new_options.GetBoolean( global_mute_option_name ):
        
        label = 'unmute global'
        
    else:
        
        label = 'mute global'
        
    
    ClientGUIMenus.AppendMenuItem( volume_menu, label, 'Mute/unmute audio.', ClientGUIMediaControls.FlipMute, ClientGUIMediaControls.AUDIO_GLOBAL )
    
    #
    
    if mute_volume_type is not None:
        
        ClientGUIMenus.AppendSeparator( volume_menu )
        
        ( mute_option_name, volume_option_name ) = ClientGUIMediaControls.volume_types_to_option_names[ mute_volume_type ]
        
        if HG.client_controller.new_options.GetBoolean( mute_option_name ):
            
            label = 'unmute {}'.format( ClientGUIMediaControls.volume_types_str_lookup[ mute_volume_type ] )
            
        else:
            
            label = 'mute {}'.format( ClientGUIMediaControls.volume_types_str_lookup[ mute_volume_type ] )
            
        
        ClientGUIMenus.AppendMenuItem( volume_menu, label, 'Mute/unmute audio.', ClientGUIMediaControls.FlipMute, mute_volume_type )
        
    
    #
    
    ClientGUIMenus.AppendSeparator( volume_menu )
    
    ( mute_option_name, volume_option_name ) = ClientGUIMediaControls.volume_types_to_option_names[ volume_volume_type ]
    
    # 0-100 inclusive
    volumes = list( range( 0, 110, 10 ) )
    
    current_volume = HG.client_controller.new_options.GetInteger( volume_option_name )
    
    if current_volume not in volumes:
        
        volumes.append( current_volume )
        
        volumes.sort()
        
    
    for volume in volumes:
        
        label = 'volume: {}'.format( volume )
        
        if volume == current_volume:
            
            ClientGUIMenus.AppendMenuCheckItem( volume_menu, label, 'Set the volume.', True, ClientGUIMediaControls.ChangeVolume, volume_volume_type, volume )
            
        else:
            
            ClientGUIMenus.AppendMenuItem( volume_menu, label, 'Set the volume.', ClientGUIMediaControls.ChangeVolume, volume_volume_type, volume )
            
        
    
    ClientGUIMenus.AppendMenu( menu, volume_menu, 'volume' )
    
def CalculateCanvasMediaSize( media, canvas_size, show_action ):
    
    ( canvas_width, canvas_height ) = canvas_size.toTuple()
    
    if ShouldHaveAnimationBar( media, show_action ):
        
        animated_scanbar_height = HG.client_controller.new_options.GetInteger( 'animated_scanbar_height' )
        
        canvas_height -= animated_scanbar_height
        
    
    canvas_width = max( canvas_width, 80 )
    canvas_height = max( canvas_height, 60 )
    
    return ( canvas_width, canvas_height )
    
def CalculateCanvasZooms( canvas, media, show_action ):
    
    if media is None:
        
        return ( 1.0, 1.0 )
        
    
    if show_action in ( CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY, CC.MEDIA_VIEWER_ACTION_SHOW_OPEN_EXTERNALLY_BUTTON, CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW ):
        
        return ( 1.0, 1.0 )
        
    
    ( media_width, media_height ) = media.GetResolution()
    
    if media_width == 0 or media_height == 0:
        
        return ( 1.0, 1.0 )
        
    
    new_options = HG.client_controller.new_options
    
    ( canvas_width, canvas_height ) = CalculateCanvasMediaSize( media, canvas.size(), show_action )
    
    width_zoom = canvas_width / media_width
    
    height_zoom = canvas_height / media_height
    
    canvas_zoom = min( ( width_zoom, height_zoom ) )
    
    #
    
    mime = media.GetMime()
    
    ( media_scale_up, media_scale_down, preview_scale_up, preview_scale_down, exact_zooms_only, scale_up_quality, scale_down_quality ) = new_options.GetMediaZoomOptions( mime )
    
    if exact_zooms_only:
        
        max_regular_zoom = 1.0
        
        if canvas_zoom > 1.0:
            
            while max_regular_zoom * 2 < canvas_zoom:
                
                max_regular_zoom *= 2
                
            
        elif canvas_zoom < 1.0:
            
            while max_regular_zoom > canvas_zoom:
                
                max_regular_zoom /= 2
                
            
        
    else:
        
        regular_zooms = new_options.GetMediaZooms()
        
        valid_regular_zooms = [ zoom for zoom in regular_zooms if zoom < canvas_zoom ]
        
        if len( valid_regular_zooms ) > 0:
            
            max_regular_zoom = max( valid_regular_zooms )
            
        else:
            
            max_regular_zoom = canvas_zoom
            
        
    
    if canvas.PREVIEW_WINDOW:
        
        scale_up_action = preview_scale_up
        scale_down_action = preview_scale_down
        
    else:
        
        scale_up_action = media_scale_up
        scale_down_action = media_scale_down
        
    
    can_be_scaled_down = media_width > canvas_width or media_height > canvas_height
    can_be_scaled_up = media_width < canvas_width and media_height < canvas_height
    
    #
    
    if can_be_scaled_up:
        
        scale_action = scale_up_action
        
    elif can_be_scaled_down:
        
        scale_action = scale_down_action
        
    else:
        
        scale_action = CC.MEDIA_VIEWER_SCALE_100
        
    
    if scale_action == CC.MEDIA_VIEWER_SCALE_100:
        
        default_zoom = 1.0
        
    elif scale_action == CC.MEDIA_VIEWER_SCALE_MAX_REGULAR:
        
        default_zoom = max_regular_zoom
        
    else:
        
        default_zoom = canvas_zoom
        
    
    return ( default_zoom, canvas_zoom )
    
def CalculateMediaContainerSize( media, zoom, show_action ):
    
    if show_action in ( CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY, CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW ):
        
        raise Exception( 'This media should not be shown in the media viewer!' )
        
    elif show_action == CC.MEDIA_VIEWER_ACTION_SHOW_OPEN_EXTERNALLY_BUTTON:
        
        ( width, height ) = OPEN_EXTERNALLY_BUTTON_SIZE
        
        if media.GetMime() in HC.MIMES_WITH_THUMBNAILS:
            
            ( thumb_width, thumb_height ) = HydrusImageHandling.GetThumbnailResolution( media.GetResolution(), HG.client_controller.options[ 'thumbnail_dimensions' ] )
            
            height = height + thumb_height
            
        
        return ( width, height )
        
    else:
        
        ( media_width, media_height ) = CalculateMediaSize( media, zoom )
        
        if ShouldHaveAnimationBar( media, show_action ):
            
            animated_scanbar_height = HG.client_controller.new_options.GetInteger( 'animated_scanbar_height' )
            
            media_height += animated_scanbar_height
            
        
        return ( media_width, media_height )
        
    
def CalculateMediaSize( media, zoom ):
    
    if media.GetMime() in HC.AUDIO:
        
        media_width = 360
        media_height = 240
        
    else:
        
        ( original_width, original_height ) = media.GetResolution()
        
        media_width = int( round( zoom * original_width ) )
        media_height = int( round( zoom * original_height ) )
        
    
    return ( media_width, media_height )
    
def ShouldHaveAnimationBar( media, show_action ):
    
    if show_action not in ( CC.MEDIA_VIEWER_ACTION_SHOW_WITH_NATIVE, CC.MEDIA_VIEWER_ACTION_SHOW_WITH_MPV ):
        
        return False
        
    
    is_audio = media.GetMime() in HC.AUDIO
    
    if is_audio:
        
        return True
        
    
    is_animated_image = media.GetMime() in HC.ANIMATIONS and media.HasDuration()
    
    is_video = media.GetMime() in HC.VIDEO
    
    num_frames = media.GetNumFrames()
    
    has_more_than_one_frame = num_frames is not None and num_frames > 1
    
    return ( is_animated_image or is_video ) and has_more_than_one_frame
    
class Animation( QW.QWidget ):
    
    def __init__( self, parent ):
        
        QW.QWidget.__init__( self, parent )
        
        self.setMouseTracking( True )
        
        self._media = None
        
        self._left_down_event = None
        
        self._something_valid_has_been_drawn = False
        self._has_played_once_through = False
        
        self._num_frames = 1
        
        self._current_frame_index = 0
        self._current_frame_drawn = False
        self._current_timestamp_ms = None
        self._next_frame_due_at = HydrusData.GetNowPrecise()
        self._slow_frame_score = 1.0
        
        self._paused = True
        
        self._video_container = None
        
        self._canvas_qt_pixmap = None
        
    
    def _ClearCanvasBitmap( self ):
        
        if self._canvas_qt_pixmap is not None:
            
            self._canvas_qt_pixmap = None
            
        
    
    def _TryToDrawCanvasBitmap( self ):
        
        if self._video_container is None:
            
            self._video_container = ClientRendering.RasterContainerVideo( self._media, self.size().toTuple(), init_position = self._current_frame_index )
            
        
        if not self._video_container.HasFrame( self._current_frame_index ):
            
            return
            
        
        my_size = self.size()
        
        my_width = my_size.width()
        my_height = my_size.height()
        
        if self._canvas_qt_pixmap is None:
            
            self._canvas_qt_pixmap = HG.client_controller.bitmap_manager.GetQtPixmap( my_width, my_height )
            
        
        painter = QG.QPainter( self._canvas_qt_pixmap )
        
        current_frame = self._video_container.GetFrame( self._current_frame_index )
        
        ( frame_width, frame_height ) = current_frame.GetSize()
        
        scale = my_width / frame_width
        
        painter.setTransform( QG.QTransform().scale( scale, scale ) )
        
        current_frame_image = current_frame.GetQtImage()
        
        painter.drawImage( 0, 0, current_frame_image )
        
        painter.setTransform( QG.QTransform().scale( 1.0, 1.0 ) )
        
        self._current_frame_drawn = True
        
        next_frame_time_s = self._video_container.GetDuration( self._current_frame_index ) / 1000.0
        
        next_frame_ideally_due = self._next_frame_due_at + next_frame_time_s
        
        if HydrusData.TimeHasPassedPrecise( next_frame_ideally_due ):
            
            self._next_frame_due_at = HydrusData.GetNowPrecise() + next_frame_time_s
            
        else:
            
            self._next_frame_due_at = next_frame_ideally_due
            
        
        self._something_valid_has_been_drawn = True
        
    
    def _DrawABlankFrame( self, painter ):
        
        new_options = HG.client_controller.new_options
        
        painter.setBackground( QG.QBrush( new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND ) ) )
        
        painter.eraseRect( painter.viewport() )
        
        self._something_valid_has_been_drawn = True
        
    
    def CurrentFrame( self ):
        
        return self._current_frame_index
        
    
    def GetAnimationBarStatus( self ):
        
        if self._video_container is None:
            
            buffer_indices = None
            
        else:
            
            buffer_indices = self._video_container.GetBufferIndices()
            
            if self._current_timestamp_ms is None and self._video_container.IsInitialised():
                
                self._current_timestamp_ms = self._video_container.GetTimestampMS( self._current_frame_index )
                
            
        
        return ( self._current_frame_index, self._current_timestamp_ms, self._paused, buffer_indices )
        
    
    def GotoFrame( self, frame_index ):
        
        if self._video_container is not None and self._video_container.IsInitialised():
            
            if frame_index != self._current_frame_index:
                
                self._current_frame_index = frame_index
                self._current_timestamp_ms = None
                
                self._next_frame_due_at = HydrusData.GetNowPrecise()
                
                self._video_container.GetReadyForFrame( self._current_frame_index )
                
                self._current_frame_drawn = False
                
            
            self._paused = True
            
        
    
    def HasPlayedOnceThrough( self ):
        
        return self._has_played_once_through
        
    
    def IsPlaying( self ):
        
        return not self._paused
        
    
    def mouseDoubleClickEvent( self, event ):
        
        if not ( event.modifiers() & ( QC.Qt.ShiftModifier | QC.Qt.ControlModifier | QC.Qt.AltModifier) ):
            
            if event.button() == QC.Qt.LeftButton:
                
                self.Pause()
                
                hash = self._media.GetHash()
                mime = self._media.GetMime()
                
                client_files_manager = HG.client_controller.client_files_manager
                
                path = client_files_manager.GetFilePath( hash, mime )
                
                new_options = HG.client_controller.new_options
                
                launch_path = new_options.GetMimeLaunch( mime )
                
                HydrusPaths.LaunchFile( path, launch_path )
                
                return
                
            
        
        event.ignore()
        
    
    def mousePressEvent( self, event ):
        
        if not ( event.modifiers() & ( QC.Qt.ShiftModifier | QC.Qt.ControlModifier | QC.Qt.AltModifier) ):
            
            if event.button() == QC.Qt.LeftButton:
                
                self.PausePlay()
                
                self.parentWidget().BeginDrag()
                
                return
                
            
        
        event.ignore()
        
    
    def paintEvent( self, event ):
        
        if not self._current_frame_drawn:
            
            self._TryToDrawCanvasBitmap()
            
        
        painter = QG.QPainter( self )
        
        if self._canvas_qt_pixmap is None:
            
            self._DrawABlankFrame( painter )
            
        else:
            
            painter.drawPixmap( 0, 0, self._canvas_qt_pixmap )
            
        
    
    def Pause( self ):
        
        self._paused = True
        
    
    def PausePlay( self ):
        
        self._paused = not self._paused
        
    
    def Play( self ):
        
        self._paused = False
        
    
    def resizeEvent( self, event ):
        
        ( my_width, my_height ) = self.size().toTuple()
        
        if my_width > 0 and my_height > 0:
            
            if self.size() != event.oldSize():
                
                self._ClearCanvasBitmap()
                
                self._current_frame_drawn = False
                self._something_valid_has_been_drawn = False
                
                self.update()
                
                if self._media is not None:
                    
                    ( media_width, media_height ) = self._media.GetResolution()
                    
                    if self._video_container is not None:
                        
                        ( renderer_width, renderer_height ) = self._video_container.GetSize()
                        
                        we_just_zoomed_in = my_width > renderer_width or my_height > renderer_height
                        we_just_zoomed_out = my_width < renderer_width or my_height < renderer_height
                        
                        if we_just_zoomed_in:
                            
                            if self._video_container.IsScaled():
                                
                                target_width = min( media_width, my_width )
                                target_height = min( media_height, my_height )
                                
                                self._video_container.Stop()
                                
                                self._video_container = ClientRendering.RasterContainerVideo( self._media, ( target_width, target_height ), init_position = self._current_frame_index )
                                
                            
                        elif we_just_zoomed_out:
                            
                            if my_width < media_width or my_height < media_height: # i.e. new zoom is scaled
                                
                                self._video_container.Stop()
                                
                                self._video_container = ClientRendering.RasterContainerVideo( self._media, ( my_width, my_height ), init_position = self._current_frame_index )
                                
                            
                        
                    
                
            
        
    
    def SetMedia( self, media, start_paused = False ):
        
        self._media = media
        
        self._left_down_event = None
        
        self._ClearCanvasBitmap()
        
        self._something_valid_has_been_drawn = False
        self._has_played_once_through = False
        
        if self._media is not None:
            
            self._num_frames = self._media.GetNumFrames()
            
        else:
            
            self._num_frames = 1
            
        
        self._current_frame_index = int( ( self._num_frames - 1 ) * HC.options[ 'animation_start_position' ] )
        self._current_frame_drawn = False
        self._current_timestamp_ms = None
        self._next_frame_due_at = HydrusData.GetNowPrecise()
        self._slow_frame_score = 1.0
        
        self._paused = start_paused
        
        if self._video_container is not None:
            
            self._video_container.Stop()
            
        
        self._video_container = None
        
        if self._media is None:
            
            HG.client_controller.gui.UnregisterAnimationUpdateWindow( self )
            
        else:
            
            HG.client_controller.gui.RegisterAnimationUpdateWindow( self )
            
            self.update()
            
        
    
    def SetNoneMedia( self ):
        
        self.SetMedia( None )
        
    
    def TIMERAnimationUpdate( self ):
        
        if self._media is None:
            
            return
            
        
        try:
            
            if self.isVisible():
                
                if self._current_frame_drawn:
                    
                    if not self._paused and HydrusData.TimeHasPassedPrecise( self._next_frame_due_at ):
                        
                        num_frames = self._media.GetNumFrames()
                        
                        self._current_frame_index = ( self._current_frame_index + 1 ) % num_frames
                        
                        if self._current_frame_index == 0:
                            
                            self._current_timestamp_ms = 0
                            self._has_played_once_through = True
                            
                        else:
                            
                            if self._current_timestamp_ms is not None and self._video_container is not None and self._video_container.IsInitialised():
                                
                                duration_ms = self._video_container.GetDuration( self._current_frame_index - 1 )
                                
                                self._current_timestamp_ms += duration_ms
                                
                            
                        
                        self._current_frame_drawn = False
                        
                    
                
                if self._video_container is not None:
                    
                    if not self._current_frame_drawn:
                        
                        if self._video_container.HasFrame( self._current_frame_index ):
                            
                            self.update()
                            
                        
                    
                
            
        except:
            
            HG.client_controller.gui.UnregisterAnimationUpdateWindow( self )
            
            raise
            
        
    
class AnimationBar( QW.QWidget ):
    
    def __init__( self, parent ):
        
        QW.QWidget.__init__( self, parent )
        
        self.setCursor( QG.QCursor( QC.Qt.ArrowCursor ) )
        
        self._media_window = None
        self._duration_ms = 1000
        self._num_frames = 1
        self._last_drawn_info = None
        
        self._has_experienced_mouse_down = False
        self._currently_in_a_drag = False
        self._it_was_playing = False
        
        self._widget_event_filter = QP.WidgetEventFilter( self )
        self._widget_event_filter.EVT_MOUSE_EVENTS( self.EventMouse )    
        
    
    def _DrawBlank( self, painter ):
        
        new_options = HG.client_controller.new_options
        
        painter.setBackground( QG.QBrush( new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND ) ) )
        
        painter.eraseRect( painter.viewport() )
        
    
    def _GetAnimationBarStatus( self ):
        
        return self._media_window.GetAnimationBarStatus() 
        
    
    def _GetXFromFrameIndex( self, index, width_offset = 0 ):
        
        if self._num_frames is None or self._num_frames < 2:
            
            return 0
            
        
        ( my_width, my_height ) = self.size().toTuple()
        
        return int( ( my_width - width_offset ) * index / ( self._num_frames - 1 ) )
        
    
    def _GetXFromTimestamp( self, timestamp_ms, width_offset = 0 ):
        
        ( my_width, my_height ) = self.size().toTuple()
        
        return int( ( my_width - width_offset ) * timestamp_ms / self._duration_ms )
        
    
    def _Redraw( self, painter ):
        
        self._last_drawn_info = self._GetAnimationBarStatus()
        
        ( current_frame_index, current_timestamp_ms, paused, buffer_indices )  = self._last_drawn_info
        
        ( my_width, my_height ) = self.size().toTuple()
        
        painter.setPen( QC.Qt.NoPen )
        
        background_colour = QP.GetSystemColour( QG.QPalette.Button )
        
        if paused:
            
            background_colour = ClientData.GetLighterDarkerColour( background_colour )
            
        
        painter.setBackground( QG.QBrush( background_colour ) )
        
        painter.eraseRect( painter.viewport() )
        
        #
        
        animated_scanbar_height = HG.client_controller.new_options.GetInteger( 'animated_scanbar_height' )
        
        if buffer_indices is not None:
            
            ( start_index, rendered_to_index, end_index ) = buffer_indices
            
            if ClientRendering.FrameIndexOutOfRange( rendered_to_index, start_index, end_index ):
                
                rendered_to_index = start_index
                
            
            start_x = self._GetXFromFrameIndex( start_index )
            rendered_to_x = self._GetXFromFrameIndex( rendered_to_index )
            end_x = self._GetXFromFrameIndex( end_index )
            
            if start_x != rendered_to_x:
                
                rendered_colour = ClientData.GetDifferentLighterDarkerColour( background_colour )
                
                painter.setBrush( QG.QBrush( rendered_colour ) )
                
                if rendered_to_x > start_x:
                    
                    painter.drawRect( start_x, 0, rendered_to_x - start_x, animated_scanbar_height )
                    
                else:
                    
                    painter.drawRect( start_x, 0, my_width - start_x, animated_scanbar_height )
                    
                    painter.drawRect( 0, 0, rendered_to_x, animated_scanbar_height )
                    
                
            
            if rendered_to_x != end_x:
                
                to_be_rendered_colour = ClientData.GetDifferentLighterDarkerColour( background_colour, 1 )
                
                painter.setBrush( QG.QBrush( to_be_rendered_colour ) )
                
                if end_x > rendered_to_x:
                    
                    painter.drawRect( rendered_to_x, 0, end_x - rendered_to_x, animated_scanbar_height )
                    
                else:
                    
                    painter.drawRect( rendered_to_x, 0, my_width - rendered_to_x, animated_scanbar_height )
                    
                    painter.drawRect( 0, 0, end_x, animated_scanbar_height )
                    
                
            
        
        painter.setBrush( QG.QBrush( QP.GetSystemColour( QG.QPalette.Shadow ) ) )
        
        animated_scanbar_nub_width = HG.client_controller.new_options.GetInteger( 'animated_scanbar_nub_width' )
        
        nub_x = None
        
        if self._num_frames is not None and current_frame_index is not None:
            
            nub_x = self._GetXFromFrameIndex( current_frame_index, width_offset = animated_scanbar_nub_width )
            
        elif self._duration_ms is not None and current_timestamp_ms is not None:
            
            nub_x = self._GetXFromTimestamp( current_timestamp_ms, width_offset = animated_scanbar_nub_width )
            
        
        if nub_x is not None:
            
            painter.drawRect( nub_x, 0, animated_scanbar_nub_width, animated_scanbar_height )
            
        
        #
        
        painter.setPen( QG.QPen() )
        
        progress_strings = []
        
        if self._num_frames is not None:
            
            progress_strings.append( HydrusData.ConvertValueRangeToPrettyString( current_frame_index + 1, self._num_frames ) )
            
        
        if current_timestamp_ms is not None:
            
            progress_strings.append( HydrusData.ConvertValueRangeToScanbarTimestampsMS( current_timestamp_ms, self._duration_ms ) )
            
        
        s = ' - '.join( progress_strings )
        
        if len( s ) > 0:
            
            ( x, y ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, s ).toTuple()
            
            QP.DrawText( painter, my_width-x-3, 3, s )
            
        
    
    def EventMouse( self, event ):
        
        if self._media_window is not None:
            
            if not self._media_window or not QP.isValid( self._media_window ):
                
                self.SetNoneMedia()
                
                return
                
            
            CC.CAN_HIDE_MOUSE = False
            
            if event.type() == QC.QEvent.MouseButtonPress:
                
                self._has_experienced_mouse_down = True
                
            
            # sometimes, this can inherit mouse-down from previous filter or embed button reveal, resulting in undesired scan
            
            if not self._has_experienced_mouse_down:
                
                return
                
            
            ( my_width, my_height ) = self.size().toTuple()
            
            if event.type() == QC.QEvent.MouseMove and event.buttons() != QC.Qt.NoButton:
                
                self._currently_in_a_drag = True
                
            
            a_button_is_down = event.buttons() != QC.Qt.NoButton
            
            if a_button_is_down:
                
                if not self._currently_in_a_drag:
                    
                    self._it_was_playing = self._media_window.IsPlaying()
                    
                
                event_pos = event.pos()
                
                animated_scanbar_nub_width = HG.client_controller.new_options.GetInteger( 'animated_scanbar_nub_width' )
                
                compensated_x_position = event_pos.x() - ( animated_scanbar_nub_width / 2 )
                
                proportion = ( compensated_x_position ) / ( my_width - animated_scanbar_nub_width )
                
                if proportion < 0: proportion = 0
                if proportion > 1: proportion = 1
                
                self.update()
                
                if isinstance( self._media_window, Animation ):
                    
                    current_frame_index = int( proportion * ( self._num_frames - 1 ) + 0.5 )
                    
                    self._media_window.GotoFrame( current_frame_index )
                    
                elif isinstance( self._media_window, ClientGUIMPV.mpvWidget ):
                    
                    time_index_ms = int( proportion * self._duration_ms )
                    
                    self._media_window.Seek( time_index_ms )
                    
                
            elif event.type() == QC.QEvent.MouseButtonRelease:
                
                if self._it_was_playing:
                    
                    self._media_window.Play()
                    
                
                self._currently_in_a_drag = False
                
            
        
    
    def paintEvent( self, event ):
        
        painter = QG.QPainter( self )
        
        if self._media_window is None:
            
            self._DrawBlank( painter )
            
        else:
            
            self._Redraw( painter )
            
        
    
    def SetMediaAndWindow( self, media, media_window ):
        
        self._media_window = media_window
        self._duration_ms = max( media.GetDuration(), 1 )
        
        num_frames = media.GetNumFrames()
        
        if num_frames is None:
            
            self._num_frames = num_frames
            
        else:
            
            self._num_frames = max( num_frames, 1 )
            
        
        self._last_drawn_info = None
        
        self._has_experienced_mouse_down = False
        self._currently_in_a_drag = False
        self._it_was_playing = False
        
        HG.client_controller.gui.RegisterAnimationUpdateWindow( self )
        
        self.update()
        
    
    def SetNoneMedia( self ):
        
        self._media_window = None
        
        HG.client_controller.gui.UnregisterAnimationUpdateWindow( self )
        
        self.update()
        
    
    def TIMERAnimationUpdate( self ):
        
        if self.isVisible():
            
            if not self._media_window or not QP.isValid( self._media_window ):
                
                self.SetNoneMedia()
                
                return
                
            
            if self._last_drawn_info != self._GetAnimationBarStatus():
                
                self.update()
                
            
        
    
class CanvasFrame( ClientGUITopLevelWindows.FrameThatResizes ):
    
    def __init__( self, parent ):            
        
        # Parent is set to None here so that this window shows up as a separate entry on the taskbar
        ClientGUITopLevelWindows.FrameThatResizes.__init__( self, None, 'hydrus client media viewer', 'media_viewer' )
        
        self._canvas_window = None
        
        self._my_shortcut_handler = ClientGUIShortcuts.ShortcutsHandler( self, [ 'global', 'media_viewer' ] )
        
        HG.client_controller.gui.RegisterCanvasFrameReference( self )
        
        self.destroyed.connect( HG.client_controller.gui.MaintainCanvasFrameReferences )
        
    
    def closeEvent( self, event ):
        
        if self._canvas_window is not None:
            
            can_close = self._canvas_window.TryToDoPreClose()
            
            if can_close:
                
                self._canvas_window.CleanBeforeDestroy()
                
                ClientGUITopLevelWindows.FrameThatResizes.closeEvent( self, event )
                
            else:
                
                event.ignore()
                
            
        else:
            
            ClientGUITopLevelWindows.FrameThatResizes.closeEvent( self, event )
            
        
    
    def FullscreenSwitch( self ):
        
        if self.isFullScreen():
            
            self.showNormal()
            
        else:
            
            if HC.PLATFORM_MACOS:
                
                return
                
            
            self.showFullScreen()
            
        
        self._canvas_window.ResetMediaWindowCenterPosition()
        
    
    def ProcessApplicationCommand( self, command ):
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'switch_between_fullscreen_borderless_and_regular_framed_window':
                
                self.FullscreenSwitch()
                
            elif action == 'flip_darkmode':
                
                HG.client_controller.gui.FlipDarkmode()
                
            elif action == 'global_audio_mute':
                
                ClientGUIMediaControls.SetMute( ClientGUIMediaControls.AUDIO_GLOBAL, True )
                
            elif action == 'global_audio_unmute':
                
                ClientGUIMediaControls.SetMute( ClientGUIMediaControls.AUDIO_GLOBAL, False )
                
            elif action == 'global_audio_mute_flip':
                
                ClientGUIMediaControls.FlipMute( ClientGUIMediaControls.AUDIO_GLOBAL )
                
            else:
                
                command_processed = False
                
            
        else:
            
            command_processed = False
            
        
        return command_processed
        
    
    def minimumSizeHint( self ):
        
        return QC.QSize( 240, 180 )
        
    
    def SetCanvas( self, canvas_window ):
        
        self._canvas_window = canvas_window
        
        self.setFocusProxy( self._canvas_window )
        
        vbox = QP.VBoxLayout( margin = 0 )
        
        QP.AddToLayout( vbox, self._canvas_window )
        
        self.setLayout( vbox )
        
        ClientGUITopLevelWindows.SetInitialTLWSizeAndPosition( self, self._frame_key )
        
        self.show()
        
        # just to reinforce, as Qt sometimes sets none focus for this window until it goes off and back on
        self._canvas_window.setFocus( QC.Qt.OtherFocusReason )
        
    
    def TakeFocusForUser( self ):
        
        self.activateWindow()
        
        self._canvas_window.setFocus( QC.Qt.OtherFocusReason )
        
    
class Canvas( QW.QWidget ):
    
    PREVIEW_WINDOW = False
    
    def __init__( self, parent ):
        
        QW.QWidget.__init__( self, parent )
        
        self.setSizePolicy( QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding )
        
        self._file_service_key = CC.LOCAL_FILE_SERVICE_KEY
        
        self._current_media_start_time = HydrusData.GetNow()
        
        self._reserved_shortcut_names = []
        
        self._reserved_shortcut_names.append( 'media' )
        self._reserved_shortcut_names.append( 'media_viewer' )
        
        self._new_options = HG.client_controller.new_options
        
        self._custom_shortcut_names = self._new_options.GetStringList( 'default_media_viewer_custom_shortcuts' )
        
        self._canvas_key = HydrusData.GenerateKey()
        
        self._maintain_pan_and_zoom = False
        
        self._service_keys_to_services = {}
        
        self._current_media = None
        
        if self.PREVIEW_WINDOW:
            
            self._canvas_type = ClientGUICommon.CANVAS_PREVIEW
            
        else:
            
            self._canvas_type = ClientGUICommon.CANVAS_MEDIA_VIEWER
            
        
        self._media_container = MediaContainer( self, self._canvas_type )
        
        self._current_zoom = 1.0
        self._canvas_zoom = 1.0
        
        self._last_drag_pos = None
        self._current_drag_is_touch = False
        self._last_motion_pos = QC.QPoint( 0, 0 )
        self._media_window_pos = QC.QPoint( 0, 0 )
        
        self._UpdateBackgroundColour()
        
        self._widget_event_filter = QP.WidgetEventFilter( self )
        
        HG.client_controller.sub( self, 'ZoomIn', 'canvas_zoom_in' )
        HG.client_controller.sub( self, 'ZoomOut', 'canvas_zoom_out' )
        HG.client_controller.sub( self, 'ZoomSwitch', 'canvas_zoom_switch' )
        HG.client_controller.sub( self, 'OpenExternally', 'canvas_open_externally' )
        HG.client_controller.sub( self, 'ManageTags', 'canvas_manage_tags' )
        HG.client_controller.sub( self, 'ProcessApplicationCommand', 'canvas_application_command' )
        HG.client_controller.sub( self, '_UpdateBackgroundColour', 'notify_new_colourset' )
        HG.client_controller.sub( self, 'update', 'notify_new_colourset' )
        
    
    def _Archive( self ):
        
        if self._current_media is not None:
            
            HG.client_controller.Write( 'content_updates', { CC.COMBINED_LOCAL_FILE_SERVICE_KEY : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_ARCHIVE, ( self._current_media.GetHash(), ) ) ] } )
            
        
    
    def _CanDisplayMedia( self, media ):
        
        if media is None:
            
            return True
            
        
        media = media.GetDisplayMedia()
        
        locations_manager = media.GetLocationsManager()
        
        if not locations_manager.IsLocal():
            
            return False
            
        
        ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( media )
        
        if media_show_action in ( CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY, CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW ):
            
            return False
            
        
        return True
        
    
    def _CopyBMPToClipboard( self ):
        
        if self._current_media is not None:
            
            if self._current_media.GetMime() in HC.IMAGES:
                
                HG.client_controller.pub( 'clipboard', 'bmp', self._current_media )
                
            else:
                
                QW.QMessageBox.critical( self, 'Error', 'Sorry, cannot take bmps of anything but static images right now!' )
                
            
        
    
    def _CopyHashToClipboard( self, hash_type ):
        
        sha256_hash = self._current_media.GetHash()
        
        if hash_type == 'sha256':
            
            hex_hash = sha256_hash.hex()
            
        else:
            
            if self._current_media.GetLocationsManager().IsLocal():
                
                ( other_hash, ) = HG.client_controller.Read( 'file_hashes', ( sha256_hash, ), 'sha256', hash_type )
                
                hex_hash = other_hash.hex()
                
            else:
                
                QW.QMessageBox.warning( self, 'Warning', 'Unfortunately, you do not have that file in your database, so its non-sha256 hashes are unknown.' )
                
                return
                
            
        
        HG.client_controller.pub( 'clipboard', 'text', hex_hash )
        
    
    def _CopyFileToClipboard( self ):
        
        if self._current_media is not None:
            
            client_files_manager = HG.client_controller.client_files_manager
            
            paths = [ client_files_manager.GetFilePath( self._current_media.GetHash(), self._current_media.GetMime() ) ]
            
            HG.client_controller.pub( 'clipboard', 'paths', paths )
            
        
    
    def _CopyPathToClipboard( self ):
        
        if self._current_media is not None:
            
            client_files_manager = HG.client_controller.client_files_manager
            
            path = client_files_manager.GetFilePath( self._current_media.GetHash(), self._current_media.GetMime() )
            
            HG.client_controller.pub( 'clipboard', 'text', path )
            
        
    
    def _Delete( self, media = None, default_reason = None, file_service_key = None ):
        
        if media is None:
            
            if self._current_media is None:
                
                return False
                
            
            media = [ self._current_media ]
            
        
        if default_reason is None:
            
            default_reason = 'Deleted from Preview or Media Viewer.'
            
        
        try:
            
            ( involves_physical_delete, jobs ) = ClientGUIDialogsQuick.GetDeleteFilesJobs( self, media, default_reason, suggested_file_service_key = file_service_key )
            
        except HydrusExceptions.CancelledException:
            
            return False
            
        
        def do_it( jobs ):
            
            for service_keys_to_content_updates in jobs:
                
                HG.client_controller.WriteSynchronous( 'content_updates', service_keys_to_content_updates )
                
            
        
        HG.client_controller.CallToThread( do_it, jobs )
        
        return True
        
    
    def _DoEdgePan( self, pan_type ):
        
        if self._current_media is None:
            
            return
            
        
        my_size = self.size()
        media_size = self._media_container.size()
        
        delta_x = 0
        delta_y = 0
        
        if pan_type == 'pan_top_edge':
            
            delta_y = - self._media_window_pos.y()
            
        elif pan_type == 'pan_left_edge':
            
            delta_x = - self._media_window_pos.x()
            
        elif pan_type == 'pan_bottom_edge':
            
            delta_y = my_size.height() - ( self._media_window_pos.y() + media_size.height() )
            
        elif pan_type == 'pan_right_edge':
            
            delta_x = my_size.width() - ( self._media_window_pos.x() + media_size.width() )
            
        elif pan_type == 'pan_vertical_center':
            
            delta_y = ( my_size.height() / 2 ) - ( self._media_window_pos.y() + ( media_size.height() / 2 ) )
            
        elif pan_type == 'pan_horizontal_center':
            
            delta_x = ( my_size.width() / 2 ) - ( self._media_window_pos.x() + ( media_size.width() / 2 ) )
            
        
        delta = QC.QPoint( delta_x, delta_y )
        
        self._media_window_pos += delta
        
        self._DrawCurrentMedia()
        
    
    def _DoManualPan( self, delta_x_step, delta_y_step ):
        
        if self._current_media is None:
            
            return
            
        
        my_size = self.size()
        media_size = self._media_container.size()
        
        x_pan_distance = min( my_size.width(), media_size.width() ) // 12
        y_pan_distance = min( my_size.height(), media_size.height() ) // 12
        
        delta_x = delta_x_step * x_pan_distance
        delta_y = delta_y_step * y_pan_distance
        
        delta = QC.QPoint( delta_x, delta_y )
        
        self._media_window_pos += delta
        
        self._DrawCurrentMedia()
        
    
    def _DrawBackgroundBitmap( self, painter ):
        
        background_colour = self._GetBackgroundColour()
        
        painter.setBackground( QG.QBrush( background_colour ) )
        
        painter.eraseRect( painter.viewport() )
        
        self._DrawBackgroundDetails( painter )
        
    
    def _DrawBackgroundDetails( self, painter ):
        
        pass
        
    
    def _DrawCurrentMedia( self ):
        
        if self._current_media is None:
            
            return
            
        
        ( my_width, my_height ) = self.size().toTuple()
        
        if my_width > 0 and my_height > 0:
            
            self._SizeAndPositionMediaContainer()
            
        
    
    def _GenerateOrderedShortcutNames( self ):
        
        # do custom first, then let the more specialised take priority
        
        shortcut_names = self._reserved_shortcut_names + self._custom_shortcut_names
        
        shortcut_names.reverse()
        
        return shortcut_names
        
    
    def _GetBackgroundColour( self ):
        
        return self._new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND )
        
    
    def _GetShowAction( self, media ):
        
        start_paused = False
        start_with_embed = False
        
        bad_result = ( CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW, start_paused, start_with_embed )
        
        if media is None:
            
            return bad_result
            
        
        mime = media.GetMime()
        
        if mime not in HC.ALLOWED_MIMES: # stopgap to catch a collection or application_unknown due to unusual import order/media moving
            
            return bad_result
            
        
        if self.PREVIEW_WINDOW:
            
            return self._new_options.GetPreviewShowAction( mime )
            
        else:
            
            return self._new_options.GetMediaShowAction( mime )
            
        
    
    def _GetIndexString( self ):
        
        return ''
        
    
    def _GetMediaContainerSize( self ):
        
        ( my_width, my_height ) = self.size().toTuple()
        
        ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( self._current_media )
        
        ( media_width, media_height ) = CalculateMediaContainerSize( self._current_media, self._current_zoom, media_show_action )
        
        new_size = ( media_width, media_height )
        
        return new_size
        
    
    def _Inbox( self ):
        
        if self._current_media is None:
            
            return
            
        
        HG.client_controller.Write( 'content_updates', { CC.COMBINED_LOCAL_FILE_SERVICE_KEY : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_INBOX, ( self._current_media.GetHash(), ) ) ] } )
        
    
    def _IsZoomable( self ):
        
        if self._current_media is None:
            
            return False
            
        
        ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( self._current_media )
        
        return media_show_action not in ( CC.MEDIA_VIEWER_ACTION_SHOW_OPEN_EXTERNALLY_BUTTON, CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY, CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW )
        
    
    def _IShouldCatchShortcutEvent( self, event = None ):
        
        return ClientGUIShortcuts.IShouldCatchShortcutEvent( self, event = event, child_tlw_classes_who_can_pass_up = ( ClientGUIHoverFrames.FullscreenHoverFrame, ) )
        
    
    def _MaintainZoom( self, previous_media ):
        
        if previous_media is None:
            
            self._ReinitZoom()
            
        else:
            
            if self._current_media is None:
                
                return
                
            
            # set up canvas zoom
            
            ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( self._current_media )
            
            ( gumpf_current_zoom, self._canvas_zoom ) = CalculateCanvasZooms( self, self._current_media, media_show_action )
            
            # for init zoom, we want the _width_ to stay the same as previous
            
            ( previous_width, previous_height ) = CalculateMediaSize( previous_media, self._current_zoom )
            
            ( current_media_100_width, current_media_100_height ) = self._current_media.GetResolution()
            
            self._current_zoom = previous_width / current_media_100_width
            
            HG.client_controller.pub( 'canvas_new_zoom', self._canvas_key, self._current_zoom )
            
            # and fix drag delta, or rewangle this so drag delta is offset to start with anyway m8, yeah
            
        
    
    def _ManageNotes( self ):
        
        def qt_do_it( media, notes ):
            
            if not self or not QP.isValid( self ):
                
                return
                
            
            title = 'manage notes'
            
            with ClientGUITopLevelWindows.DialogEdit( self, title ) as dlg:
                
                panel = ClientGUIScrolledPanels.EditSingleCtrlPanel( dlg, [ 'manage_file_notes' ] )
                
                control = QW.QPlainTextEdit( panel )
                
                ( min_width, min_height ) = ClientGUIFunctions.ConvertTextToPixels( control, ( 80, 14 ) )
                
                control.setMinimumWidth( min_width )
                control.setMinimumHeight( min_height )
                
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
                    
                
            
        
        def thread_wait( media ):
            
            # if it ultimately makes sense, I can load/cache notes in the media result
            
            notes = HG.client_controller.Read( 'file_notes', media.GetHash() )
            
            QP.CallAfter( qt_do_it, media, notes )
            
        
        if self._current_media is None:
            
            return
            
        
        HG.client_controller.CallToThread( thread_wait, self._current_media )
        
    
    def _ManageRatings( self ):
        
        if self._current_media is None:
            
            return
            
        
        if len( HG.client_controller.services_manager.GetServices( HC.RATINGS_SERVICES ) ) > 0:
            
            with ClientGUIDialogsManage.DialogManageRatings( self, ( self._current_media, ) ) as dlg:
                
                dlg.exec()
                
            
        
    
    def _ManageTags( self ):
        
        if self._current_media is None:
            
            return
            
        
        for child in self.children():
            
            if isinstance( child, ClientGUITopLevelWindows.FrameThatTakesScrollablePanel ):
                
                panel = child.GetPanel()
                
                if isinstance( panel, ClientGUITags.ManageTagsPanel ):
                    
                    child.activateWindow()
                    
                    command = ClientData.ApplicationCommand( CC.APPLICATION_COMMAND_TYPE_SIMPLE, 'set_search_focus' )
                    
                    panel.ProcessApplicationCommand( command )
                    
                    return
                    
                
            
        
        # take any focus away from hover window, which will mess up window order when it hides due to the new frame
        self.setFocus( QC.Qt.OtherFocusReason )
        
        title = 'manage tags'
        frame_key = 'manage_tags_frame'
        
        manage_tags = ClientGUITopLevelWindows.FrameThatTakesScrollablePanel( self, title, frame_key )
        
        panel = ClientGUITags.ManageTagsPanel( manage_tags, self._file_service_key, ( self._current_media, ), immediate_commit = True, canvas_key = self._canvas_key )
        
        manage_tags.SetPanel( panel )
        
    
    def _ManageURLs( self ):
        
        if self._current_media is None:
            
            return
            
        
        title = 'manage known urls'
        
        with ClientGUITopLevelWindows.DialogManage( self, title ) as dlg:
            
            panel = ClientGUIScrolledPanelsManagement.ManageURLsPanel( dlg, ( self._current_media, ) )
            
            dlg.SetPanel( panel )
            
            dlg.exec()
            
        
    
    def _MediaFocusWentToExternalProgram( self ):
        
        if self._current_media is None:
            
            return
            
        
        mime = self._current_media.GetMime()
        
        if self._current_media.HasDuration():
            
            self._media_container.Pause()
            
        
    
    def _OpenExternally( self ):
        
        if self._current_media is None:
            
            return
            
        
        hash = self._current_media.GetHash()
        mime = self._current_media.GetMime()
        
        client_files_manager = HG.client_controller.client_files_manager
        
        path = client_files_manager.GetFilePath( hash, mime )
        
        launch_path = self._new_options.GetMimeLaunch( mime )
        
        HydrusPaths.LaunchFile( path, launch_path )
        
        self._MediaFocusWentToExternalProgram()
        
    
    def _OpenFileInWebBrowser( self ):
        
        if self._current_media is not None:
            
            hash = self._current_media.GetHash()
            mime = self._current_media.GetMime()
            
            client_files_manager = HG.client_controller.client_files_manager
            
            path = client_files_manager.GetFilePath( hash, mime )
            
            ClientPaths.LaunchPathInWebBrowser( path )
            
            self._MediaFocusWentToExternalProgram()
            
        
    
    def _OpenFileLocation( self ):
        
        if self._current_media is not None:
            
            hash = self._current_media.GetHash()
            mime = self._current_media.GetMime()
            
            client_files_manager = HG.client_controller.client_files_manager
            
            path = client_files_manager.GetFilePath( hash, mime )
            
            HydrusPaths.OpenFileLocation( path )
            
            self._MediaFocusWentToExternalProgram()
            
        
    
    def _OpenKnownURL( self ):
        
        if self._current_media is not None:
            
            ClientGUIMedia.DoOpenKnownURLFromShortcut( self, self._current_media )
            
        
    
    def _PauseCurrentMedia( self ):
        
        if self._current_media is None:
            
            return
            
        
        self._media_container.Pause()
        
    
    def _PausePlayCurrentMedia( self ):
        
        if self._current_media is None:
            
            return
            
        
        self._media_container.PausePlay()
        
    
    def _PrefetchNeighbours( self ):
        
        pass
        
    
    def _ProcessShortcut( self, shortcut ):
        
        shortcut_processed = False
        
        shortcut_names = self._GenerateOrderedShortcutNames()
        
        command = HG.client_controller.GetCommandFromShortcut( shortcut_names, shortcut )
        
        if command is not None:
            
            command_processed = self.ProcessApplicationCommand( command )
            
            shortcut_processed = command_processed
            
        
        return shortcut_processed
        
    
    def _ReinitZoom( self ):
        
        if self._current_media is None:
            
            return
            
        
        ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( self._current_media )
        
        ( self._current_zoom, self._canvas_zoom ) = CalculateCanvasZooms( self, self._current_media, media_show_action )
        
        HG.client_controller.pub( 'canvas_new_zoom', self._canvas_key, self._current_zoom )
        
    
    def _ResetMediaWindowCenterPosition( self ):
        
        if self._current_media is None:
            
            return
            
        
        my_size = self.size()
        
        ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( self._current_media )
        
        ( media_width, media_height ) = CalculateMediaContainerSize( self._current_media, self._current_zoom, media_show_action )
        
        x = ( my_size.width() - media_width ) // 2
        y = ( my_size.height() - media_height ) // 2
        
        self._media_window_pos = QC.QPoint( x, y )
        
        self._last_drag_pos = None
        
    
    def _SaveCurrentMediaViewTime( self ):
        
        now = HydrusData.GetNow()
        
        viewtime_delta = now - self._current_media_start_time
        
        self._current_media_start_time = now
        
        if self._current_media is None:
            
            return
            
        
        if self.PREVIEW_WINDOW:
            
            viewtype = 'preview'
            
        else:
            
            if isinstance( self, CanvasFilterDuplicates ):
                
                viewtype = 'media_duplicates_filter'
                
            else:
                
                viewtype = 'media'
                
            
        
        hash = self._current_media.GetHash()
        
        HG.client_controller.file_viewing_stats_manager.FinishViewing( viewtype, hash, viewtime_delta )
        
    
    def _ShowMediaInNewPage( self ):
        
        if self._current_media is None:
            
            return
            
        
        hash = self._current_media.GetHash()
        
        hashes = { hash }
        
        HG.client_controller.pub( 'new_page_query', self._file_service_key, initial_hashes = hashes )
        
    
    def _SizeAndPositionMediaContainer( self ):
        
        if self._current_media is None:
            
            return
            
        
        new_size = self._GetMediaContainerSize()
        
        if new_size != self._media_container.size().toTuple():
            
            self._media_container.setFixedSize( QP.TupleToQSize( new_size ) )
            
        
        if self._media_window_pos == self._media_container.pos():
            
            if HC.PLATFORM_MACOS:
                
                self._media_container.update()
                
            
        else:
            
            self._media_container.move( self._media_window_pos )
            
        
    
    def _TryToChangeZoom( self, new_zoom ):
        
        if self._current_media is None:
            
            return
            
        
        ( media_window_width, media_window_height ) = self._media_container.size().toTuple()
        
        ( new_media_window_width, new_media_window_height ) = CalculateMediaSize( self._current_media, new_zoom )
        
        my_size = self.size()
        
        old_size_bigger = my_size.width() < media_window_width or my_size.height() < media_window_height
        new_size_fits = my_size.width() >= new_media_window_width and my_size.height() >= new_media_window_height
        
        width_delta = media_window_width - new_media_window_width
        height_delta = media_window_height - new_media_window_height
        
        half_delta = QC.QPoint( width_delta // 2, height_delta // 2 )
        
        self._media_window_pos += half_delta
        
        self._current_zoom = new_zoom
        
        HG.client_controller.pub( 'canvas_new_zoom', self._canvas_key, self._current_zoom )
        
        if old_size_bigger and new_size_fits:
            
            self._ResetMediaWindowCenterPosition()
            
        
        # due to the foolish 'giganto window' system for large zooms, some auto-update stuff doesn't work right if the convas rect is contained by the media rect, so do a refresh here
        self._DrawCurrentMedia()
        
        self.update()
        
    
    def _Undelete( self ):
        
        locations_manager = self._current_media.GetLocationsManager()
        
        if CC.TRASH_SERVICE_KEY in locations_manager.GetCurrent():
            
            do_it = False
            
            if not HC.options[ 'confirm_trash' ]:
                
                do_it = True
                
            else:
                
                result = ClientGUIDialogsQuick.GetYesNo( self, 'Undelete this file?' )
                
                if result == QW.QDialog.Accepted:
                    
                    do_it = True
                    
                
            
            if do_it:
                
                HG.client_controller.Write( 'content_updates', { CC.TRASH_SERVICE_KEY : [ HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_UNDELETE, ( self._current_media.GetHash(), ) ) ] } )
                
            
        
    
    def _UpdateBackgroundColour( self ):
        
        colour = self._GetBackgroundColour()
        
        QP.SetBackgroundColour( self, colour )
        
        self.update()
        
    
    def _ZoomIn( self ):
        
        if self._current_media is not None and self._IsZoomable():
            
            ( media_scale_up, media_scale_down, preview_scale_up, preview_scale_down, exact_zooms_only, scale_up_quality, scale_down_quality ) = self._new_options.GetMediaZoomOptions( self._current_media.GetMime() )
            
            if exact_zooms_only:
                
                exact_zoom = 1.0
                
                if exact_zoom <= self._current_zoom:
                    
                    while exact_zoom <= self._current_zoom:
                        
                        exact_zoom *= 2
                        
                    
                else:
                    
                    while exact_zoom / 2 > self._current_zoom:
                        
                        exact_zoom /= 2
                        
                    
                
                possible_zooms = [ exact_zoom ]
                
            else:
                
                possible_zooms = self._new_options.GetMediaZooms()
                
            
            possible_zooms.append( self._canvas_zoom )
            
            bigger_zooms = [ zoom for zoom in possible_zooms if zoom > self._current_zoom ]
            
            if len( bigger_zooms ) > 0:
                
                new_zoom = min( bigger_zooms )
                
                self._TryToChangeZoom( new_zoom )
                
            
        
    
    def _ZoomOut( self ):
        
        if self._current_media is not None and self._IsZoomable():
            
            ( media_scale_up, media_scale_down, preview_scale_up, preview_scale_down, exact_zooms_only, scale_up_quality, scale_down_quality ) = self._new_options.GetMediaZoomOptions( self._current_media.GetMime() )
            
            if exact_zooms_only:
                
                exact_zoom = 1.0
                
                if exact_zoom < self._current_zoom:
                    
                    while exact_zoom * 2 < self._current_zoom:
                        
                        exact_zoom *= 2
                        
                    
                else:
                    
                    while exact_zoom >= self._current_zoom:
                        
                        exact_zoom /= 2
                        
                    
                
                possible_zooms = [ exact_zoom ]
                
            else:
                
                possible_zooms = self._new_options.GetMediaZooms()
                
            
            possible_zooms.append( self._canvas_zoom )
            
            smaller_zooms = [ zoom for zoom in possible_zooms if zoom < self._current_zoom ]
            
            if len( smaller_zooms ) > 0:
                
                new_zoom = max( smaller_zooms )
                
                self._TryToChangeZoom( new_zoom )
                
            
        
    
    def _ZoomSwitch( self ):
        
        if self._current_media is not None and self._IsZoomable():
            
            if self._canvas_zoom == 1.0 and self._current_zoom == 1.0:
                
                return
                
            
            ( my_width, my_height ) = self.size().toTuple()
            
            ( media_width, media_height ) = self._current_media.GetResolution()
            
            if self._current_zoom == 1.0:
                
                new_zoom = self._canvas_zoom
                
            else:
                
                new_zoom = 1.0
                
            
            self._TryToChangeZoom( new_zoom )
            
            if new_zoom <= self._canvas_zoom:
                
                self._ResetMediaWindowCenterPosition()
                
            
        
    
    def event( self, event ):
        
        if event.type() == QC.QEvent.LayoutRequest:
            
            return True
            
        else:
            
            return QW.QWidget.event( self, event )
            
        
    
    def CleanBeforeDestroy( self ):
        
        self.SetMedia( None )
        
    
    def BeginDrag( self, point = None ):
        
        if point is None:
            
            point = self.mapFromGlobal( QG.QCursor.pos() )
            
        
        self._last_drag_pos = point
        self._current_drag_is_touch = False
        
    
    def resizeEvent( self, event ):
        
        ( my_width, my_height ) = self.size().toTuple()
        
        if self._current_media is not None:
            
            ( media_width, media_height ) = self._media_container.size().toTuple()
            
            if my_width != media_width or my_height != media_height:
                
                self._ReinitZoom()
                
                self._ResetMediaWindowCenterPosition()
                
            
        
        self.update()
        
    
    def FlipActiveCustomShortcutName( self, name ):
        
        if name in self._custom_shortcut_names:
            
            self._custom_shortcut_names.remove( name )
            
        else:
            
            self._custom_shortcut_names.append( name )
            
            self._custom_shortcut_names.sort()
            
        
    
    def GetActiveCustomShortcutNames( self ):
        
        return self._custom_shortcut_names
        
    
    def KeepCursorAlive( self ):
        
        pass
        
    
    def keyPressEvent( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            shortcut = ClientGUIShortcuts.ConvertKeyEventToShortcut( event )
            
            if shortcut is not None:
                
                shortcut_processed = self._ProcessShortcut( shortcut )
                
                if shortcut_processed:
                    
                    return
                    
                
            
        
        QW.QWidget.keyPressEvent( self, event )
        
    
    def ManageTags( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ManageTags()
            
        
    
    def MouseIsNearAnimationBar( self ):
        
        if self._current_media is None:
            
            return False
            
        else:
            
            return self._media_container.MouseIsNearAnimationBar()
            
        
    
    def MouseIsOverMedia( self ):
        
        if self._current_media is None:
            
            return False
            
        else:
            
            media_mouse_pos = self._media_container.mapFromGlobal( QG.QCursor.pos() )
            
            media_rect = self._media_container.rect()
            
            return media_rect.contains( media_mouse_pos )
            
        
    
    def OpenExternally( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._OpenExternally()
            
        
    
    def paintEvent( self, event ):
        
        painter = QG.QPainter( self )
        
        self._DrawBackgroundBitmap( painter )
        
        if self._current_media is not None:
            
            self._DrawCurrentMedia()
            
        
    
    def ProcessApplicationCommand( self, command, canvas_key = None ):
        
        if canvas_key is not None and canvas_key != self._canvas_key:
            
            return False
            
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'manage_file_ratings':
                
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
                
            elif action == 'copy_bmp':
                
                self._CopyBMPToClipboard()
                
            elif action == 'copy_file':
                
                self._CopyFileToClipboard()
                
            elif action == 'copy_path':
                
                self._CopyPathToClipboard()
                
            elif action == 'copy_sha256_hash':
                
                self._CopyHashToClipboard( 'sha256' )
                
            elif action == 'delete_file':
                
                self._Delete()
                
            elif action == 'inbox_file':
                
                self._Inbox()
                
            elif action == 'open_file_in_external_program':
                
                self._OpenExternally()
                
            elif action == 'pan_up':
                
                self._DoManualPan( 0, -1 )
                
            elif action == 'pan_down':
                
                self._DoManualPan( 0, 1 )
                
            elif action == 'pan_left':
                
                self._DoManualPan( -1, 0 )
                
            elif action == 'pan_right':
                
                self._DoManualPan( 1, 0 )
                
            elif action in ( 'pan_top_edge', 'pan_bottom_edge', 'pan_left_edge', 'pan_right_edge', 'pan_vertical_center', 'pan_horizontal_center' ):
                
                self._DoEdgePan( action )
                
            elif action == 'pause_media':
                
                self._PauseCurrentMedia()
                
            elif action == 'pause_play_media':
                
                self._PausePlayCurrentMedia()
                
            elif action == 'move_animation_to_previous_frame':
                
                self._media_container.GotoPreviousOrNextFrame( -1 )
                
            elif action == 'move_animation_to_next_frame':
                
                self._media_container.GotoPreviousOrNextFrame( 1 )
                
            elif action == 'zoom_in':
                
                self._ZoomIn()
                
            elif action == 'zoom_out':
                
                self._ZoomOut()
                
            elif action == 'switch_between_100_percent_and_canvas_zoom':
                
                self._ZoomSwitch()
                
            else:
                
                command_processed = False
                
            
        elif command_type == CC.APPLICATION_COMMAND_TYPE_CONTENT:
            
            if self._current_media is None:
                
                return
                
            
            command_processed = ClientGUIFunctions.ApplyContentApplicationCommandToMedia( self, command, ( self._current_media, ) )
            
        else:
            
            command_processed = False
            
        
        return command_processed
        
    
    def ResetMediaWindowCenterPosition( self ):
        
        self._ResetMediaWindowCenterPosition()
        
    
    def SetMedia( self, media ):
        
        if media is not None and not self.isVisible():
            
            return
            
        
        if media is not None:
            
            media = media.GetDisplayMedia()
            
            if not self._CanDisplayMedia( media ):
                
                media = None
                
            
        
        if media != self._current_media:
            
            HG.client_controller.ResetIdleTimer()
            
            self._SaveCurrentMediaViewTime()
            
            previous_media = self._current_media
            
            self._current_media = media
            
            if self._current_media is None:
                
                self._media_container.SetNoneMedia()
                
            else:
                
                if previous_media is not None and self._maintain_pan_and_zoom:
                    
                    self._MaintainZoom( previous_media )
                    
                else:
                    
                    self._ReinitZoom()
                    
                
                if not self._maintain_pan_and_zoom:
                    
                    self._ResetMediaWindowCenterPosition()
                    
                
                initial_size = self._GetMediaContainerSize()
                
                ( initial_width, initial_height ) = initial_size
                
                if self._current_media.GetLocationsManager().IsLocal() and initial_width > 0 and initial_height > 0:
                    
                    ( media_show_action, media_start_paused, media_start_with_embed ) = self._GetShowAction( self._current_media )
                    
                    pos = ( self._media_window_pos.x(), self._media_window_pos.y() )
                    
                    self._media_container.SetMedia( self._current_media, initial_size, pos, media_show_action, media_start_paused, media_start_with_embed )
                    
                    self._PrefetchNeighbours()
                    
                else:
                    
                    self._current_media = None
                    
                
            
            HG.client_controller.pub( 'canvas_new_display_media', self._canvas_key, self._current_media )
            
            HG.client_controller.pub( 'canvas_new_index_string', self._canvas_key, self._GetIndexString() )
            
            self.update()
            
        
    
    def minimumSizeHint( self ):
        
        return QC.QSize( 120, 120 )
        
    
    def ZoomIn( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ZoomIn()
            
        
    
    def ZoomOut( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ZoomOut()
            
        
    
    def ZoomSwitch( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ZoomSwitch()
            
        
    
class CanvasPanel( Canvas ):
    
    PREVIEW_WINDOW = True
    
    def __init__( self, parent, page_key ):
        
        Canvas.__init__( self, parent )
        
        self._page_key = page_key
        
        HG.client_controller.sub( self, 'MediaFocusWentToExternalProgram', 'media_focus_went_to_external_program' )
        HG.client_controller.sub( self, 'PreviewChanged', 'preview_changed' )
        HG.client_controller.sub( self, 'ProcessContentUpdates', 'content_updates_gui' )
        
    
    def mouseReleaseEvent( self, event ):
        
        if event.button() != QC.Qt.RightButton:
            
            Canvas.mouseReleaseEvent( self, event )
            
            return
            
        
        menu = QW.QMenu()
        
        if self._current_media is not None:
            
            new_options = HG.client_controller.new_options
            
            advanced_mode = new_options.GetBoolean( 'advanced_mode' )
            
            services = HG.client_controller.services_manager.GetServices()
            
            locations_manager = self._current_media.GetLocationsManager()
            
            local_ratings_services = [ service for service in services if service.GetServiceType() in ( HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ) ]
            
            i_can_post_ratings = len( local_ratings_services ) > 0
            
            #
            
            info_lines = self._current_media.GetPrettyInfoLines()
            
            top_line = info_lines.pop(0)
            
            info_menu = QW.QMenu( menu )
            
            for line in info_lines:
                
                ClientGUIMenus.AppendMenuLabel( info_menu, line, line )
                
            
            ClientGUIMedia.AddFileViewingStatsMenu( info_menu, self._current_media )
            
            ClientGUIMenus.AppendMenu( menu, info_menu, top_line )
            
            ClientGUIMenus.AppendSeparator( menu )
            
        
        AddAudioVolumeMenu( menu, self._canvas_type )
        
        if self._current_media is not None:
            
            #
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if self._current_media.HasInbox():
                
                ClientGUIMenus.AppendMenuItem( menu, 'archive', 'Archive this file.', self._Archive )
                
            
            if self._current_media.HasArchive():
                
                ClientGUIMenus.AppendMenuItem( menu, 'inbox', 'Send this files back to the inbox.', self._Inbox )
                
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if CC.LOCAL_FILE_SERVICE_KEY in locations_manager.GetCurrent():

                ClientGUIMenus.AppendMenuItem( menu, 'delete', 'Delete this file.', self._Delete, file_service_key = CC.LOCAL_FILE_SERVICE_KEY )
                
            elif CC.TRASH_SERVICE_KEY in locations_manager.GetCurrent():
                
                ClientGUIMenus.AppendMenuItem( menu, 'delete completely', 'Physically delete this file from disk.', self._Delete, file_service_key = CC.TRASH_SERVICE_KEY )
                ClientGUIMenus.AppendMenuItem( menu, 'undelete', 'Take this file out of the trash.', self._Undelete )
                
            
            ClientGUIMenus.AppendSeparator( menu )
            
            manage_menu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'tags', 'Manage this file\'s tags.', self._ManageTags )
            
            if i_can_post_ratings:
                
                ClientGUIMenus.AppendMenuItem( manage_menu, 'ratings', 'Manage this file\'s ratings.', self._ManageRatings )
                
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'known urls', 'Manage this file\'s known URLs.', self._ManageURLs )
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'notes', 'Manage this file\'s notes.', self._ManageNotes )
            
            ClientGUIMenus.AppendMenu( menu, manage_menu, 'manage' )
            
            ClientGUIMedia.AddKnownURLsViewCopyMenu( self, menu, self._current_media )
            
            open_menu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( open_menu, 'in external program', 'Open this file in your OS\'s default program.', self._OpenExternally )
            ClientGUIMenus.AppendMenuItem( open_menu, 'in a new page', 'Show your current media in a simple new page.', self._ShowMediaInNewPage )
            ClientGUIMenus.AppendMenuItem( open_menu, 'in web browser', 'Show this file in your OS\'s web browser.', self._OpenFileInWebBrowser )
            
            show_open_in_explorer = advanced_mode and not HC.PLATFORM_LINUX
            
            if show_open_in_explorer:
                
                ClientGUIMenus.AppendMenuItem( open_menu, 'in file browser', 'Show this file in your OS\'s file browser.', self._OpenFileLocation )
                
            
            ClientGUIMenus.AppendMenu( menu, open_menu, 'open' )
            
            share_menu = QW.QMenu( menu )
            
            copy_menu = QW.QMenu( share_menu )

            ClientGUIMenus.AppendMenuItem( copy_menu, 'file', 'Copy this file to your clipboard.', self._CopyFileToClipboard )
            
            copy_hash_menu = QW.QMenu( copy_menu )

            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha256 (hydrus default)', 'Open this file\'s SHA256 hash.', self._CopyHashToClipboard, 'sha256' )
            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'md5', 'Open this file\'s MD5 hash.', self._CopyHashToClipboard, 'md5' )
            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha1', 'Open this file\'s SHA1 hash.', self._CopyHashToClipboard, 'sha1' )
            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha512', 'Open this file\'s SHA512 hash.', self._CopyHashToClipboard, 'sha512' )
            
            ClientGUIMenus.AppendMenu( copy_menu, copy_hash_menu, 'hash' )
            
            if self._current_media.GetMime() in HC.IMAGES:
                
                ClientGUIMenus.AppendMenuItem( copy_menu, 'image (bitmap)', 'Copy this file to your clipboard as a bmp.', self._CopyBMPToClipboard )
                

            ClientGUIMenus.AppendMenuItem( copy_menu, 'path', 'Copy this file\'s path to your clipboard.', self._CopyPathToClipboard )
            
            ClientGUIMenus.AppendMenu( share_menu, copy_menu, 'copy' )
            
            ClientGUIMenus.AppendMenu( menu, share_menu, 'share' )
            
        
        HG.client_controller.PopupMenu( self, menu )
        
    
    def MediaFocusWentToExternalProgram( self, page_key ):
        
        if page_key == self._page_key:
            
            self._MediaFocusWentToExternalProgram()
            
        
    
    def PreviewChanged( self, page_key, media ):
        
        if HC.options[ 'hide_preview' ]:
            
            return
            
        
        if page_key == self._page_key:
            
            self.SetMedia( media )
            
        
    
    def ProcessContentUpdates( self, service_keys_to_content_updates ):
        
        if self._current_media is not None:
            
            my_hash = self._current_media.GetHash()
            
            do_redraw = False
            
            for ( service_key, content_updates ) in list(service_keys_to_content_updates.items()):
                
                if True in ( my_hash in content_update.GetHashes() for content_update in content_updates ):
                    
                    do_redraw = True
                    
                    break
                    
                
            
            if do_redraw:
                
                self.update()
                
            
        
    
class CanvasWithDetails( Canvas ):
    
    def __init__( self, parent ):
        
        Canvas.__init__( self, parent )
        
        HG.client_controller.sub( self, 'RedrawDetails', 'refresh_all_tag_presentation_gui' )
        
    
    def _DrawAdditionalTopMiddleInfo( self, painter, current_y ):
        
        pass
        
    
    def _DrawBackgroundDetails( self, painter ):
        
        if self._current_media is None:
            
            text = self._GetNoMediaText()
            
            ( width, height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, text ).toTuple()
            
            ( my_width, my_height ) = self.size().toTuple()
            
            x = ( my_width - width ) // 2
            y = ( my_height - height ) // 2
            
            QP.DrawText( painter, x, y, text )
            
        else:
            
            ( client_width, client_height ) = self.size().toTuple()
            
            # tags on the top left
            
            painter.setFont( QW.QApplication.font() )
            
            tags_manager = self._current_media.GetTagsManager()
            
            current = tags_manager.GetCurrent( CC.COMBINED_TAG_SERVICE_KEY, ClientTags.TAG_DISPLAY_SINGLE_MEDIA )
            pending = tags_manager.GetPending( CC.COMBINED_TAG_SERVICE_KEY, ClientTags.TAG_DISPLAY_SINGLE_MEDIA )
            petitioned = tags_manager.GetPetitioned( CC.COMBINED_TAG_SERVICE_KEY, ClientTags.TAG_DISPLAY_SINGLE_MEDIA )
            
            tags_i_want_to_display = set()
            
            tags_i_want_to_display.update( current )
            tags_i_want_to_display.update( pending )
            tags_i_want_to_display.update( petitioned )
            
            tags_i_want_to_display = list( tags_i_want_to_display )
            
            ClientTags.SortTags( HC.options[ 'default_tag_sort' ], tags_i_want_to_display )
            
            current_y = 3
            
            namespace_colours = HC.options[ 'namespace_colours' ]
            
            for tag in tags_i_want_to_display:
                
                display_string = ClientTags.RenderTag( tag, True )
                
                if tag in pending:
                    
                    display_string += ' (+)'
                    
                
                if tag in petitioned:
                    
                    display_string += ' (-)'
                    
                
                ( namespace, subtag ) = HydrusTags.SplitTag( tag )
                
                if namespace in namespace_colours:
                    
                    ( r, g, b ) = namespace_colours[ namespace ]
                    
                else:
                    
                    ( r, g, b ) = namespace_colours[ None ]
                    
                
                painter.setPen( QG.QPen( QG.QColor( r, g, b ) ) )
                
                ( x, y ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, display_string ).toTuple()
                
                QP.DrawText( painter, 5, current_y, display_string )
                
                current_y += y
            
            # top right
            
            current_y = 2
            
            # ratings
            
            services_manager = HG.client_controller.services_manager
            
            like_services = services_manager.GetServices( ( HC.LOCAL_RATING_LIKE, ), randomised = False )
            
            like_services.reverse()
            
            like_rating_current_x = client_width - 16 - 2 # -2 to line up exactly with the floating panel
            
            for like_service in like_services:
                
                service_key = like_service.GetServiceKey()
                
                rating_state = ClientRatings.GetLikeStateFromMedia( ( self._current_media, ), service_key )
                
                ClientRatings.DrawLike( painter, like_rating_current_x, current_y, service_key, rating_state )
                
                like_rating_current_x -= 16
                
            
            if len( like_services ) > 0:
                
                current_y += 20
                
            
            numerical_services = services_manager.GetServices( ( HC.LOCAL_RATING_NUMERICAL, ), randomised = False )
            
            for numerical_service in numerical_services:
                
                service_key = numerical_service.GetServiceKey()
                
                ( rating_state, rating ) = ClientRatings.GetNumericalStateFromMedia( ( self._current_media, ), service_key )
                
                numerical_width = ClientRatings.GetNumericalWidth( service_key )
                
                ClientRatings.DrawNumerical( painter, client_width - numerical_width - 2, current_y, service_key, rating_state, rating ) # -2 to line up exactly with the floating panel
                
                current_y += 20
                
            
            # icons
            
            icons_to_show = []
            
            if CC.TRASH_SERVICE_KEY in self._current_media.GetLocationsManager().GetCurrent():
                
                icons_to_show.append( CC.GlobalPixmaps.trash )
                
            
            if self._current_media.HasInbox():
                
                icons_to_show.append( CC.GlobalPixmaps.inbox )
                
            
            if len( icons_to_show ) > 0:
                
                icon_x = 0
                
                for icon in icons_to_show:
                    
                    painter.drawPixmap( client_width+icon_x-18, current_y, icon )
                    
                    icon_x -= 18
                    
                
                current_y += 18
                
            painter.setPen( QG.QPen( self._new_options.GetColour( CC.COLOUR_MEDIA_TEXT ) ) )
            
            # repo strings
            
            remote_strings = self._current_media.GetLocationsManager().GetRemoteLocationStrings()
            
            for remote_string in remote_strings:
                
                ( text_width, text_height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, remote_string ).toTuple()
                
                QP.DrawText( painter, client_width-text_width-3, current_y, remote_string )
                
                current_y += text_height + 4
                
            
            # urls
            
            urls = self._current_media.GetLocationsManager().GetURLs()
            
            url_tuples = HG.client_controller.network_engine.domain_manager.ConvertURLsToMediaViewerTuples( urls )
            
            for ( display_string, url ) in url_tuples:
                
                ( text_width, text_height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, display_string ).toTuple()
                
                QP.DrawText( painter, client_width-text_width-3, current_y, display_string )
                
                current_y += text_height + 4
                
            
            # top-middle
            
            current_y = 3
            
            title_string = self._current_media.GetTitleString()
            
            if len( title_string ) > 0:
                
                ( x, y ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, title_string ).toTuple()
                
                QP.DrawText( painter, (client_width-x)//2, current_y, title_string )
                
                current_y += y + 3
                
            
            info_string = self._GetInfoString()
            
            ( x, y ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, info_string ).toTuple()
            
            QP.DrawText( painter, (client_width-x)//2, current_y, info_string )
            
            current_y += y + 3
            
            self._DrawAdditionalTopMiddleInfo( painter, current_y )
            
            # bottom-right index
            
            index_string = self._GetIndexString()
            
            if len( index_string ) > 0:
                
                ( x, y ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, index_string ).toTuple()
                
                QP.DrawText( painter, client_width-x-3, client_height-y-3, index_string )
                
            
        
    
    def _GetInfoString( self ):
        
        lines = self._current_media.GetPrettyInfoLines()
        
        lines.insert( 1, ClientData.ConvertZoomToPercentage( self._current_zoom ) )
        
        info_string = ' | '.join( lines )
        
        return info_string
        
    
    def _GetNoMediaText( self ):
        
        return 'No media to display'
        
    
    def RedrawDetails( self ):
        
        self.update()
        
    
class CanvasWithHovers( CanvasWithDetails ):
    
    def __init__( self, parent ):
        
        CanvasWithDetails.__init__( self, parent )
        
        self._GenerateHoverTopFrame()
        ClientGUIHoverFrames.FullscreenHoverFrameTags( self, self, self._canvas_key )
        
        ratings_services = HG.client_controller.services_manager.GetServices( ( HC.RATINGS_SERVICES ) )
        
        ClientGUIHoverFrames.FullscreenHoverFrameTopRight( self, self, self._canvas_key )
        
        #
        
        self._timer_cursor_hide_job = None
        
        self._widget_event_filter.EVT_MOTION( self.EventMouseMove )
        
        HG.client_controller.sub( self, 'CloseFromHover', 'canvas_close' )
        HG.client_controller.sub( self, 'FullscreenSwitch', 'canvas_fullscreen_switch' )
        
    
    def _GenerateHoverTopFrame( self ):
        
        raise NotImplementedError()
        
    
    def _TryToCloseWindow( self ):
        
        self.window().close()
        
    
    def CloseFromHover( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._TryToCloseWindow()
            
        
    
    def EventDragBegin( self, event ):
        
        if event.button() != QC.Qt.LeftButton:
            
            return True
            
        
        point = event.pos()
        
        self.BeginDrag( point = point )
        
        return True # was: event.ignore()
        
    
    def EventDragEnd( self, event ):
        
        if event.button() != QC.Qt.LeftButton:
            
            return True
            
        
        self._last_drag_pos = None
        
        return True # was: event.ignore()
        
    
    def EventMouseMove( self, event ):
        
        CC.CAN_HIDE_MOUSE = True
        
        event_pos = event.pos()
        
        show_mouse = self.cursor() == QG.QCursor( QC.Qt.ArrowCursor )
        
        is_dragging = ( event.type() == QC.QEvent.MouseMove and event.buttons() == QC.Qt.LeftButton ) and self._last_drag_pos is not None
        has_moved = event_pos != self._last_motion_pos
        
        if is_dragging:
            
            delta = event_pos - self._last_drag_pos
            
            approx_distance = delta.manhattanLength()
            
            if approx_distance > 0:
                
                touchscreen_canvas_drags_unanchor = HG.client_controller.new_options.GetBoolean( 'touchscreen_canvas_drags_unanchor' )
                
                if not self._current_drag_is_touch and approx_distance > 50:
                    
                    # if user is able to generate such a large distance, they are almost certainly touching
                    
                    self._current_drag_is_touch = True
                    
                
                # touch events obviously don't mix with warping well. the touch just warps it back and again and we get a massive delta!
                
                touch_anchor_override = touchscreen_canvas_drags_unanchor and self._current_drag_is_touch
                anchor_and_hide_canvas_drags = HG.client_controller.new_options.GetBoolean( 'anchor_and_hide_canvas_drags' )
                
                if anchor_and_hide_canvas_drags and not touch_anchor_override:
                    
                    show_mouse = False
                    
                    global_mouse_pos = self.mapToGlobal( self._last_drag_pos )
                    
                    QG.QCursor.setPos( global_mouse_pos )
                    
                else:
                    
                    show_mouse = True
                    
                    self._last_drag_pos = QC.QPoint( event_pos )
                    
                
                self._media_window_pos += delta
                
                self._DrawCurrentMedia()
                
            
        elif has_moved:
            
            self._last_motion_pos = QC.QPoint( event_pos )
            
            show_mouse = True
            
        
        if show_mouse:
            
            self.setCursor( QG.QCursor( QC.Qt.ArrowCursor ) )
            
            self._PutOffCursorHide()
            
        else:
            
            self.setCursor( QG.QCursor( QC.Qt.BlankCursor ) )
            
        
        return True
        
    
    def FullscreenSwitch( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self.parentWidget().FullscreenSwitch()
            
        
    
    def _PutOffCursorHide( self ):
        
        if self._timer_cursor_hide_job is not None:
            
            self._timer_cursor_hide_job.Cancel()
            
        
        self._timer_cursor_hide_job = HG.client_controller.CallLaterQtSafe( self, 0.8, self._HideCursor )
        
    
    def _HideCursor( self ):
        
        if not CC.CAN_HIDE_MOUSE:
            
            return
            
        
        if HG.client_controller.MenuIsOpen():
            
            self._PutOffCursorHide()
            
        else:
            
            self.setCursor( QG.QCursor( QC.Qt.BlankCursor ) )
            
        
    
    def TryToDoPreClose( self ):
        
        can_close = True
        
        return can_close
        
    
class CanvasFilterDuplicates( CanvasWithHovers ):
    
    def __init__( self, parent, file_search_context, both_files_match ):
        
        CanvasWithHovers.__init__( self, parent )
        
        ClientGUIHoverFrames.FullscreenHoverFrameRightDuplicates( self, self, self._canvas_key )
        
        self._file_search_context = file_search_context
        self._both_files_match = both_files_match
        
        self._maintain_pan_and_zoom = True
        
        self._currently_fetching_pairs = False
        
        self._unprocessed_pairs = []
        self._current_pair = None
        self._processed_pairs = []
        self._hashes_due_to_be_deleted_in_this_batch = set()
        
        file_service_key = self._file_search_context.GetFileServiceKey()
        
        self._media_list = ClientMedia.ListeningMediaList( file_service_key, [] )
        
        self._reserved_shortcut_names.append( 'media_viewer_browser' )
        self._reserved_shortcut_names.append( 'duplicate_filter' )
        
        self._widget_event_filter.EVT_MOUSE_EVENTS( self.EventMouse )
        
        # add support for 'f' to borderless
        # add support for F4 and other general shortcuts so people can do edits before processing
        
        HG.client_controller.sub( self, 'ProcessContentUpdates', 'content_updates_gui' )
        HG.client_controller.sub( self, 'Delete', 'canvas_delete' )
        HG.client_controller.sub( self, 'Undelete', 'canvas_undelete' )
        HG.client_controller.sub( self, 'SwitchMedia', 'canvas_show_next' )
        HG.client_controller.sub( self, 'SwitchMedia', 'canvas_show_previous' )
        
        QP.CallAfter( self._ShowNewPair )
        
    
    def TryToDoPreClose( self ):
        
        num_committable = self._GetNumCommittableDecisions()
        
        if num_committable > 0:
            
            label = 'commit ' + HydrusData.ToHumanInt( num_committable ) + ' decisions?'
            
            ( result, cancelled ) = ClientGUIDialogsQuick.GetFinishFilteringAnswer( self, label )
            
            if cancelled:
                
                close_was_triggered_by_everything_being_processed = len( self._unprocessed_pairs ) == 0
                
                if close_was_triggered_by_everything_being_processed:
                    
                    self._GoBack()
                    
                
                return False
                
            elif result == QW.QDialog.Accepted:
                
                self._CommitProcessed( blocking = False )
                
            
        
        ClientMedia.hashes_to_jpeg_quality = {} # clear the cache
        ClientMedia.hashes_to_pixel_hashes = {} # clear the cache
        
        HG.client_controller.pub( 'refresh_dupe_page_numbers' )
        
        return CanvasWithHovers.TryToDoPreClose( self )
        
    
    def _CommitProcessed( self, blocking = True ):
        
        pair_info = []
        
        for ( hash_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) in self._processed_pairs:
            
            if duplicate_type is None or was_auto_skipped:
                
                continue # it was a 'skip' decision
                
            
            first_hash = first_media.GetHash()
            second_hash = second_media.GetHash()
            
            pair_info.append( ( duplicate_type, first_hash, second_hash, service_keys_to_content_updates ) )
            
        
        if len( pair_info ) > 0:
            
            if blocking:
                
                HG.client_controller.WriteSynchronous( 'duplicate_pair_status', pair_info )
                
            else:
                
                HG.client_controller.Write( 'duplicate_pair_status', pair_info )
                
            
        
        self._processed_pairs = []
        self._hashes_due_to_be_deleted_in_this_batch = set()
        
    
    def _CurrentMediaIsBetter( self, delete_second = True ):
        
        self._ProcessPair( HC.DUPLICATE_BETTER, delete_second = delete_second )
        
    
    def _Delete( self, media = None, reason = None, file_service_key = None ):
        
        if self._current_media is None:
            
            return
            
        
        text = 'Delete just this file, or both?'
        
        yes_tuples = []
        
        yes_tuples.append( ( 'delete just this one', 'current' ) )
        yes_tuples.append( ( 'delete both', 'both' ) )
        
        with ClientGUIDialogs.DialogYesYesNo( self, text, yes_tuples = yes_tuples, no_label = 'forget it' ) as dlg:
            
            if dlg.exec() == QW.QDialog.Accepted:
                
                value = dlg.GetValue()
                
                if value == 'current':
                    
                    media = [ self._current_media ]
                    
                    default_reason = 'Deleted manually in Duplicate Filter.'
                    
                elif value == 'both':
                    
                    media = [ self._current_media, self._media_list.GetNext( self._current_media ) ]
                    
                    default_reason = 'Deleted manually in Duplicate Filter, along with its potential duplicate.'
                    
                else:
                    
                    return False
                    
                
            else:
                
                return False
                
            
        
        deleted = CanvasWithHovers._Delete( self, media = media, default_reason = default_reason, file_service_key = file_service_key )
        
        if deleted:
            
            self._SkipPair()
            
        
        return True
        
    
    def _DoCustomAction( self ):
        
        if self._current_media is None:
            
            return
            
        
        duplicate_types = [ HC.DUPLICATE_BETTER, HC.DUPLICATE_SAME_QUALITY, HC.DUPLICATE_ALTERNATE, HC.DUPLICATE_FALSE_POSITIVE ]
        
        choice_tuples = [ ( HC.duplicate_type_string_lookup[ duplicate_type ], duplicate_type ) for duplicate_type in duplicate_types ]
        
        try:
            
            duplicate_type = ClientGUIDialogsQuick.SelectFromList( self, 'select duplicate type', choice_tuples )
            
        except HydrusExceptions.CancelledException:
            
            return
            
        
        new_options = HG.client_controller.new_options
        
        if duplicate_type in [ HC.DUPLICATE_BETTER, HC.DUPLICATE_SAME_QUALITY ] or ( new_options.GetBoolean( 'advanced_mode' ) and duplicate_type == HC.DUPLICATE_ALTERNATE ):
            
            duplicate_action_options = new_options.GetDuplicateActionOptions( duplicate_type )
            
            with ClientGUITopLevelWindows.DialogEdit( self, 'edit duplicate merge options' ) as dlg_2:
                
                panel = ClientGUIScrolledPanelsEdit.EditDuplicateActionOptionsPanel( dlg_2, duplicate_type, duplicate_action_options, for_custom_action = True )
                
                dlg_2.SetPanel( panel )
                
                if dlg_2.exec() == QW.QDialog.Accepted:
                    
                    duplicate_action_options = panel.GetValue()
                    
                else:
                    
                    return
                    
                
            
        else:
            
            duplicate_action_options = None
            
        
        text = 'Delete any of the files?'
        
        yes_tuples = []
        
        yes_tuples.append( ( 'delete neither', 'delete_neither' ) )
        yes_tuples.append( ( 'delete this one', 'delete_first' ) )
        yes_tuples.append( ( 'delete the other', 'delete_second' ) )
        yes_tuples.append( ( 'delete both', 'delete_both' ) )
        
        delete_first = False
        delete_second = False
        delete_both = False
        
        with ClientGUIDialogs.DialogYesYesNo( self, text, yes_tuples = yes_tuples, no_label = 'forget it' ) as dlg:
            
            result = dlg.exec()
            
            if result == QW.QDialog.Accepted:
                
                value = dlg.GetValue()
                
                if value == 'delete_first':
                    
                    delete_first = True
                    
                elif value == 'delete_second':
                    
                    delete_second = True
                    
                elif value == 'delete_both':
                    
                    delete_both = True
                    
                
            else:
                
                return
                
            
        
        self._ProcessPair( duplicate_type, delete_first = delete_first, delete_second = delete_second, delete_both = delete_both, duplicate_action_options = duplicate_action_options )
        
    
    def _DrawBackgroundDetails( self, painter ):
        
        if self._currently_fetching_pairs:
            
            text = 'Loading pairs\u2026'
            
            ( width, height ) = painter.fontMetrics().size( QC.Qt.TextSingleLine, text ).toTuple()
            
            ( my_width, my_height ) = self.size().toTuple()
            
            x = ( my_width - width ) // 2
            y = ( my_height - height ) // 2
            
            QP.DrawText( painter, x, y, text )
            
        else:
            
            CanvasWithHovers._DrawBackgroundDetails( self, painter )
            
        
    
    def _GenerateHoverTopFrame( self ):
        
        ClientGUIHoverFrames.FullscreenHoverFrameTopDuplicatesFilter( self, self, self._canvas_key )
        
    
    def _GetBackgroundColour( self ):
        
        normal_colour = self._new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND )
        
        if self._current_media is None or len( self._media_list ) == 0:
            
            return normal_colour
            
        else:
            
            if self._current_media == self._media_list.GetFirst():
                
                return normal_colour
                
            else:
                
                new_options = HG.client_controller.new_options
                
                duplicate_intensity = new_options.GetNoneableInteger( 'duplicate_background_switch_intensity' )
                
                return ClientData.GetLighterDarkerColour( normal_colour, duplicate_intensity )
                
            
        
    
    def _GetIndexString( self ):
        
        if self._current_media is None or len( self._media_list ) == 0:
            
            return '-'
            
        else:
            
            progress = len( self._processed_pairs ) + 1 # +1 here actually counts for the one currently displayed
            total = progress + len( self._unprocessed_pairs )
            
            index_string = HydrusData.ConvertValueRangeToPrettyString( progress, total )
            
            if self._current_media == self._media_list.GetFirst():
                
                return 'A - ' + index_string
                
            else:
                
                return 'B - ' + index_string
                
            
        
    
    def _GetNoMediaText( self ):
        
        return 'Looking for pairs to compare--please wait.'
        
    
    def _GetNumCommittableDecisions( self ):
        
        return len( [ 1 for ( hash_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) in self._processed_pairs if duplicate_type is not None and not was_auto_skipped ] )
        
    
    def _GoBack( self ):
        
        if len( self._processed_pairs ) > 0 and self._GetNumCommittableDecisions() > 0:
            
            self._unprocessed_pairs.append( self._current_pair )
            
            ( hash_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) = self._processed_pairs.pop()
            
            self._unprocessed_pairs.append( hash_pair )
            
            while was_auto_skipped:
                
                if len( self._processed_pairs ) == 0:
                    
                    QW.QMessageBox.critical( self, 'Error', 'Due to an unexpected series of events (likely a series of file deletes), the duplicate filter has no valid pair to back up to. It will now close.' )
                    
                    self.window().deleteLater()
                    
                    return
                    
                
                ( hash_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) = self._processed_pairs.pop()
                
                self._unprocessed_pairs.append( hash_pair )
                
            
            self._hashes_due_to_be_deleted_in_this_batch.difference_update( hash_pair )
            
            self._ShowNewPair()
            
        
    
    def _MediaAreAlternates( self ):
        
        self._ProcessPair( HC.DUPLICATE_ALTERNATE )
        
    
    def _MediaAreFalsePositive( self ):
        
        self._ProcessPair( HC.DUPLICATE_FALSE_POSITIVE )
        
    
    def _MediaAreTheSame( self ):
        
        self._ProcessPair( HC.DUPLICATE_SAME_QUALITY )
        
    
    def _ProcessPair( self, duplicate_type, delete_first = False, delete_second = False, delete_both = False, duplicate_action_options = None ):
        
        if self._current_media is None:
            
            return
            
        
        if duplicate_action_options is None:
            
            if duplicate_type in [ HC.DUPLICATE_BETTER, HC.DUPLICATE_SAME_QUALITY ] or ( HG.client_controller.new_options.GetBoolean( 'advanced_mode' ) and duplicate_type == HC.DUPLICATE_ALTERNATE ):
                
                new_options = HG.client_controller.new_options
                
                duplicate_action_options = new_options.GetDuplicateActionOptions( duplicate_type )
                
            else:
                
                duplicate_action_options = ClientDuplicates.DuplicateActionOptions()
                
            
        
        first_media = self._current_media
        second_media = self._media_list.GetNext( first_media )
        
        was_auto_skipped = False
        
        if delete_first or delete_second or delete_both:
            
            if delete_first or delete_both:
                
                self._hashes_due_to_be_deleted_in_this_batch.update( first_media.GetHashes() )
                
            
            if delete_second or delete_both:
                
                self._hashes_due_to_be_deleted_in_this_batch.update( second_media.GetHashes() )
                
            
            if duplicate_type in ( HC.DUPLICATE_BETTER, HC.DUPLICATE_WORSE ):
                
                file_deletion_reason = 'better/worse'
                
                if delete_second:
                    
                    file_deletion_reason += ', worse file deleted'
                    
                
            else:
                
                file_deletion_reason = HC.duplicate_type_string_lookup[ duplicate_type ]
                
            
            if delete_both:
                
                file_deletion_reason += ', both files deleted'
                
            
            file_deletion_reason = 'Deleted in Duplicate Filter ({}).'.format( file_deletion_reason )
            
        else:
            
            file_deletion_reason = None
            
        
        service_keys_to_content_updates = duplicate_action_options.ProcessPairIntoContentUpdates( first_media, second_media, delete_first = delete_first, delete_second = delete_second, delete_both = delete_both, file_deletion_reason = file_deletion_reason )
        
        self._processed_pairs.append( ( self._current_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) )
        
        self._ShowNewPair()
        
    
    def _ShowNewPair( self ):
        
        if self._currently_fetching_pairs:
            
            return
            
        
        # hackery dackery doo to quick solve something that is calling this a bunch of times while the 'and continue?' dialog is open, making like 16 of them
        # a full rewrite is needed on this awful workflow
        
        tlws = QW.QApplication.topLevelWidgets()
        
        for tlw in tlws:
            
            if isinstance( tlw, ClientGUITopLevelWindows.DialogCustomButtonQuestion ) and tlw.isModal():
                
                return
                
            
        
        #
        
        num_committable = self._GetNumCommittableDecisions()
        
        if len( self._unprocessed_pairs ) == 0 and num_committable > 0:
            
            label = 'commit ' + HydrusData.ToHumanInt( num_committable ) + ' decisions and continue?'
            
            result = ClientGUIDialogsQuick.GetInterstitialFilteringAnswer( self, label )
            
            if result == QW.QDialog.Accepted:
                
                self._CommitProcessed( blocking = True )
                
            else:
                
                ( hash_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) = self._processed_pairs.pop()
                
                self._unprocessed_pairs.append( hash_pair )
                
                while was_auto_skipped:
                    
                    if len( self._processed_pairs ) == 0:
                        
                        QW.QMessageBox.critical( self, 'Error', 'Due to an unexpected series of events (likely a series of file deletes), the duplicate filter has no valid pair to back up to. It will now close.' )
                        
                        self.window().deleteLater()
                        
                        return
                        
                    
                    ( hash_pair, duplicate_type, first_media, second_media, service_keys_to_content_updates, was_auto_skipped ) = self._processed_pairs.pop()
                    
                    self._unprocessed_pairs.append( hash_pair )
                    
                
                self._hashes_due_to_be_deleted_in_this_batch.difference_update( hash_pair )
                
            
        
        file_service_key = self._file_search_context.GetFileServiceKey()
        
        if len( self._unprocessed_pairs ) == 0:
            
            self._hashes_due_to_be_deleted_in_this_batch = set()
            self._processed_pairs = [] # just in case someone 'skip'ed everything in the last batch, so this never got cleared above
            
            self.SetMedia( None )
            
            self._media_list = ClientMedia.ListeningMediaList( file_service_key, [] )
            
            self._currently_fetching_pairs = True
            
            HG.client_controller.CallToThread( self.THREADFetchPairs, self._file_search_context, self._both_files_match )
            
            self.update()
            
        else:
            
            def pair_is_good( pair ):
                
                ( first_hash, second_hash ) = pair
                
                if first_hash in self._hashes_due_to_be_deleted_in_this_batch or second_hash in self._hashes_due_to_be_deleted_in_this_batch:
                    
                    return False
                    
                
                ( first_media_result, second_media_result ) = HG.client_controller.Read( 'media_results', pair )
                
                first_media = ClientMedia.MediaSingleton( first_media_result )
                second_media = ClientMedia.MediaSingleton( second_media_result )
                
                if not self._CanDisplayMedia( first_media ) or not self._CanDisplayMedia( second_media ):
                    
                    return False
                    
                
                return True
                
            
            potential_pair = self._unprocessed_pairs.pop()
            
            while not pair_is_good( potential_pair ):
                
                was_auto_skipped = True
                
                self._processed_pairs.append( ( potential_pair, None, None, None, {}, was_auto_skipped ) )
                
                if len( self._unprocessed_pairs ) == 0:
                    
                    if len( self._processed_pairs ) == 0:
                        
                        QW.QMessageBox.critical( self, 'Error', 'It seems an entire batch of pairs were unable to be displayed. The duplicate filter will now close.' )
                        
                        self.window().deleteLater()
                        
                        return
                        
                    else:
                        
                        self._ShowNewPair() # there are no useful decisions left in the queue, so let's reset
                        
                        return
                        
                    
                
                potential_pair = self._unprocessed_pairs.pop()
                
            
            self._current_pair = potential_pair
            
            ( first_media_result, second_media_result ) = HG.client_controller.Read( 'media_results', self._current_pair )
            
            if not ( first_media_result.GetLocationsManager().IsLocal() and second_media_result.GetLocationsManager().IsLocal() ):
                
                QW.QMessageBox.warning( self, 'Warning', 'At least one of the potential files in this pair was not in this client. Likely it was very recently deleted through a different process. Your decisions until now will be saved, and then the duplicate filter will close.' )
                
                self._CommitProcessed( blocking = True )
                
                self._TryToCloseWindow()
                
                return
                
            
            first_media = ClientMedia.MediaSingleton( first_media_result )
            second_media = ClientMedia.MediaSingleton( second_media_result )
            
            score = ClientMedia.GetDuplicateComparisonScore( first_media, second_media )
            
            if score > 0:
                
                media_results_with_better_first = ( first_media_result, second_media_result )
                
            else:
                
                media_results_with_better_first = ( second_media_result, first_media_result )
                
            
            self._media_list = ClientMedia.ListeningMediaList( file_service_key, media_results_with_better_first )
            
            self.SetMedia( self._media_list.GetFirst() )

            self._media_container.hide()
            
            self._ReinitZoom()
            
            self._ResetMediaWindowCenterPosition()
            
            self._SizeAndPositionMediaContainer()
            
            self._media_container.show()
            
        
    
    def _SkipPair( self ):
        
        if self._current_media is None:
            
            return
            
        
        was_auto_skipped = False
        
        self._processed_pairs.append( ( self._current_pair, None, None, None, {}, was_auto_skipped ) )
        
        self._ShowNewPair()
        
    
    def _SwitchMedia( self ):
        
        if self._current_media is not None:
            
            try:
                
                other_media = self._media_list.GetNext( self._current_media )
                
                self.SetMedia( other_media )
                
            except HydrusExceptions.DataMissing:
                
                return
                
            
        
    
    def Archive( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._Archive()
            
        
    
    def Delete( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._Delete()
            
        
    
    def EventMouse( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            if event.modifiers() & QC.Qt.ShiftModifier:
                
                caught = True
                
                if event.type() == QC.QEvent.MouseButtonPress and event.button() == QC.Qt.LeftButton:
                    
                    self.EventDragBegin( event )
                    
                elif event.type() == QC.QEvent.MouseButtonRelease and event.button() == QC.Qt.LeftButton:
                    
                    self.EventDragEnd( event )
                    
                elif event.type() == QC.QEvent.MouseMove and event.buttons() != QC.Qt.NoButton:
                    
                    self.EventMouseMove( event )
                    
                else:
                    
                    caught = False
                    
                
                if caught:
                    
                    return
                    
                
            
            shortcut = ClientGUIShortcuts.ConvertMouseEventToShortcut( event )
            
            if shortcut is not None:
                
                shortcut_processed = self._ProcessShortcut( shortcut )
                
                if shortcut_processed:
                    
                    return
                    
                
            if event.type() == QC.QEvent.Wheel and event.angleDelta().y() != 0:
                
                self._SwitchMedia()
                
            else:
                
                return True # was: event.ignore()    
            
        else:
            
            return True # was: event.ignore()
            
        
    
    def Inbox( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._Inbox()
            
        
    
    def keyPressEvent( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
            
            if key in ( QC.Qt.Key_Enter, QC.Qt.Key_Return, QC.Qt.Key_Escape ):
                
                self._TryToCloseWindow()
                
            else:
                
                ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
                
                if modifier == QC.Qt.NoModifier and key in CC.DELETE_KEYS:
                    
                    self._Delete()
                    
                elif modifier == QC.Qt.ShiftModifier and key in CC.DELETE_KEYS:
                    
                    self._Undelete()
                    
                else:
                    
                    CanvasWithHovers.keyPressEvent( self, event )
                    
                
            
        else:
            
            event.ignore()
            
        
    
    def ProcessApplicationCommand( self, command, canvas_key = None ):
        
        if canvas_key is not None and canvas_key != self._canvas_key:
            
            return False
            
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'duplicate_filter_this_is_better_and_delete_other':
                
                self._CurrentMediaIsBetter( delete_second = True )
                
            elif action == 'duplicate_filter_this_is_better_but_keep_both':
                
                self._CurrentMediaIsBetter( delete_second = False )
                
            elif action == 'duplicate_filter_exactly_the_same':
                
                self._MediaAreTheSame()
                
            elif action == 'duplicate_filter_alternates':
                
                self._MediaAreAlternates()
                
            elif action == 'duplicate_filter_false_positive':
                
                self._MediaAreFalsePositive()
                
            elif action == 'duplicate_filter_custom_action':
                
                self._DoCustomAction()
                
            elif action == 'duplicate_filter_skip':
                
                self._SkipPair()
                
            elif action == 'duplicate_filter_back':
                
                self._GoBack()
                
            elif action in ( 'view_first', 'view_last', 'view_previous', 'view_next' ):
                
                self._SwitchMedia()
                
            else:
                
                command_processed = False
                
            
        else:
            
            command_processed = False
            
        
        if not command_processed:
            
            command_processed = CanvasWithHovers.ProcessApplicationCommand( self, command )
            
        
        return command_processed
        
    
    def ProcessContentUpdates( self, service_keys_to_content_updates ):
        
        def catch_up():
            
            # ugly, but it will do for now
            
            if len( self._media_list ) < 2:
                
                self._ShowNewPair()
                
            else:
                
                self.update()
                
            
        
        HG.client_controller.CallLaterQtSafe(self, 0.1, catch_up)
        
    
    def SetMedia( self, media ):
        
        CanvasWithHovers.SetMedia( self, media )
        
        if media is not None:
            
            shown_media = self._current_media
            comparison_media = self._media_list.GetNext( shown_media )
            
            if shown_media != comparison_media:
                
                HG.client_controller.pub( 'canvas_new_duplicate_pair', self._canvas_key, shown_media, comparison_media )
                
            
        
    
    def SwitchMedia( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._SwitchMedia()
            
        
    
    def Undelete( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Undelete()
            
        
    
    def THREADFetchPairs( self, file_search_context, both_files_match ):
        
        def qt_close():
            
            if not self or not QP.isValid( self ):
                
                return
                
            
            QW.QMessageBox.information( self, 'Information', 'All pairs have been filtered!' )
            
            self._TryToCloseWindow()
            
        
        def qt_continue( unprocessed_pairs ):
            
            if not self or not QP.isValid( self):
                
                return
                
            
            self._unprocessed_pairs = unprocessed_pairs
            
            self._currently_fetching_pairs = False
            
            self._ShowNewPair()
            
        
        result = HG.client_controller.Read( 'duplicate_pairs_for_filtering', file_search_context, both_files_match )
        
        if len( result ) == 0:
            
            QP.CallAfter( qt_close )
            
        else:
            
            QP.CallAfter( qt_continue, result )
            
        
    
class CanvasMediaList( ClientMedia.ListeningMediaList, CanvasWithHovers ):
    
    def __init__( self, parent, page_key, media_results ):
        
        CanvasWithHovers.__init__( self, parent )
        ClientMedia.ListeningMediaList.__init__( self, CC.LOCAL_FILE_SERVICE_KEY, media_results )
        
        self._page_key = page_key
        
        self._just_started = True
        
        self._widget_event_filter.EVT_LEFT_DOWN( self.EventDragBegin )
        self._widget_event_filter.EVT_LEFT_UP( self.EventDragEnd )
        
        HG.client_controller.pub( 'set_focus', self._page_key, None )
        
    
    def TryToDoPreClose( self ):
        
        HG.client_controller.pub( 'set_focus', self._page_key, self._current_media )
        
        return CanvasWithHovers.TryToDoPreClose( self )
        
    
    def _GetIndexString( self ):
        
        if self._current_media is None:
            
            index_string = '-/' + HydrusData.ToHumanInt( len( self._sorted_media ) )
            
        else:
            
            index_string = HydrusData.ConvertValueRangeToPrettyString( self._sorted_media.index( self._current_media ) + 1, len( self._sorted_media ) )
            
        
        return index_string
        
    
    def _PrefetchNeighbours( self ):
        
        media_looked_at = set()
        
        to_render = []
        
        previous = self._current_media
        next = self._current_media
        
        delay_base = 0.1
        
        num_to_go_back = 3
        num_to_go_forward = 5
        
        # if media_looked_at nukes the list, we want shorter delays, so do next first
        
        for i in range( num_to_go_forward ):
            
            next = self._GetNext( next )
            
            if next in media_looked_at:
                
                break
                
            else:
                
                media_looked_at.add( next )
                
            
            delay = delay_base * ( i + 1 )
            
            to_render.append( ( next, delay ) )
            
        
        for i in range( num_to_go_back ):
            
            previous = self._GetPrevious( previous )
            
            if previous in media_looked_at:
                
                break
                
            else:
                
                media_looked_at.add( previous )
                
            
            delay = delay_base * 2 * ( i + 1 )
            
            to_render.append( ( previous, delay ) )
            
        
        image_cache = HG.client_controller.GetCache( 'images' )
        
        for ( media, delay ) in to_render:
            
            hash = media.GetHash()
            mime = media.GetMime()
            
            if media.IsStaticImage():
                
                if not image_cache.HasImageRenderer( hash ):
                    
                    HG.client_controller.CallLaterQtSafe(self, delay, image_cache.GetImageRenderer, media)
                    
                
            
        
    
    def _Remove( self ):
        
        next_media = self._GetNext( self._current_media )
        
        if next_media == self._current_media:
            
            next_media = None
            
        
        hashes = { self._current_media.GetHash() }
        
        HG.client_controller.pub( 'remove_media', self._page_key, hashes )
        
        singleton_media = { self._current_media }
        
        ClientMedia.ListeningMediaList._RemoveMediaDirectly( self, singleton_media, {} )
        
        if self.HasNoMedia():
            
            self._TryToCloseWindow()
            
        elif self.HasMedia( self._current_media ):
            
            HG.client_controller.pub( 'canvas_new_index_string', self._canvas_key, self._GetIndexString() )
            
            self.update()
            
        else:
            
            self.SetMedia( next_media )
            
        
    
    def _ShowFirst( self ):
        
        self.SetMedia( self._GetFirst() )
        
    
    def _ShowLast( self ):
        
        self.SetMedia( self._GetLast() )
        
    
    def _ShowNext( self ):
        
        self.SetMedia( self._GetNext( self._current_media ) )
        
    
    def _ShowPrevious( self ):
        
        self.SetMedia( self._GetPrevious( self._current_media ) )
        
    
    def _StartSlideshow( self, interval ):
        
        pass
        
    
    def AddMediaResults( self, page_key, media_results ):
        
        if page_key == self._page_key:
            
            ClientMedia.ListeningMediaList.AddMediaResults( self, media_results )
            
            HG.client_controller.pub( 'canvas_new_index_string', self._canvas_key, self._GetIndexString() )
            
            self.update()
            
        
    
    def EventFullscreenSwitch( self, event ):
        
        self.parentWidget().FullscreenSwitch()
        
    
    def KeepCursorAlive( self ):
        
        self._PutOffCursorHide()
        
    
    def ProcessContentUpdates( self, service_keys_to_content_updates ):
        
        if self._current_media is None:
            
            # probably a file view stats update as we close down--ignore it
            
            return
            
        
        if self.HasMedia( self._current_media ):
            
            next_media = self._GetNext( self._current_media )
            
            if next_media == self._current_media:
                
                next_media = None
                
            
        else:
            
            next_media = None
            
        
        ClientMedia.ListeningMediaList.ProcessContentUpdates( self, service_keys_to_content_updates )
        
        if self.HasNoMedia():
            
            self._TryToCloseWindow()
            
        elif self.HasMedia( self._current_media ):
            
            HG.client_controller.pub( 'canvas_new_index_string', self._canvas_key, self._GetIndexString() )
            
            self.update()
            
        elif self.HasMedia( next_media ):
            
            self.SetMedia( next_media )
            
        else:
            
            self.SetMedia( self._GetFirst() )
            
        
    
class CanvasMediaListFilterArchiveDelete( CanvasMediaList ):
    
    def __init__( self, parent, page_key, media_results ):
        
        CanvasMediaList.__init__( self, parent, page_key, media_results )
        
        self._reserved_shortcut_names.append( 'archive_delete_filter' )
        
        self._kept = set()
        self._deleted = set()
        
        self._widget_event_filter.EVT_MOUSE_EVENTS( self.EventMouse )
        
        HG.client_controller.sub( self, 'Delete', 'canvas_delete' )
        HG.client_controller.sub( self, 'Undelete', 'canvas_undelete' )
        
        QP.CallAfter( self.SetMedia, self._GetFirst() ) # don't set this until we have a size > (20, 20)!
        
    
    def _Back( self ):
        
        if self._IShouldCatchShortcutEvent():
            
            if self._current_media == self._GetFirst():
                
                return
                
            else:
                
                self._ShowPrevious()
                
                self._kept.discard( self._current_media )
                self._deleted.discard( self._current_media )
                
            
        
    
    def TryToDoPreClose( self ):
        
        if len( self._kept ) > 0 or len( self._deleted ) > 0:
            
            label = 'keep ' + HydrusData.ToHumanInt( len( self._kept ) ) + ' and delete ' + HydrusData.ToHumanInt( len( self._deleted ) ) + ' files?'
            
            ( result, cancelled ) = ClientGUIDialogsQuick.GetFinishFilteringAnswer( self, label )
            
            if cancelled:
                
                if self._current_media in self._kept:
                    
                    self._kept.remove( self._current_media )
                    
                
                if self._current_media in self._deleted:
                    
                    self._deleted.remove( self._current_media )
                    
                
                return False
                
            elif result == QW.QDialog.Accepted:
                
                def process_in_thread( service_keys_and_content_updates ):
                    
                    for ( service_key, content_update ) in service_keys_and_content_updates:
                        
                        HG.client_controller.WriteSynchronous( 'content_updates', { service_key : [ content_update ] } )
                        
                    
                
                self._deleted_hashes = [ media.GetHash() for media in self._deleted ]
                self._kept_hashes = [ media.GetHash() for media in self._kept ]
                
                service_keys_and_content_updates = []
                
                reason = 'Deleted in Archive/Delete filter.'
                
                for chunk_of_hashes in HydrusData.SplitListIntoChunks( self._deleted_hashes, 64 ):
                    
                    service_keys_and_content_updates.append( ( CC.LOCAL_FILE_SERVICE_KEY, HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_DELETE, chunk_of_hashes, reason = reason ) ) )
                    
                
                service_keys_and_content_updates.append( ( CC.COMBINED_LOCAL_FILE_SERVICE_KEY, HydrusData.ContentUpdate( HC.CONTENT_TYPE_FILES, HC.CONTENT_UPDATE_ARCHIVE, self._kept_hashes ) ) )
                
                HG.client_controller.CallToThread( process_in_thread, service_keys_and_content_updates )
                
                self._kept = set()
                self._deleted = set()
                
                self._current_media = self._GetFirst() # so the pubsub on close is better
                
                if HC.options[ 'remove_filtered_files' ]:
                    
                    all_hashes = set()
                    
                    all_hashes.update( self._deleted_hashes )
                    all_hashes.update( self._kept_hashes )
                    
                    HG.client_controller.pub( 'remove_media', self._page_key, all_hashes )
                    
                
            
        
        return CanvasMediaList.TryToDoPreClose( self )
        
    
    def _Delete( self, media = None, reason = None, file_service_key = None ):
        
        if self._current_media is None:
            
            return False
            
        
        self._deleted.add( self._current_media )
        
        if self._current_media == self._GetLast():
            
            self._TryToCloseWindow()
            
        else:
            
            self._ShowNext()
            
        
        return True
        
    
    def _GenerateHoverTopFrame( self ):
        
        ClientGUIHoverFrames.FullscreenHoverFrameTopArchiveDeleteFilter( self, self, self._canvas_key )
        
    
    def _Keep( self ):
        
        self._kept.add( self._current_media )
        
        if self._current_media == self._GetLast():
            
            self._TryToCloseWindow()
            
        else:
            
            self._ShowNext()
            
        
    
    def _Skip( self ):
        
        if self._current_media == self._GetLast():
            
            self._TryToCloseWindow()
            
        else:
            
            self._ShowNext()
            
        
    
    def Keep( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Keep()
            
        
    
    def Back( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Back()
            
        
    
    def Delete( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Delete()
            
        
    
    def EventDelete( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            self._Delete()
            
        else:
            
            return True # was: event.ignore()
            
        
    
    def EventMouse( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            if event.modifiers() & QC.Qt.ShiftModifier:
                
                caught = True
                
                if event.type() == QC.QEvent.MouseButtonPress and event.button() == QC.Qt.LeftButton:
                    
                    self.EventDragBegin( event )
                    
                elif event.type() == QC.QEvent.MouseButtonRelease and event.button() == QC.Qt.LeftButton:
                    
                    self.EventDragEnd( event )
                    
                elif event.type() == QC.QEvent.MouseMove and event.buttons() != QC.Qt.NoButton:
                    
                    self.EventMouseMove( event )
                    
                else:
                    
                    caught = False
                    
                
                if caught:
                    
                    return
                    
                
            
            shortcut = ClientGUIShortcuts.ConvertMouseEventToShortcut( event )
            
            if shortcut is not None:
                
                shortcut_processed = self._ProcessShortcut( shortcut )
                
                if shortcut_processed:
                    
                    return
                    
                
            
        
        return True # was: event.ignore()
        
    
    def EventUndelete( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            self._Undelete()
            
        else:
            
            return True # was: event.ignore()
            
        
    
    def keyPressEvent( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
            
            if key in ( QC.Qt.Key_Enter, QC.Qt.Key_Return, QC.Qt.Key_Escape ):
                
                self._TryToCloseWindow()
                
            else:
                
                CanvasMediaList.keyPressEvent( self, event )
                
            
        else:
            
            event.ignore()
            
        
    
    def ProcessApplicationCommand( self, command, canvas_key = None ):
        
        if canvas_key is not None and canvas_key != self._canvas_key:
            
            return False
            
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action in ( 'archive_delete_filter_keep', 'archive_file' ):
                
                self._Keep()
                
            elif action in ( 'archive_delete_filter_delete', 'delete_file' ):
                
                self._Delete()
                
            elif action == 'archive_delete_filter_skip':
                
                self._Skip()
                
            elif action == 'archive_delete_filter_back':
                
                self._Back()
                
            elif action == 'launch_the_archive_delete_filter':
                
                self._TryToCloseWindow()
                
            else:
                
                command_processed = False
                
            
        else:
            
            command_processed = False
            
        
        if not command_processed:
            
            command_processed = CanvasMediaList.ProcessApplicationCommand( self, command )
            
        
        return command_processed
        
    
    def Skip( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Skip()
            
        
    
    def Undelete( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Undelete()
            
        
    
class CanvasMediaListNavigable( CanvasMediaList ):
    
    def __init__( self, parent, page_key, media_results ):
        
        CanvasMediaList.__init__( self, parent, page_key, media_results )
        
        self._reserved_shortcut_names.append( 'media_viewer_browser' )
        
        HG.client_controller.sub( self, 'Delete', 'canvas_delete' )
        HG.client_controller.sub( self, 'ShowNext', 'canvas_show_next' )
        HG.client_controller.sub( self, 'ShowPrevious', 'canvas_show_previous' )
        HG.client_controller.sub( self, 'Undelete', 'canvas_undelete' )
        
    
    def _GenerateHoverTopFrame( self ):
        
        ClientGUIHoverFrames.FullscreenHoverFrameTopNavigableList( self, self, self._canvas_key )
        
    
    def Archive( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._Archive()
            
        
    
    def Delete( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._Delete()
            
        
    
    def Inbox( self, canvas_key ):
        
        if self._canvas_key == canvas_key:
            
            self._Inbox()
            
        
    
    def ProcessApplicationCommand( self, command, canvas_key = None ):
        
        if canvas_key is not None and canvas_key != self._canvas_key:
            
            return False
            
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'remove_file_from_view':
                
                self._Remove()
                
            elif action == 'view_first':
                
                self._ShowFirst()
                
            elif action == 'view_last':
                
                self._ShowLast()
                
            elif action == 'view_previous':
                
                self._ShowPrevious()
                
            elif action == 'view_next':
                
                self._ShowNext()
                
            else:
                
                command_processed = False
                
            
        else:
            
            command_processed = False
            
        
        if not command_processed:
            
            command_processed = CanvasMediaList.ProcessApplicationCommand( self, command )
            
        
        return command_processed
        
    
    def ShowFirst( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ShowFirst()
            
        
    
    def ShowLast( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ShowLast()
            
        
    
    def ShowNext( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ShowNext()
            
        
    
    def ShowPrevious( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._ShowPrevious()
            
        
    
    def Undelete( self, canvas_key ):
        
        if canvas_key == self._canvas_key:
            
            self._Undelete()
            
        
    
class CanvasMediaListBrowser( CanvasMediaListNavigable ):
    
    def __init__( self, parent, page_key, media_results, first_hash ):
        
        CanvasMediaListNavigable.__init__( self, parent, page_key, media_results )
        
        self._timer_slideshow_job = None
        self._timer_slideshow_interval = 0
        
        self._widget_event_filter.EVT_LEFT_DCLICK( self.EventMouseClose )
        self._widget_event_filter.EVT_MIDDLE_DOWN( self.EventMouseClose )
        
        if first_hash is None:
            
            first_media = self._GetFirst()
            
        else:
            
            try:
                
                first_media = self._GetMedia( { first_hash } )[0]
                
            except:
                
                first_media = self._GetFirst()
                
            
        
        QP.CallAfter( self.SetMedia, first_media ) # don't set this until we have a size > (20, 20)!
        
        HG.client_controller.sub( self, 'AddMediaResults', 'add_media_results' )
        
    
    def EventMouseClose( self, event ):
        
        self._TryToCloseWindow()
        
    
    def _PausePlaySlideshow( self ):
        
        if self._timer_slideshow_job is not None:
            
            self._StopSlideshow()
            
        elif self._timer_slideshow_interval > 0:
            
            self._StartSlideshow( self._timer_slideshow_interval )
            
        
    
    def _StartSlideshow( self, interval = None ):
        
        self._StopSlideshow()
        
        if interval is None:
            
            with ClientGUIDialogs.DialogTextEntry( self, 'Enter the interval, in seconds.', default = '15' ) as dlg:
                
                if dlg.exec() == QW.QDialog.Accepted:
                    
                    try:
                        
                        interval = float( dlg.GetValue() )
                        
                    except:
                        
                        return
                        
                    
                
            
        
        if interval > 0:
            
            self._timer_slideshow_interval = interval
            
            self._timer_slideshow_job = HG.client_controller.CallLaterQtSafe(self, self._timer_slideshow_interval, self.DoSlideshow)
            
        
    
    def _StopSlideshow( self ):
        
        if self._timer_slideshow_job is not None:
            
            self._timer_slideshow_job.Cancel()
            
            self._timer_slideshow_job = None
            
        
    
    def DoSlideshow( self ):
        
        try:
            
            if self._current_media is not None and self._timer_slideshow_job is not None:
                
                if self._media_container.ReadyToSlideshow() and not HG.client_controller.MenuIsOpen():
                    
                    self._ShowNext()
                    
                    self._timer_slideshow_job = HG.client_controller.CallLaterQtSafe(self, self._timer_slideshow_interval, self.DoSlideshow)
                    
                else:
                    
                    self._timer_slideshow_job = HG.client_controller.CallLaterQtSafe(self, 0.5, self.DoSlideshow)
                    
                
            
        except:
            
            self._timer_slideshow_job = None
            
            raise
            
        
    
    def mouseReleaseEvent( self, event ):
        
        if event.button() != QC.Qt.RightButton:
            
            CanvasMediaListNavigable.mouseReleaseEvent( self, event )
            
            return
            
        
        if self._current_media is not None:
            
            new_options = HG.client_controller.new_options
            
            advanced_mode = new_options.GetBoolean( 'advanced_mode' )
        
            services = HG.client_controller.services_manager.GetServices()
            
            local_ratings_services = [ service for service in services if service.GetServiceType() in ( HC.LOCAL_RATING_LIKE, HC.LOCAL_RATING_NUMERICAL ) ]
            
            i_can_post_ratings = len( local_ratings_services ) > 0
            
            self._last_drag_pos = None # to stop successive right-click drag warp bug
            
            locations_manager = self._current_media.GetLocationsManager()
            
            menu = QW.QMenu()
            
            #
            
            info_lines = self._current_media.GetPrettyInfoLines()
            
            top_line = info_lines.pop(0)
            
            info_menu = QW.QMenu( menu )
            
            for line in info_lines:
                
                ClientGUIMenus.AppendMenuLabel( info_menu, line, line )
                
            
            ClientGUIMedia.AddFileViewingStatsMenu( info_menu, self._current_media )
            
            ClientGUIMenus.AppendMenu( menu, info_menu, top_line )
            
            #
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if self._IsZoomable():
                
                zoom_menu = QW.QMenu( menu )
                
                ClientGUIMenus.AppendMenuItem( zoom_menu, 'zoom in', 'Zoom the media in.', self._ZoomIn )
                ClientGUIMenus.AppendMenuItem( zoom_menu, 'zoom out', 'Zoom the media out.', self._ZoomOut )
                
                if self._current_zoom != 1.0:
                    
                    ClientGUIMenus.AppendMenuItem( zoom_menu, 'zoom to 100%', 'Set the zoom to 100%.', self._ZoomSwitch )
                    
                elif self._current_zoom != self._canvas_zoom:
                    
                    ClientGUIMenus.AppendMenuItem( zoom_menu, 'zoom fit', 'Set the zoom so the media fits the canvas.', self._ZoomSwitch )
                    
                
                ClientGUIMenus.AppendMenu( menu, zoom_menu, 'current zoom: {}'.format( ClientData.ConvertZoomToPercentage( self._current_zoom ) ) )
                
            
            AddAudioVolumeMenu( menu, self._canvas_type )
            
            if self.parentWidget().isFullScreen():
                
                ClientGUIMenus.AppendMenuItem( menu, 'exit fullscreen', 'Make this media viewer a regular window with borders.', self.parentWidget().FullscreenSwitch )
                
            else:
                
                ClientGUIMenus.AppendMenuItem( menu, 'go fullscreen', 'Make this media viewer a fullscreen window without borders.', self.parentWidget().FullscreenSwitch )
                
            
            slideshow = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( slideshow, '1 second', 'Start a slideshow with a one second interval.', self._StartSlideshow, 1.0 )
            ClientGUIMenus.AppendMenuItem( slideshow, '5 second', 'Start a slideshow with a five second interval.', self._StartSlideshow, 5.0 )
            ClientGUIMenus.AppendMenuItem( slideshow, '10 second', 'Start a slideshow with a ten second interval.', self._StartSlideshow, 10.0 )
            ClientGUIMenus.AppendMenuItem( slideshow, '30 second', 'Start a slideshow with a thirty second interval.', self._StartSlideshow, 30.0 )
            ClientGUIMenus.AppendMenuItem( slideshow, '60 second', 'Start a slideshow with a one minute interval.', self._StartSlideshow, 60.0 )
            ClientGUIMenus.AppendMenuItem( slideshow, 'very fast', 'Start a very fast slideshow.', self._StartSlideshow, 0.08 )
            ClientGUIMenus.AppendMenuItem( slideshow, 'custom interval', 'Start a slideshow with a custom interval.', self._StartSlideshow )
            
            ClientGUIMenus.AppendMenu( menu, slideshow, 'start slideshow' )
            
            if self._timer_slideshow_job is not None:
                
                ClientGUIMenus.AppendMenuItem( menu, 'stop slideshow', 'Stop the current slideshow.', self._PausePlaySlideshow )
                
            
            ClientGUIMenus.AppendSeparator( menu )
            
            ClientGUIMenus.AppendMenuItem( menu, 'remove from view', 'Remove this file from the list you are viewing.', self._Remove )
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if self._current_media.HasInbox():

                ClientGUIMenus.AppendMenuItem( menu, 'archive', 'Archive this file, taking it out of the inbox.', self._Archive )
                
            elif self._current_media.HasArchive():
                
                ClientGUIMenus.AppendMenuItem( menu, 'return to inbox', 'Put this file back in the inbox.', self._Inbox )
                
            
            ClientGUIMenus.AppendSeparator( menu )
            
            if CC.LOCAL_FILE_SERVICE_KEY in locations_manager.GetCurrent():

                ClientGUIMenus.AppendMenuItem( menu, 'delete', 'Send this file to the trash.', self._Delete, file_service_key=CC.LOCAL_FILE_SERVICE_KEY )
                
            elif CC.TRASH_SERVICE_KEY in locations_manager.GetCurrent():
                
                ClientGUIMenus.AppendMenuItem( menu, 'delete from trash now', 'Delete this file immediately. This cannot be undone.', self._Delete, file_service_key=CC.TRASH_SERVICE_KEY )
                ClientGUIMenus.AppendMenuItem( menu, 'undelete', 'Take this file out of the trash, returning it to its original file service.', self._Undelete )
                
            
            ClientGUIMenus.AppendSeparator( menu )
            
            manage_menu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'tags', 'Manage this file\'s tags.', self._ManageTags )
            
            if i_can_post_ratings:
                
                ClientGUIMenus.AppendMenuItem( manage_menu, 'ratings', 'Manage this file\'s ratings.', self._ManageRatings )
                
            
            ClientGUIMenus.AppendMenuItem( manage_menu, 'known urls', 'Manage this file\'s known urls.', self._ManageURLs )
            ClientGUIMenus.AppendMenuItem( manage_menu, 'notes', 'Manage this file\'s notes.', self._ManageNotes )
            
            ClientGUIMenus.AppendMenu( menu, manage_menu, 'manage' )
            
            ClientGUIMedia.AddKnownURLsViewCopyMenu( self, menu, self._current_media )
            
            open_menu = QW.QMenu( menu )
            
            ClientGUIMenus.AppendMenuItem( open_menu, 'in external program', 'Open this file in the default external program.', self._OpenExternally )
            ClientGUIMenus.AppendMenuItem( open_menu, 'in a new page', 'Show your current media in a simple new page.', self._ShowMediaInNewPage )
            ClientGUIMenus.AppendMenuItem( open_menu, 'in web browser', 'Show this file in your OS\'s web browser.', self._OpenFileInWebBrowser )
            
            show_open_in_explorer = advanced_mode and not HC.PLATFORM_LINUX
            
            if show_open_in_explorer:
                
                ClientGUIMenus.AppendMenuItem( open_menu, 'in file browser', 'Show this file in your OS\'s file browser.', self._OpenFileLocation )
                
            
            ClientGUIMenus.AppendMenu( menu, open_menu, 'open' )
            
            share_menu = QW.QMenu( menu )
            
            copy_menu = QW.QMenu( share_menu )

            ClientGUIMenus.AppendMenuItem( copy_menu, 'file', 'Copy this file to your clipboard.', self._CopyFileToClipboard )
            
            copy_hash_menu = QW.QMenu( copy_menu )

            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha256 (hydrus default)', 'Copy this file\'s SHA256 hash to your clipboard.', self._CopyHashToClipboard, 'sha256' )
            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'md5', 'Copy this file\'s MD5 hash to your clipboard.', self._CopyHashToClipboard, 'md5' )
            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha1', 'Copy this file\'s SHA1 hash to your clipboard.', self._CopyHashToClipboard, 'sha1' )
            ClientGUIMenus.AppendMenuItem( copy_hash_menu, 'sha512', 'Copy this file\'s SHA512 hash to your clipboard.', self._CopyHashToClipboard, 'sha512' )
            
            ClientGUIMenus.AppendMenu( copy_menu, copy_hash_menu, 'hash' )
            
            if self._current_media.GetMime() in HC.IMAGES:
                
                ClientGUIMenus.AppendMenuItem( copy_menu, 'image (bitmap)', 'Copy this file to your clipboard as a BMP image.', self._CopyBMPToClipboard )
                

            ClientGUIMenus.AppendMenuItem( copy_menu, 'path', 'Copy this file\'s path to your clipboard.', self._CopyPathToClipboard )
            
            ClientGUIMenus.AppendMenu( share_menu, copy_menu, 'copy' )
            
            ClientGUIMenus.AppendMenu( menu, share_menu, 'share' )
            
            HG.client_controller.PopupMenu( self, menu )
            
        
    
    def keyPressEvent( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            ( modifier, key ) = ClientGUIShortcuts.ConvertKeyEventToSimpleTuple( event )
            
            if modifier == QC.Qt.NoModifier and key in CC.DELETE_KEYS: self._Delete()
            elif modifier == QC.Qt.ShiftModifier and key in CC.DELETE_KEYS: self._Undelete()
            elif key in ( QC.Qt.Key_Enter, QC.Qt.Key_Return, QC.Qt.Key_Escape ):
                
                self._TryToCloseWindow()
                
            else:
                
                CanvasMediaListNavigable.keyPressEvent( self, event )
                
            
        else:
            
            event.ignore()
            
        
    
    def ProcessApplicationCommand( self, command, canvas_key = None ):
        
        if canvas_key is not None and canvas_key != self._canvas_key:
            
            return False
            
        
        command_processed = True
        
        command_type = command.GetCommandType()
        data = command.GetData()
        
        if command_type == CC.APPLICATION_COMMAND_TYPE_SIMPLE:
            
            action = data
            
            if action == 'pause_play_slideshow':
                
                self._PausePlaySlideshow()
                
            else:
                
                command_processed = False
                
            
        else:
            
            command_processed = False
            
        
        if not command_processed:
            
            command_processed = CanvasMediaListNavigable.ProcessApplicationCommand( self, command )
            
        
        return command_processed
        
    
    def wheelEvent( self, event ):
        
        if self._IShouldCatchShortcutEvent( event = event ):
            
            if event.modifiers() & QC.Qt.ControlModifier:
                
                if event.angleDelta().y() > 0:
                    
                    self._ZoomIn()
                    
                else:
                    
                    self._ZoomOut()
                    
                
            else:
                
                if event.angleDelta().y() > 0:
                    
                    self._ShowPrevious()
                    
                else:
                    
                    self._ShowNext()
                    
                
            
        else:
            
            return True # was: event.ignore()
            
        
    
class MediaContainer( QW.QWidget ):
    
    def __init__( self, parent, canvas_type ):
        
        QW.QWidget.__init__( self, parent )
        
        self._canvas_type = canvas_type
        
        # If I do not set this, macOS goes 100% CPU endless repaint events!
        # My guess is it due to the borked layout
        # it means 'I guarantee to cover my whole viewport with pixels, no need for automatic background clear'
        self.setAttribute( QC.Qt.WA_OpaquePaintEvent, True )
        
        self.setSizePolicy( QW.QSizePolicy.Fixed, QW.QSizePolicy.Fixed )
        
        self._media = None
        self._show_action = CC.MEDIA_VIEWER_ACTION_SHOW_WITH_NATIVE
        self._start_paused = False
        self._start_with_embed = False
        
        self._media_window = None
        
        self._embed_button = EmbedButton( self )
        self._embed_button_widget_event_filter = QP.WidgetEventFilter( self._embed_button )
        self._embed_button_widget_event_filter.EVT_LEFT_DOWN( self.EventEmbedButton )
        
        self.setMouseTracking( True )
        
        self._animation_window = Animation( self )
        self._animation_bar = AnimationBar( self )
        self._volume_control = ClientGUIMediaControls.VolumeControl( self, self._canvas_type, direction = 'up' )
        self._mpv_window = None
        self._static_image_window = StaticImage( self )
        
        self._volume_control.adjustSize()
        self._volume_control.setCursor( QG.Qt.ArrowCursor )
        
        self._animation_window.hide()
        self._animation_bar.hide()
        self._volume_control.hide()
        self._static_image_window.hide()
        self._embed_button.hide()
        
        self.hide()
        
    
    def _DestroyOrHideThisMediaWindow( self, media_window ):
        
        if media_window is not None:
            
            if isinstance( media_window, ( Animation, StaticImage ) ):
                
                media_window.SetNoneMedia()
                
                media_window.hide()
                
            elif isinstance( media_window, ClientGUIMPV.mpvWidget ):
                
                self._mpv_window = None
                
                media_window.SetNoneMedia()
                
                media_window.hide()
                
                HG.client_controller.gui.ReleaseMPVWidget( media_window )
                
            else:
                
                media_window.deleteLater()
                
            
        
    
    def _HideAnimationBar( self ):
        
        self._animation_bar.SetNoneMedia()
        
        self._animation_bar.hide()
        
    
    def _MakeMediaWindow( self ):
        
        old_media_window = self._media_window
        destroy_old_media_window = True
        
        if self._show_action == CC.MEDIA_VIEWER_ACTION_SHOW_WITH_MPV and not ClientGUIMPV.MPV_IS_AVAILABLE:
            
            self._show_action = CC.MEDIA_VIEWER_ACTION_SHOW_OPEN_EXTERNALLY_BUTTON
            
            HydrusData.ShowText( 'MPV is not available!' )
            
        
        if self._show_action in ( CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW_ON_ACTIVATION_OPEN_EXTERNALLY, CC.MEDIA_VIEWER_ACTION_DO_NOT_SHOW ):
            
            raise Exception( 'This media should not be shown in the media viewer!' )
            
        elif self._show_action == CC.MEDIA_VIEWER_ACTION_SHOW_OPEN_EXTERNALLY_BUTTON:
            
            self._media_window = OpenExternallyPanel( self, self._media )
            
        elif self._show_action == CC.MEDIA_VIEWER_ACTION_SHOW_WITH_NATIVE:
            
            if self._media.IsStaticImage():
                
                if isinstance( self._media_window, StaticImage ):
                    
                    destroy_old_media_window = False
                    
                else:
                    
                    self._media_window = self._static_image_window
                    
                
                self._media_window.SetMedia( self._media )
                
            else:
                
                if isinstance( self._media_window, Animation ):
                    
                    destroy_old_media_window = False
                    
                else:
                    
                    self._media_window = self._animation_window
                    
                
                self._media_window.SetMedia( self._media, start_paused = self._start_paused )
                
            
        elif self._show_action == CC.MEDIA_VIEWER_ACTION_SHOW_WITH_MPV:
            
            if isinstance( self._media_window, ClientGUIMPV.mpvWidget ):
                
                destroy_old_media_window = False
                
            else:
                
                if self._mpv_window is None:
                    
                    self._mpv_window = HG.client_controller.gui.GetMPVWidget( self )
                    
                
                self._mpv_window.SetCanvasType( self._canvas_type )
                
                self._media_window = self._mpv_window
                
            
            self._media_window.SetMedia( self._media, start_paused = self._start_paused )
            
        
        if ShouldHaveAnimationBar( self._media, self._show_action ):
            
            self._animation_bar.SetMediaAndWindow( self._media, self._media_window )
            
            if self._mpv_window is not None and self._media.HasAudio():
                
                self._volume_control.show()
                
            else:
                
                self._volume_control.hide()
                
            
            self._animation_bar.show()
            
        else:
            
            self._HideAnimationBar()
            
            self._volume_control.hide()
            
        
        if old_media_window is not None and destroy_old_media_window:
            
            self._DestroyOrHideThisMediaWindow( old_media_window )
            
            # this forces a flush of the last valid background bmp, so we don't get a flicker of a file from five files ago when we last saw a static image
            self.repaint()
            
        
        self._media_window.show()
        
    
    def _SizeAndPositionChildren( self ):
        
        if self._media is not None:
            
            ( my_width, my_height ) = self.size().toTuple()
            
            if self._media_window is None:
                
                self._embed_button.setFixedSize( QP.TupleToQSize( ( my_width, my_height ) ) )
                self._embed_button.move( QP.TupleToQPoint( ( 0, 0 ) ) )
                
            else:
                
                is_open_externally = isinstance( self._media_window, OpenExternallyPanel )
                
                ( media_width, media_height ) = ( my_width, my_height )
                
                if ShouldHaveAnimationBar( self._media, self._show_action ) and not is_open_externally:
                    
                    animated_scanbar_height = HG.client_controller.new_options.GetInteger( 'animated_scanbar_height' )
                    
                    media_height -= animated_scanbar_height
                    
                    if self._volume_control.isVisibleTo( self ):
                        
                        volume_width = self._volume_control.width()
                        
                    else:
                        
                        volume_width = 0
                        
                    
                    self._animation_bar.setFixedSize( QP.TupleToQSize( ( my_width - volume_width, animated_scanbar_height ) ) )
                    self._animation_bar.move( QP.TupleToQPoint( ( 0, my_height - animated_scanbar_height ) ) )
                    
                    if self._volume_control.isVisibleTo( self ):
                        
                        self._volume_control.setFixedSize( QP.TupleToQSize( ( volume_width, animated_scanbar_height ) ) )
                        self._volume_control.move( QP.TupleToQPoint( ( self._animation_bar.width(), my_height - animated_scanbar_height ) ) )
                        
                    
                
                self._media_window.setFixedSize( QP.TupleToQSize( ( media_width, media_height ) ) )
                self._media_window.move( QP.TupleToQPoint( ( 0, 0 ) ) )
                
            
        
    
    def BeginDrag( self ):
        
        self.parentWidget().BeginDrag()
        
    
    def EventEmbedButton( self, event ):
        
        self._embed_button.hide()
        
        self._MakeMediaWindow()
        
        self._SizeAndPositionChildren()
        
    
    def resizeEvent( self, event ):
        
        if self._media is not None:
            
            self._SizeAndPositionChildren()
            
        
    
    def GotoPreviousOrNextFrame( self, direction ):
        
        if self._media is not None:
            
            if ShouldHaveAnimationBar( self._media, self._show_action ):
                
                if isinstance( self._media_window, Animation ):
                    
                    current_frame_index = self._media_window.CurrentFrame()
                    
                    num_frames = self._media.GetNumFrames()
                    
                    if direction == 1:
                        
                        if current_frame_index == num_frames - 1:
                            
                            current_frame_index = 0
                            
                        else:
                            
                            current_frame_index += 1
                            
                        
                    else:
                        
                        if current_frame_index == 0:
                            
                            current_frame_index = num_frames - 1
                            
                        else:
                            
                            current_frame_index -= 1
                            
                        
                    
                    self._media_window.GotoFrame( current_frame_index )
                    
                elif isinstance( self._media_window, ClientGUIMPV.mpvWidget ):
                    
                    self._media_window.GotoPreviousOrNextFrame( direction )
                    
                
            
        
    
    def MouseIsNearAnimationBar( self ):
        
        if self._media is None:
            
            return False
            
        else:
            
            if ShouldHaveAnimationBar( self._media, self._show_action ):
                
                animation_bar_mouse_pos = self._animation_bar.mapFromGlobal( QG.QCursor.pos() )
                
                animation_bar_rect = self._animation_bar.rect()
                
                buffer = 100
                
                test_rect = animation_bar_rect.adjusted( -buffer, -buffer, buffer, buffer )
                
                return test_rect.contains( animation_bar_mouse_pos )
                
            
            return False
            
        
    
    def paintEvent( self, event ):
        
        painter = None
        
        # hackery dackery doo to deal with non-redrawing single-pixel border around the real widget
        # we'll fix this when we fix the larger layout/repaint issue
        if self._volume_control.isVisible():
            
            painter = QG.QPainter( self )
            
            background_colour = HG.client_controller.new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND )
            
            painter.setBrush( QG.QBrush( background_colour ) )
            painter.setPen( QC.Qt.NoPen )
            
            painter.drawRect( self._volume_control.geometry() )
            
        
        if self._media_window is not None and self._media_window.isVisible():
            
            return
            
        
        # this only happens when we are transitioning from one media to another. in the brief period when one media type is going to another, we'll get flicker of the last valid bmp
        # mpv embed fun aggravates this
        # so instead we do an explicit repaint after the hide and before the new show, to clear our window
        
        if painter is None:
            
            painter = QG.QPainter( self )
            
        
        background_colour = HG.client_controller.new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND )
        
        painter.setBrush( QG.QBrush( background_colour ) )
        
        painter.drawRect( painter.viewport() )
        
    
    def Pause( self ):
        
        if self._media is not None:
            
            if isinstance( self._media_window, ( Animation, ClientGUIMPV.mpvWidget ) ):
                
                self._media_window.Pause()
                
            
        
    
    def PausePlay( self ):
        
        if self._media is not None:
            
            if isinstance( self._media_window, ( Animation, ClientGUIMPV.mpvWidget ) ):
                
                self._media_window.PausePlay()
                
            
        
    
    def ReadyToSlideshow( self ):
        
        if self._media is None:
            
            return False
            
        else:
            
            if isinstance( self._media_window, ( Animation, ClientGUIMPV.mpvWidget ) ):
                
                if self._media_window.IsPlaying() and not self._media_window.HasPlayedOnceThrough():
                    
                    return False
                    
                
            
            if isinstance( self._media_window, StaticImage ):
                
                if not self._media_window.IsRendered():
                    
                    return False
                    
                
            
            return True
            
        
    
    def SetEmbedButton( self ):
        
        self._HideAnimationBar()
        
        self._volume_control.hide()
        
        self._DestroyOrHideThisMediaWindow( self._media_window )
        
        self._media_window = None
        
        self._embed_button.SetMedia( self._media )
        
        self._embed_button.show()
        
    
    def SetMedia( self, media, initial_size, initial_position, show_action, start_paused, start_with_embed ):
        
        self._media = media
        
        self._show_action = show_action
        self._start_paused = start_paused
        self._start_with_embed = start_with_embed
        
        if self._start_with_embed:
            
            self.SetEmbedButton()
            
        else:
            
            self._embed_button.hide()
            
            self._MakeMediaWindow()
            
        
        self.setFixedSize( QP.TupleToQSize( initial_size ) )
        self.move( QP.TupleToQPoint( initial_position ) )
        
        self._SizeAndPositionChildren()
        
        self.show()
        
    
    def SetNoneMedia( self ):
        
        self._media = None
        
        self._HideAnimationBar()
        
        self._volume_control.hide()
        
        self._DestroyOrHideThisMediaWindow( self._media_window )
        
        self._media_window = None
        
        self.hide()
        
    
class EmbedButton( QW.QWidget ):
    
    def __init__( self, parent ):
        
        QW.QWidget.__init__( self, parent )
        
        self._media = None
        
        self._thumbnail_qt_pixmap = None
        
        self.setCursor( QG.QCursor( QC.Qt.PointingHandCursor ) )
        
        HG.client_controller.sub( self, 'update', 'notify_new_colourset' )
        
    
    def _Redraw( self, painter ):
        
        ( x, y ) = self.size().toTuple()
        
        center_x = x // 2
        center_y = y // 2
        radius = min( 50, center_x, center_y ) - 5
        
        new_options = HG.client_controller.new_options
        
        painter.setBackground( QG.QBrush( new_options.GetColour(CC.COLOUR_MEDIA_BACKGROUND) ) )
        
        painter.eraseRect( painter.viewport() )
        
        if self._thumbnail_qt_pixmap is not None:
            
            ( thumb_width, thumb_height ) = self._thumbnail_qt_pixmap.size().toTuple()
            
            scale = x / thumb_width
            
            painter.setTransform( QG.QTransform().scale( scale, scale ) )
            
            painter.drawPixmap( 0, 0, self._thumbnail_qt_pixmap )
            
            painter.setTransform( QG.QTransform().scale( 1.0, 1.0 ) )
            
        
        painter.setBrush( QG.QBrush( QP.GetSystemColour( QG.QPalette.Button ) ) )
        
        painter.drawEllipse( QC.QPointF( center_x, center_y ), radius, radius )
        
        painter.setBrush( QG.QBrush( QP.GetSystemColour( QG.QPalette.Window ) ) )
        
        # play symbol is a an equilateral triangle
        
        triangle_side = radius * 0.8
        
        half_triangle_side = int( triangle_side // 2 )
        
        cos30 = 0.866
        
        triangle_width = triangle_side * cos30
        
        third_triangle_width = int( triangle_width // 3 )
        
        points = []
        
        points.append( QC.QPoint( center_x - third_triangle_width, center_y - half_triangle_side ) )
        points.append( QC.QPoint( center_x + third_triangle_width * 2, center_y ) )
        points.append( QC.QPoint( center_x - third_triangle_width, center_y + half_triangle_side ) )
        
        painter.drawPolygon( QG.QPolygon( points ) )
        
        #
        
        painter.setPen( QG.QPen( QP.GetSystemColour( QG.QPalette.Shadow ) ) )

        painter.setBrush( QG.QBrush( QG.QColor( QC.Qt.transparent ) ) )
        
        painter.drawRect( 0, 0, x, y )
        
    
    def paintEvent( self, event ):
        
        painter = QG.QPainter( self )
        
        self._Redraw( painter )
        
    
    def SetMedia( self, media ):
        
        self._media = media
        
        if self._media is None:
            
            needs_thumb = False
            
        else:
            
            needs_thumb = self._media.GetLocationsManager().IsLocal() and self._media.GetMime() in HC.MIMES_WITH_THUMBNAILS
            
        
        if needs_thumb:
            
            mime = self._media.GetMime()
            
            thumbnail_path = HG.client_controller.client_files_manager.GetThumbnailPath( self._media )
            
            self._thumbnail_qt_pixmap = ClientRendering.GenerateHydrusBitmap( thumbnail_path, mime ).GetQtPixmap()
            
            self.update()
            
        else:
            
            self._thumbnail_qt_pixmap = None
            
        
    
class OpenExternallyPanel( QW.QWidget ):
    
    def __init__( self, parent, media ):
        
        QW.QWidget.__init__( self, parent )
        
        self._new_options = HG.client_controller.new_options
        
        self._media = media
        
        vbox = QP.VBoxLayout()
        
        if self._media.GetLocationsManager().IsLocal() and self._media.GetMime() in HC.MIMES_WITH_THUMBNAILS:
            
            mime = self._media.GetMime()
            
            thumbnail_path = HG.client_controller.client_files_manager.GetThumbnailPath( self._media )
            
            qt_pixmap = ClientRendering.GenerateHydrusBitmap( thumbnail_path, mime ).GetQtPixmap()
            
            thumbnail_window = ClientGUICommon.BufferedWindowIcon( self, qt_pixmap )
            
            QP.AddToLayout( vbox, thumbnail_window, CC.FLAGS_CENTER )
            
        
        m_text = HC.mime_string_lookup[ media.GetMime() ]
        
        button = QW.QPushButton( 'open ' + m_text + ' externally', self )
        
        button.setFocusPolicy( QC.Qt.NoFocus )
        
        QP.AddToLayout( vbox, button, CC.FLAGS_EXPAND_BOTH_WAYS )
        
        self.setLayout( vbox )
        
        self.setCursor( QG.QCursor( QC.Qt.PointingHandCursor ) )
        
        button.clicked.connect( self.LaunchFile )
        
    
    def mousePressEvent( self, event ):
        
        if not ( event.modifiers() & ( QC.Qt.ShiftModifier | QC.Qt.ControlModifier | QC.Qt.AltModifier) ) and event.button() == QC.Qt.LeftButton:
            
            self.LaunchFile()
            
        else:
            
            event.ignore()
            
        
    
    def paintEvent( self, event ):
        
        # have to manually repaint background because of parent WA_OpaquePaintEvent
        
        painter = QG.QPainter( self )
        
        background_colour = self._new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND )
        
        painter.setBackground( QG.QBrush( background_colour ) )
        
        painter.eraseRect( painter.viewport() )
        
    
    def LaunchFile( self ):
        
        hash = self._media.GetHash()
        mime = self._media.GetMime()
        
        client_files_manager = HG.client_controller.client_files_manager
        
        path = client_files_manager.GetFilePath( hash, mime )
        
        launch_path = self._new_options.GetMimeLaunch( mime )
        
        HydrusPaths.LaunchFile( path, launch_path )
        
    
class StaticImage( QW.QWidget ):
    
    def __init__( self, parent ):
        
        QW.QWidget.__init__( self, parent )
        
        self.setAttribute( QC.Qt.WA_OpaquePaintEvent, True )
        
        self.setMouseTracking( True )
        
        self._media = None
        
        self._first_background_drawn = False
        
        self._image_renderer = None
        
        self._is_rendered = False
        
        self._canvas_qt_pixmap = None
        
    
    def _ClearCanvasBitmap( self ):
        
        self._canvas_qt_pixmap = None
        
        self._is_rendered = False
        
        self._first_background_drawn = False
        
    
    def _DrawBackground( self, painter ):
        
        new_options = HG.client_controller.new_options
        
        painter.setBackground( QG.QBrush( new_options.GetColour( CC.COLOUR_MEDIA_BACKGROUND ) ) )
        
        painter.eraseRect( painter.viewport() )
        
        self._first_background_drawn = True
        
    
    def _TryToDrawCanvasBitmap( self ):
        
        if self._image_renderer is not None and self._image_renderer.IsReady():
            
            my_size = self.size()
            
            width = my_size.width()
            height = my_size.height()
            
            self._canvas_qt_pixmap = HG.client_controller.bitmap_manager.GetQtPixmap( width, height )
            
            painter = QG.QPainter( self._canvas_qt_pixmap )
            
            self._DrawBackground( painter )
            
            qt_bitmap = self._image_renderer.GetQtImage( self.size() )
            
            painter.drawImage( 0, 0, qt_bitmap )
            
            self._is_rendered = True
            
        
    
    def paintEvent( self, event ):           
        
        if self._canvas_qt_pixmap is None:
            
            self._TryToDrawCanvasBitmap()
            
        
        painter = QG.QPainter( self )
        
        if self._canvas_qt_pixmap is None:
            
            self._DrawBackground( painter )
            
        else:
            
            painter.drawPixmap( 0, 0, self._canvas_qt_pixmap )
            
        
    
    def resizeEvent( self, event ):
        
        self._ClearCanvasBitmap()
        
    
    def IsRendered( self ):
        
        return self._is_rendered
        
    
    def SetMedia( self, media ):
        
        self._media = media
        
        image_cache = HG.client_controller.GetCache( 'images' )
        
        self._image_renderer = image_cache.GetImageRenderer( self._media )
        
        self._ClearCanvasBitmap()
        
        if not self._image_renderer.IsReady():
            
            HG.client_controller.gui.RegisterAnimationUpdateWindow( self )
            
        
        self.update()
        
    
    def SetNoneMedia( self ):
        
        self._media = None
        self._image_renderer = None
        
        self._ClearCanvasBitmap()
        
        self.update()
        
    
    def TIMERAnimationUpdate( self ):
        
        try:
            
            if self._image_renderer is None or self._image_renderer.IsReady():
                
                self.update()
                
                HG.client_controller.gui.UnregisterAnimationUpdateWindow( self )
                
            
        except:
            
            HG.client_controller.gui.UnregisterAnimationUpdateWindow( self )
            
            raise
            
        
    
