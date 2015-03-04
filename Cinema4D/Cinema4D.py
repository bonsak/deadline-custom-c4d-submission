from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

def GetDeadlinePlugin():
    return Cinema4DPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

class Cinema4DPlugin (DeadlinePlugin):
    LocalRendering = False
    LocalFilePath = ""
    NetworkFilePath = ""
    LocalMPFilePath = ""
    NetworkMPFilePath = ""
    FinishedFrameCount = 0

    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PostRenderTasksCallback += self.PostRenderTasks

    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.PreRenderTasksCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PostRenderTasksCallback

    def InitializeProcess( self ):
        self.StdoutHandling = True
        self.SingleFramesOnly = False
        self.PopupHandling = True

        #self.AddStdoutHandlerCallback("Error:.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Document not found.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Project not found.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Error rendering project.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Error loading project.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Error rendering document.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Error loading document.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Rendering failed.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Asset missing.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Invalid License from License Server.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Files cannot be written.*").HandleCallback += self.HandleStdoutError
        self.AddStdoutHandlerCallback(".*Enter Registration Data.*").HandleCallback += self.HandleStdoutError

        self.AddStdoutHandlerCallback(".*Rendering frame ([0-9]+) at.*").HandleCallback +=  self.HandleProgress
        self.AddStdoutHandlerCallback(".*Rendering successful.*").HandleCallback +=  self.HandleProgress2
        self.AddStdoutHandlerCallback(".*Rendering Phase: Finalize.*").HandleCallback +=  self.HandleFrameProgress

    def PreRenderTasks( self ):
        self.LogInfo("Starting Cinema 4D Task")
        self.FinishedFrameCount = 0

    def RenderExecutable( self ):
        version = self.GetIntegerPluginInfoEntryWithDefault( "Version", 12 )
        # RACECAR Custom
        self.LogInfo("This is the C4D version: " + str(version))

        C4DExeList = self.GetConfigEntry( "C4D_" + str(version) + "_RenderExecutable" )
        C4DExe = ""

        build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower().strip()
        if( build == "32bit" ):
            self.LogInfo( "Enforcing 32 bit build of Cinema 4D" )
            C4DExe = FileUtils.SearchFileListFor32Bit( C4DExeList )
            if( C4DExe == "" ):
                self.FailRender( "32 bit Cinema 4D " + str(version) + " render executable was not found in the semicolon separated list \"" + C4DExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        elif( build == "64bit" ):
            self.LogInfo( "Enforcing 64 bit build of Cinema 4D" )
            C4DExe = FileUtils.SearchFileListFor64Bit( C4DExeList )
            if( C4DExe == "" ):
                self.FailRender( "64 bit Cinema 4D " + str(version) + " render executable was not found in the semicolon separated list \"" + C4DExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        else:
            self.LogInfo( "Not enforcing a build of Cinema 4D" )
            C4DExe = FileUtils.SearchFileList( C4DExeList )
            if( C4DExe == "" ):
                self.FailRender( "Cinema 4D " + str(version) + " render executable was not found in the semicolon separated list \"" + C4DExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )

        return C4DExe

    def RenderArgument( self ):
        sceneFile = self.GetPluginInfoEntryWithDefault("SceneFile", self.GetDataFilename())
        sceneFile = RepositoryUtils.CheckPathMapping( sceneFile )
        sceneFile = self.ProcessPath( sceneFile )

        activeTake = self.GetPluginInfoEntryWithDefault("Take",0)

        argument = " -nogui"
        argument += " -render \"" + sceneFile + "\""
        argument += " -frame " + str(self.GetStartFrame()) + " " + str(self.GetEndFrame())
        argument += " -take \"" + str(activeTake) + "\""

        threads = self.GetIntegerPluginInfoEntryWithDefault("Threads",0)
        if threads > 0:
            argument += " -threads " + str(threads)

        width = self.GetIntegerPluginInfoEntryWithDefault("Width",0)
        height = self.GetIntegerPluginInfoEntryWithDefault("Height",0)

        if(width>0 and height>0):
            argument += " -oresolution " + str(width) + " " + str(height)

        self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )

        # Build the output filename from the path and prefix
        filepath = self.GetPluginInfoEntryWithDefault("FilePath","").strip()
        filepath = RepositoryUtils.CheckPathMapping( filepath )
        if(filepath != ""):
            filepath = self.ProcessPath( filepath )

            if self.LocalRendering:
                self.NetworkFilePath = filepath

                filepath = self.CreateTempDirectory( "c4dOutput" )
                filepath = self.ProcessPath( filepath )

                self.LocalFilePath = filepath

                self.LogInfo( "Rendering main output to local drive, will copy files and folders to final location after render is complete" )
            else:
                self.LogInfo( "Rendering main output to network drive" )

            fileprefix = self.GetPluginInfoEntryWithDefault("FilePrefix","").strip()
            argument += " -oimage \"" + Path.Combine(filepath, fileprefix) + "\""

        # Build the multipass output filename from the path and prefix
        multifilepath = self.GetPluginInfoEntryWithDefault("MultiFilePath","").strip()
        multifilepath = RepositoryUtils.CheckPathMapping( multifilepath )
        if(multifilepath != ""):
            multifilepath = self.ProcessPath( multifilepath )

            if self.LocalRendering:
                self.NetworkMPFilePath = multifilepath

                multifilepath = self.CreateTempDirectory( "c4dOutputMP" )
                multifilepath = self.ProcessPath( multifilepath )

                self.LocalMPFilePath = multifilepath

                self.LogInfo( "Rendering multipass output to local drive, will copy files and folders to final location after render is complete" )
            else:
                self.LogInfo( "Rendering multipass output to network drive" )

            multifileprefix = self.GetPluginInfoEntryWithDefault("MultiFilePrefix","").strip()
            argument += " -omultipass \"" + Path.Combine(multifilepath, multifileprefix) + "\""

        return argument

    def PostRenderTasks( self ):
        if( self.LocalRendering ):
            if( self.NetworkFilePath != "" ):
                self.LogInfo( "Moving main output files and folders from " + self.LocalFilePath + " to " + self.NetworkFilePath )
                self.VerifyAndMoveDirectory( self.LocalFilePath, self.NetworkFilePath, False, -1 )
            if( self.NetworkMPFilePath != "" ):
                self.LogInfo( "Moving multipass output files and folders from " + self.LocalMPFilePath + " to " + self.NetworkMPFilePath )
                self.VerifyAndMoveDirectory( self.LocalMPFilePath, self.NetworkMPFilePath, False, -1 )

        self.LogInfo("Finished Cinema 4D Task")

    def ProcessPath( self, filepath ):
        if SystemUtils.IsRunningOnWindows():
            filepath = filepath.replace("/","\\")
            if filepath.startswith( "\\" ) and not filepath.startswith( "\\\\" ):
                filepath = "\\" + filepath
        else:
            filepath = filepath.replace("\\","/")
        return filepath

    def HandleProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( 100 * ( int(self.GetRegexMatch(1)) - startFrame ) / ( endFrame - startFrame + 1 ) )
        self.SetStatusMessage( self.GetRegexMatch(0) )

    def HandleProgress2( self ):
        self.SetProgress( 100 )
        self.SetStatusMessage( self.GetRegexMatch(0) )

    def HandleFrameProgress( self ):
        self.FinishedFrameCount = self.FinishedFrameCount + 1

        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( 100 * self.FinishedFrameCount / ( endFrame - startFrame + 1 ) )

    def HandleStdoutError( self ):
        self.FailRender(self.GetRegexMatch(0))
