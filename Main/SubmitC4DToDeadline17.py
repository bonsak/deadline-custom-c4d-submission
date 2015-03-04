import os, sys, subprocess, re, traceback

try:
    import ConfigParser
except:
    print( "Could not load ConfigParser module, sticky settings will not be loaded/saved" )

import c4d
from c4d import documents
from c4d import gui
from c4d import plugins

## The submission dialog class.
class SubmitC4DToDeadlineDialog (gui.GeDialog):
    DeadlineHome = ""
    DeadlineSettings = ""
    DeadlineTemp = ""
    DeadlineRepositoryRoot = ""
    ConfigFile = ""
    SanityCheckFile = ""

    MaximumPriority = 100
    Pools = []
    SecondaryPools = []
    Groups = []
    OnComplete = []
    Builds = []

    ShotgunJobSettings = {}
    FTrackJobSettings = {}

    integrationType = 0 #0 = Shotgun 1 = FTrack

    LabelWidth = 200
    TextBoxWidth = 600
    ComboBoxWidth = 180
    RangeBoxWidth = 190

    SliderLabelWidth = 180

    LabelID = 1000
    NameBoxID = 10
    CommentBoxID = 20
    DepartmentBoxID = 30
    PoolBoxID = 40
    SecondaryPoolBoxID = 45
    GroupBoxID = 50
    PriorityBoxID = 60
    AutoTimeoutBoxID = 65
    TaskTimeoutBoxID = 70
    ConcurrentTasksBoxID = 80
    LimitConcurrentTasksBoxID = 85
    MachineLimitBoxID = 90
    IsBlacklistBoxID = 94
    MachineListBoxID=  96
    MachineListButtonID = 98
    LimitGroupsBoxID = 100
    LimitGroupsButtonID = 110
    DependenciesBoxID = 120
    DependenciesButtonID = 130
    OnCompleteBoxID = 140
    SubmitSuspendedBoxID = 150
    FramesBoxID = 160
    ChunkSizeBoxID = 170
    ThreadsBoxID = 180
    BuildBoxID = 190
    LocalRenderingBoxID = 195
    SubmitSceneBoxID = 200
    ExportProjectBoxID = 205

    ConnectToIntegrationButtonID = 210
    UseIntegrationBoxID = 220
    IntegrationVersionBoxID = 225
    IntegrationInfoBoxID = 230
    IntegrationDescriptionBoxID = 235

    UseDraftBoxID = 240
    UploadDraftToShotgunBoxID = 250
    DraftTemplateBoxID = 260
    DraftTemplateButtonID = 270
    DraftUserBoxID = 280
    DraftEntityBoxID = 290
    DraftVersionBoxID = 300
    DraftUseShotgunDataButtonID = 310
    DraftExtraArgsBoxID = 320

    IntegrationTypeBoxID = 330
    uploadLayout = 360
    UploadMovieBoxID = 340
    UploadFilmStripBoxID = 350

    SubmitButtonID = 910
    CancelButtonID = 920

    def __init__( self ):
        c4d.StatusSetBar( 15 )

        stdout = None

        # Get the current user Deadline home directory, which we'll use to store settings and temp files.
        print( "Getting Deadline home folder" )
        self.DeadlineHome = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
        self.DeadlineHome = self.DeadlineHome.replace( "\n", "" ).replace( "\r", "" )

        self.DeadlineSettings = self.DeadlineHome + "/settings"
        self.DeadlineTemp = self.DeadlineHome + "/temp"

        c4d.StatusSetBar( 30 )

        # Get the maximum priority.
        print( "Getting maximum priority" )
        try:
            output = CallDeadlineCommand( ["-getmaximumpriority",] )
            self.MaximumPriority = int(output)
        except:
            self.MaximumPriority = 100

        c4d.StatusSetBar( 45 )

        # Get the pools.
        print( "Loading pools" )
        output = CallDeadlineCommand( ["-pools",] )

        self.Pools = []
        self.SecondaryPools = []
        for line in output.splitlines():
            currPool = line.replace( "\n", "" )
            self.Pools.append( currPool )
            self.SecondaryPools.append( currPool )

        if len(self.Pools) == 0:
            self.Pools.append( "none" )
            self.SecondaryPools.append( "none" )

        # Need to have a space, since empty strings don't seem to show up.
        self.SecondaryPools.insert( 0, " " )

        c4d.StatusSetBar( 60 )

        # Get the groups.
        print( "Loading groups" )
        output = CallDeadlineCommand( ["-groups",] )

        self.Groups = []
        for line in output.splitlines():
            self.Groups.append( line.replace( "\n", "" ) )

        if len(self.Groups) == 0:
            self.Groups.append( "none" )

        c4d.StatusSetBar( 75 )

        # Get the repo root.
        print( "Getting Repository root" )
        self.DeadlineRepositoryRoot = CallDeadlineCommand( ["-GetRepositoryRoot",] )
        self.DeadlineRepositoryRoot = self.DeadlineRepositoryRoot.replace( "\n", "" ).replace( "\r", "" )

        c4d.StatusSetBar( 100 )

        # Set On Job Complete settings.
        self.OnComplete = []
        self.OnComplete.append( "Archive" )
        self.OnComplete.append( "Delete" )
        self.OnComplete.append( "Nothing" )

        # Set Build settings.
        self.Builds = []
        self.Builds.append( "None" )
        self.Builds.append( "32bit" )
        self.Builds.append( "64bit" )

        c4d.StatusClear()

    def GetLabelID( self ):
        self.LabelID = self.LabelID + 1
        return self.LabelID

    def StartGroup( self, label ):
        self.GroupBegin( self.GetLabelID(), 0, 0, 20, label, 0 )
        self.GroupBorder( c4d.BORDER_THIN_IN )
        self.GroupBorderSpace( 4, 4, 4, 4 )

    def EndGroup( self ):
        self.GroupEnd()

    def AddTextBoxGroup( self, id, label ):
        self.GroupBegin( self.GetLabelID(), 0, 2, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, label, 0 )
        self.AddEditText( id, 0, self.TextBoxWidth, 0 )
        self.GroupEnd()

    def AddComboBoxGroup( self, id, label, checkboxID=-1, checkboxLabel="" ):
        self.GroupBegin( self.GetLabelID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, label, 0 )
        self.AddComboBox( id, 0, self.ComboBoxWidth, 0 )
        if checkboxID >= 0 and checkboxLabel != "":
            self.AddCheckbox( checkboxID, 0, self.LabelWidth + self.ComboBoxWidth + 12, 0, checkboxLabel )
        elif checkboxID > -2:
            self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth + self.ComboBoxWidth + 12, 0, "", 0 )
        self.GroupEnd()

    def AddRangeBoxGroup( self, id, label, min, max, inc, checkboxID=-1, checkboxLabel="" ):
        self.GroupBegin( self.GetLabelID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, label, 0 )
        self.AddEditNumberArrows( id, 0, self.RangeBoxWidth, 0 )
        if checkboxID >= 0 and checkboxLabel != "":
            self.AddCheckbox( checkboxID, 0, self.LabelWidth + self.ComboBoxWidth + 12, 0, checkboxLabel )
        else:
            self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth + self.RangeBoxWidth + 4, 0, "", 0 )
        self.SetLong( id, min, min, max, inc )
        self.GroupEnd()

    def AddSelectionBoxGroup( self, id, label, buttonID ):
        self.GroupBegin( self.GetLabelID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, label, 0 )
        self.AddEditText( id, 0, self.TextBoxWidth - 56, 0 )
        self.AddButton( buttonID, 0, 8, 0, "..." )
        self.GroupEnd()

    def AddCheckboxGroup( self, checkboxID, checkboxLabel, textID, buttonID ):
        self.GroupBegin( self.GetLabelID(), 0, 3, 1, "", 0 )
        self.AddCheckbox( checkboxID, 0, self.LabelWidth, 0, checkboxLabel )
        self.AddEditText( textID, 0, self.TextBoxWidth - 56, 0 )
        self.AddButton( buttonID, 0, 8, 0, "..." )
        self.GroupEnd()

    ## This is called when the dialog is initialized.
    def CreateLayout( self ):
        self.SetTitle( "Submit To Deadline 17" )

        self.TabGroupBegin( self.GetLabelID(), 0 )
        #General Options Tab
        self.GroupBegin( self.GetLabelID(), 0, 0, 20, "General Options", 0 )
        self.GroupBorderNoTitle( c4d.BORDER_NONE )

        self.StartGroup( "Job Description" )
        self.AddTextBoxGroup( self.NameBoxID, "Job Name" )
        self.AddTextBoxGroup( self.CommentBoxID, "Comment" )
        self.AddTextBoxGroup( self.DepartmentBoxID, "Department" )
        self.EndGroup()

        self.StartGroup( "Job Options" )
        self.AddComboBoxGroup( self.PoolBoxID, "Pool" )
        self.AddComboBoxGroup( self.SecondaryPoolBoxID, "Secondary Pool" )
        self.AddComboBoxGroup( self.GroupBoxID, "Group" )
        self.AddRangeBoxGroup( self.PriorityBoxID, "Priority", 0, 100, 1 )
        self.AddRangeBoxGroup( self.TaskTimeoutBoxID, "Task Timeout", 0, 999999, 1, self.AutoTimeoutBoxID, "Enable Auto Task Timeout" )
        self.AddRangeBoxGroup( self.ConcurrentTasksBoxID, "Concurrent Tasks", 1, 16, 1, self.LimitConcurrentTasksBoxID, "Limit Tasks To Slave's Task Limit" )
        self.AddRangeBoxGroup( self.MachineLimitBoxID, "Machine Limit", 0, 999999, 1, self.IsBlacklistBoxID, "Machine List is a Blacklist" )
        self.AddSelectionBoxGroup( self.MachineListBoxID, "Machine List", self.MachineListButtonID )
        self.AddSelectionBoxGroup( self.LimitGroupsBoxID, "Limit Groups", self.LimitGroupsButtonID )
        self.AddSelectionBoxGroup( self.DependenciesBoxID, "Dependencies", self.DependenciesButtonID )
        self.AddComboBoxGroup( self.OnCompleteBoxID, "On Job Complete", self.SubmitSuspendedBoxID, "Submit Job As Suspended" )
        self.EndGroup()

        self.StartGroup( "Cinema 4D Options" )
        self.AddTextBoxGroup( self.FramesBoxID, "Frame List" )
        #self.AddRangeBoxGroup( self.ChunkSizeBoxID, "Frames Per Task", 1, 999999, 1 )
        #self.AddRangeBoxGroup( self.ThreadsBoxID, "Threads To Use", 0, 16, 1 )
        #self.AddComboBoxGroup( self.BuildBoxID, "Build To Force", self.SubmitSceneBoxID, "Submit Cinema 4D Scene File" )

        self.AddRangeBoxGroup( self.ChunkSizeBoxID, "Frames Per Task", 1, 999999, 1, self.SubmitSceneBoxID, "Submit Cinema 4D Scene File" )
        self.AddRangeBoxGroup( self.ThreadsBoxID, "Threads To Use", 0, 256, 1, self.ExportProjectBoxID, "Export Project Before Submission" )
        self.AddComboBoxGroup( self.BuildBoxID, "Build To Force", self.LocalRenderingBoxID, "Enable Local Rendering" )

        self.EndGroup()

        self.GroupEnd() #General Options Tab

        #Shotgun/Draft Tab
        self.GroupBegin( self.GetLabelID(), c4d.BFV_TOP, 0, 20, "Integration", 0 )
        self.GroupBorderNoTitle( c4d.BORDER_NONE )

        self.StartGroup( "Project Management" )
        self.GroupBegin( self.GetLabelID(), 0, 3, 1, "", 0 )
        #self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, "Project Management", 0 )
        #self.AddComboBox( self.IntegrationTypeBoxID, 0, self.ComboBoxWidth, 0 )
        self.AddComboBoxGroup( self.IntegrationTypeBoxID, "Project Management" )
        self.GroupEnd()

        self.GroupBegin( self.GetLabelID(), 0, 3, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, "", 0 )
        #self.AddComboBox( self.IntegrationTypeBoxID, 0, self.ComboBoxWidth, 0 )
        self.AddButton( self.ConnectToIntegrationButtonID, 0, self.ComboBoxWidth, 0, "Connect..." )
        self.AddCheckbox( self.UseIntegrationBoxID, 0, self.LabelWidth+self.ComboBoxWidth + 12, 0, "Create new version" )
        self.Enable( self.UseIntegrationBoxID, False )
        self.GroupEnd()
        self.AddTextBoxGroup( self.IntegrationVersionBoxID, "Version Name" )
        self.AddTextBoxGroup( self.IntegrationDescriptionBoxID, "Description" )

        self.GroupBegin( self.GetLabelID(), c4d.BFV_TOP, 2, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), c4d.BFV_TOP, self.LabelWidth + 3, 0, "Selected Entity Info", 0 )
        self.AddMultiLineEditText( self.IntegrationInfoBoxID, c4d.BFV_TOP, self.TextBoxWidth + 20, 95 )
        self.Enable( self.IntegrationInfoBoxID, False )
        self.GroupEnd()


        self.GroupBegin( self.uploadLayout, 0, 3, 1, "", 0 )
        self.AddStaticText( self.uploadLayout+1, 0, self.LabelWidth, 0, "Draft Options", 0 )
        self.AddCheckbox( self.UploadMovieBoxID, 0, self.LabelWidth+ + 12, 0, "Create/Upload Movie" )
        self.Enable( self.UploadMovieBoxID, False )
        self.AddCheckbox( self.UploadFilmStripBoxID, 0, self.LabelWidth + self.ComboBoxWidth + 12, 0, "Create/Upload Film Strip" )
        self.Enable( self.UploadFilmStripBoxID, False )
        self.GroupEnd()

        self.EndGroup() #Shotgun group

        self.StartGroup( "Draft" )
        self.GroupBegin( self.GetLabelID(), c4d.BFH_LEFT, 3, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, "", 0 )
        self.AddCheckbox( self.UseDraftBoxID, 0, 290, 0, "Submit Draft Job On Completion" )
        self.AddCheckbox( self.UploadDraftToShotgunBoxID, 0, 302, 0, "Upload Draft Results To Shotgun" )
        self.EndGroup()

        self.AddSelectionBoxGroup( self.DraftTemplateBoxID, "Draft Template", self.DraftTemplateButtonID )
        self.AddTextBoxGroup( self.DraftUserBoxID, "User Name" )
        self.AddTextBoxGroup( self.DraftEntityBoxID, "Entity Name" )
        self.AddTextBoxGroup( self.DraftVersionBoxID, "Version Name" )
        self.AddTextBoxGroup( self.DraftExtraArgsBoxID, "Additional Args" )

        self.GroupBegin( self.GetLabelID(), c4d.BFH_LEFT, 2, 1, "", 0 )
        self.AddStaticText( self.GetLabelID(), 0, self.LabelWidth, 0, "", 0 )
        self.AddButton( self.DraftUseShotgunDataButtonID, 0, self.ComboBoxWidth, 0, "Use Shotgun Data" )
        self.EndGroup()
        self.EndGroup() #Draft group

        #Updates enabled status of the draft controls
        self.Command( self.UseDraftBoxID, None )
        self.Command( self.UseIntegrationBoxID, None )

        self.GroupEnd() #Shotgun/Draft tab
        self.GroupEnd() #Tab group

        self.GroupBegin( self.GetLabelID(), 0, 2, 1, "", 0 )
        self.AddButton( self.SubmitButtonID, 0, 100, 0, "Submit" )
        self.AddButton( self.CancelButtonID, 0, 100, 0, "Cancel" )
        self.GroupEnd()

        return True

    ## This is called after the dialog has been initialized.
    def InitValues( self ):
        scene = documents.GetActiveDocument()
        sceneName = scene.GetDocumentName()
        frameRate = scene.GetFps()

        startFrame = 0
        endFrame = 0
        stepFrame = 0

        renderData = scene.GetActiveRenderData().GetData()
        frameMode = renderData.GetLong( c4d.RDATA_FRAMESEQUENCE )
        if frameMode == c4d.RDATA_FRAMESEQUENCE_MANUAL:
            startFrame = renderData.GetTime( c4d.RDATA_FRAMEFROM ).GetFrame( frameRate )
            endFrame = renderData.GetTime( c4d.RDATA_FRAMETO ).GetFrame( frameRate )
            stepFrame = renderData.GetLong( c4d.RDATA_FRAMESTEP )
        elif frameMode == c4d.RDATA_FRAMESEQUENCE_CURRENTFRAME:
            startFrame = scene.GetTime().GetFrame( frameRate )
            endFrame = startFrame
            stepFrame = 1
        elif frameMode == c4d.RDATA_FRAMESEQUENCE_ALLFRAMES:
            startFrame = scene.GetMinTime().GetFrame( frameRate )
            endFrame = scene.GetMaxTime().GetFrame( frameRate )
            stepFrame = renderData.GetLong( c4d.RDATA_FRAMESTEP )
        elif frameMode == c4d.RDATA_FRAMESEQUENCE_PREVIEWRANGE:
            startFrame = scene.GetLoopMinTime().GetFrame( frameRate )
            endFrame = scene.GetLoopMaxTime().GetFrame( frameRate )
            stepFrame = renderData.GetLong( c4d.RDATA_FRAMESTEP )

        frameList = str(startFrame)
        if startFrame != endFrame:
            frameList = frameList + "-" + str(endFrame)
        if stepFrame > 1:
            frameList = frameList + "x" + str(stepFrame)

        initName = sceneName
        initComment = ""
        initDepartment = ""

        initPool = "none"
        initSecondaryPool = " " # Needs to have a space
        initGroup = "none"
        initPriority = 50
        initMachineLimit = 0
        initTaskTimeout = 0
        initAutoTaskTimeout = False
        initConcurrentTasks = 1
        initLimitConcurrentTasks = True
        initIsBlacklist = False
        initMachineList = ""
        initLimitGroups = ""
        initDependencies = ""
        initOnComplete = "Nothing"
        initSubmitSuspended = False

        initFrames = frameList
        initChunkSize = 1
        initThreads = 0
        initBuild = "None"
        initSubmitScene = False
        initExportProject = False
        initLocalRendering = False

        initOverrideOutput = False
        initOverrideMultipass = False

        initDraftTemplate = ""
        initDraftUser = ""
        initDraftEntity = ""
        initDraftVersion = ""
        initDraftExtraArgs = ""

        initIntegration = "Shotgun"

        # Read in sticky settings
        self.ConfigFile = self.DeadlineSettings + "/c4d_py_submission.ini"
        try:
            if os.path.isfile( self.ConfigFile ):
                config = ConfigParser.ConfigParser()
                config.read( self.ConfigFile )

                if config.has_section( "Sticky" ):
                    if config.has_option( "Sticky", "Department" ):
                        initDepartment = config.get( "Sticky", "Department" )
                    if config.has_option( "Sticky", "Pool" ):
                        initPool = config.get( "Sticky", "Pool" )
                    if config.has_option( "Sticky", "SecondaryPool" ):
                        initSecondaryPool = config.get( "Sticky", "SecondaryPool" )
                    if config.has_option( "Sticky", "Group" ):
                        initGroup = config.get( "Sticky", "Group" )
                    if config.has_option( "Sticky", "Priority" ):
                        initPriority = config.getint( "Sticky", "Priority" )
                    if config.has_option( "Sticky", "MachineLimit" ):
                        initMachineLimit = config.getint( "Sticky", "MachineLimit" )
                    if config.has_option( "Sticky", "LimitGroups" ):
                        initLimitGroups = config.get( "Sticky", "LimitGroups" )
                    if config.has_option( "Sticky", "IsBlacklist" ):
                        initIsBlacklist = config.getboolean( "Sticky", "IsBlacklist" )
                    if config.has_option( "Sticky", "MachineList" ):
                        initMachineList = config.get( "Sticky", "MachineList" )
                    if config.has_option( "Sticky", "SubmitSuspended" ):
                        initSubmitSuspended = config.getboolean( "Sticky", "SubmitSuspended" )
                    if config.has_option( "Sticky", "ChunkSize" ):
                        initChunkSize = config.getint( "Sticky", "ChunkSize" )
                    if config.has_option( "Sticky", "Threads" ):
                        initThreads = config.getint( "Sticky", "Threads" )
                    if config.has_option( "Sticky", "Build" ):
                        initBuild = config.get( "Sticky", "Build" )
                    if config.has_option( "Sticky", "SubmitScene" ):
                        initSubmitScene = config.getboolean( "Sticky", "SubmitScene" )
                    if config.has_option( "Sticky", "OverrideOutput" ):
                        initOverrideOutput = config.getboolean( "Sticky", "OverrideOutput" )
                    if config.has_option( "Sticky", "OverrideMultipass" ):
                        initOverrideMultipass = config.getboolean( "Sticky", "OverrideMultipass" )
                    if config.has_option( "Sticky", "DraftTemplate" ):
                        initDraftTemplate = config.get( "Sticky", "DraftTemplate" )
                    if config.has_option( "Sticky", "DraftUser" ):
                        initDraftUser = config.get( "Sticky", "DraftUser" )
                    if config.has_option( "Sticky", "DraftEntity" ):
                        initDraftEntity = config.get( "Sticky", "DraftEntity" )
                    if config.has_option( "Sticky", "DraftVersion" ):
                        initDraftVersion = config.get( "Sticky", "DraftVersion" )
                    if config.has_option( "Sticky", "ExportProject" ):
                        initExportProject = config.getboolean( "Sticky", "ExportProject" )
                    if config.has_option( "Sticky", "LocalRendering" ):
                        initLocalRendering = config.getboolean( "Sticky", "LocalRendering" )
                    if config.has_option( "Sticky", "DraftExtraArgs" ):
                        initDraftExtraArgs = config.get( "Sticky", "DraftExtraArgs" )
                    if config.has_option( "Sticky", "Integration" ):
                        initIntegration = config.get( "Sticky", "Integration" )
        except:
            print( "Could not read sticky settings" )

        if initPriority > self.MaximumPriority:
            initPriority = self.MaximumPriority / 2

        # Populate the combo boxes, and figure out the default selected index if necessary.
        selectedPoolID = 0
        for i in range( 0, len(self.Pools) ):
            self.AddChild( self.PoolBoxID, i, self.Pools[ i ] )
            if initPool == self.Pools[ i ]:
                selectedPoolID = i

        selectedSecondaryPoolID = 0
        for i in range( 0, len(self.SecondaryPools) ):
            self.AddChild( self.SecondaryPoolBoxID, i, self.SecondaryPools[ i ] )
            if initSecondaryPool == self.SecondaryPools[ i ]:
                selectedSecondaryPoolID = i

        selectedGroupID = 0
        for i in range( 0, len(self.Groups) ):
            self.AddChild( self.GroupBoxID, i, self.Groups[ i ] )
            if initGroup == self.Groups[ i ]:
                selectedGroupID = i

        selectedOnCompleteID = 0
        for i in range( 0, len(self.OnComplete) ):
            self.AddChild( self.OnCompleteBoxID, i, self.OnComplete[ i ] )
            if initOnComplete == self.OnComplete[ i ]:
                selectedOnCompleteID = i

        selectedBuildID = 0
        for i in range( 0, len(self.Builds) ):
            self.AddChild( self.BuildBoxID, i, self.Builds[ i ] )
            if initBuild == self.Builds[ i ]:
                selectedBuildID = i

        self.AddChild( self.IntegrationTypeBoxID, 0, "Shotgun" )
        if initIntegration == "FTrack":
            self.integrationType = 1
        self.AddChild( self.IntegrationTypeBoxID, 1, "FTrack" )

        # Set the default settings.
        self.SetString( self.NameBoxID, initName )
        self.SetString( self.CommentBoxID, initComment )
        self.SetString( self.DepartmentBoxID, initDepartment )

        self.SetLong( self.PoolBoxID, selectedPoolID )
        self.SetLong( self.SecondaryPoolBoxID, selectedSecondaryPoolID )
        self.SetLong( self.GroupBoxID, selectedGroupID )
        self.SetLong( self.PriorityBoxID, initPriority, 0, self.MaximumPriority, 1 )
        self.SetLong( self.MachineLimitBoxID, initMachineLimit )
        self.SetLong( self.TaskTimeoutBoxID, initTaskTimeout )
        self.SetBool( self.AutoTimeoutBoxID, initAutoTaskTimeout )
        self.SetLong( self.ConcurrentTasksBoxID, initConcurrentTasks )
        self.SetBool( self.LimitConcurrentTasksBoxID, initLimitConcurrentTasks )
        self.SetBool( self.IsBlacklistBoxID, initIsBlacklist )
        self.SetString( self.MachineListBoxID, initMachineList )
        self.SetString( self.LimitGroupsBoxID, initLimitGroups )
        self.SetString( self.DependenciesBoxID, initDependencies )
        self.SetLong( self.OnCompleteBoxID, selectedOnCompleteID )
        self.SetBool( self.SubmitSuspendedBoxID, initSubmitSuspended )

        self.SetString( self.FramesBoxID, initFrames )
        self.SetLong( self.ChunkSizeBoxID, initChunkSize )
        self.SetLong( self.ThreadsBoxID, initThreads )
        self.SetBool( self.SubmitSceneBoxID, initSubmitScene )
        self.SetBool( self.ExportProjectBoxID, initExportProject )
        self.SetLong( self.BuildBoxID, selectedBuildID )
        self.SetBool( self.LocalRenderingBoxID, initLocalRendering )

        self.SetLong( self.IntegrationTypeBoxID, self.integrationType )

        self.SetString( self.DraftTemplateBoxID, initDraftTemplate )
        self.SetString( self.DraftUserBoxID, initDraftUser )
        self.SetString( self.DraftEntityBoxID, initDraftEntity )
        self.SetString( self.DraftVersionBoxID, initDraftVersion )
        self.SetString( self.DraftExtraArgsBoxID, initDraftExtraArgs )

        self.Enable( self.SubmitSceneBoxID, not initExportProject )

        #If 'CustomSanityChecks.py' exists, then it executes. This gives the user the ability to change default values
        if os.name == 'nt':
            self.SanityCheckFile = self.DeadlineRepositoryRoot + "\\submission\\Cinema4D\\Main\\CustomSanityChecks.py"
        else:
            self.SanityCheckFile = self.DeadlineRepositoryRoot + "/submission/Cinema4D/Main/CustomSanityChecks.py"

        if os.path.isfile( self.SanityCheckFile ):
            print ( "Running sanity check script: " + self.SanityCheckFile )
            try:
                import CustomSanityChecks
                sanityResult = CustomSanityChecks.RunSanityCheck( self )
                if not sanityResult:
                    print( "Sanity check returned False, exiting" )
                    self.Close()
            except:
                gui.MessageDialog( "Could not run CustomSanityChecks.py script: " + traceback.format_exc() )

        return True

    ## This is called when a user clicks on a button or changes the value of a field.
    def Command( self, id, msg ):
        # The Limit Group browse button was pressed.
        if id == self.LimitGroupsButtonID:
            c4d.StatusSetSpin()

            currLimitGroups = self.GetString( self.LimitGroupsBoxID )
            result = CallDeadlineCommand( ["-selectlimitgroups",currLimitGroups] )
            result = result.replace( "\n", "" ).replace( "\r", "" )

            if result != "Action was cancelled by user":
                self.SetString( self.LimitGroupsBoxID, result )

            c4d.StatusClear()

        # The Dependencies browse button was pressed.
        elif id == self.DependenciesButtonID:
            c4d.StatusSetSpin()

            currDependencies = self.GetString( self.DependenciesBoxID )
            result = CallDeadlineCommand( ["-selectdependencies",currDependencies] )
            result = result.replace( "\n", "" ).replace( "\r", "" )

            if result != "Action was cancelled by user":
                self.SetString( self.DependenciesBoxID, result )

            c4d.StatusClear()

        elif id == self.MachineListButtonID:
            c4d.StatusSetSpin()

            currMachineList = self.GetString( self.MachineListBoxID )
            result = CallDeadlineCommand( ["-selectmachinelist",currMachineList] )
            result = result.replace( "\n", "" ).replace( "\r", "" )

            if result != "Action was cancelled by user":
                self.SetString( self.MachineListBoxID, result )

            c4d.StatusClear()

        elif id == self.ExportProjectBoxID:
            self.Enable( self.SubmitSceneBoxID, not self.GetBool( self.ExportProjectBoxID ) )

        elif id == self.ConnectToIntegrationButtonID:
            c4d.StatusSetSpin()

            try:
                script = ""
                if self.integrationType == 0:
                    script = ("%s/events/Shotgun/ShotgunUI.py" % self.DeadlineRepositoryRoot)
                else:
                    script = ("%s/submission/FTrack/Main/FTrackUI.py" % self.DeadlineRepositoryRoot)

                output = CallDeadlineCommand( ["-ExecuteScript",script,"Cinema4D"], False )
                outputLines = output.splitlines()

                tempKVPs = {}

                for line in outputLines:
                    line = line.strip()
                    tokens = line.split( '=', 1 )

                    if len( tokens ) > 1:
                        key = tokens[0]
                        value = tokens[1]
                        tempKVPs[key] = value

                if len( tempKVPs ) > 0:
                    if self.integrationType == 0:
                        self.ShotgunJobSettings = tempKVPs
                    else:
                        self.FTrackJobSettings = tempKVPs
                self.updateDisplay()

                self.Command( self.UseIntegrationBoxID, None )
            finally:
                c4d.StatusClear()

        elif id == self.UseIntegrationBoxID:
            enable = self.GetBool( self.UseIntegrationBoxID )
            self.Enable( self.IntegrationVersionBoxID, enable )
            self.Enable( self.IntegrationDescriptionBoxID, enable )
            self.Enable( self.UploadMovieBoxID, enable )
            self.Enable( self.UploadFilmStripBoxID, enable )

            enable = (enable and self.GetBool( self.UseDraftBoxID ))
            self.Enable( self.UploadDraftToShotgunBoxID, enable )
            self.Enable( self.DraftUseShotgunDataButtonID, enable )

        elif id == self.IntegrationVersionBoxID:
            if integrationType == 0:
                self.ShotgunJobSettings[ 'VersionName' ] = self.GetString( self.IntegrationVersionBoxID )
            else:
                self.FTrackJobSettings[ 'FT_AssetName' ] = self.GetString( self.IntegrationVersionBoxID )

        elif id == self.IntegrationDescriptionBoxID:
            if integrationType == 0:
                self.ShotgunJobSettings[ 'Description' ] = self.GetString( self.IntegrationDescriptionBoxID )
            else:
                self.FTrackJobSettings[ 'FT_Description' ] = self.GetString( self.IntegrationVersionBoxID )
        elif id == self.IntegrationTypeBoxID:
            self.integrationType = self.GetLong(self.IntegrationTypeBoxID)
            self.HideElement( self.uploadLayout+1,self.integrationType)
            self.HideElement(self.UploadMovieBoxID,self.integrationType)
            self.HideElement(self.UploadFilmStripBoxID,self.integrationType)
            self.LayoutChanged(self.uploadLayout)
            self.updateDisplay()
        elif id == self.UseDraftBoxID:
            enable = self.GetBool( self.UseDraftBoxID )
            self.Enable( self.DraftTemplateBoxID, enable )
            self.Enable( self.DraftTemplateButtonID, enable )
            self.Enable( self.DraftUserBoxID, enable )
            self.Enable( self.DraftEntityBoxID, enable )
            self.Enable( self.DraftVersionBoxID, enable )
            self.Enable( self.DraftExtraArgsBoxID, enable )

            enable = (enable and self.GetBool( self.UseIntegrationBoxID ))
            self.Enable( self.UploadDraftToShotgunBoxID, enable )
            self.Enable( self.DraftUseShotgunDataButtonID, enable )

        elif id == self.DraftTemplateButtonID:
            c4d.StatusSetSpin()

            try:
                currTemplate = self.GetString( self.DraftTemplateBoxID )
                result = CallDeadlineCommand( ["-SelectFilenameLoad", currTemplate] )

                if result != "Action was cancelled by user" and result != "":
                    self.SetString( self.DraftTemplateBoxID, result )
            finally:
                c4d.StatusClear()

        elif id == self.DraftUseShotgunDataButtonID:
            shotgunValues = self.GetString( self.IntegrationInfoBoxID ).split( '\n' )

            user = self.ShotgunJobSettings.get( 'UserName', "" )
            task = self.ShotgunJobSettings.get( 'TaskName', "" )
            project = self.ShotgunJobSettings.get( 'ProjectName', "" )
            entity = self.ShotgunJobSettings.get( 'EntityName', "" )
            version = self.ShotgunJobSettings.get( 'VersionName', "" )
            draftTemplate = self.ShotgunJobSettings.get( 'DraftTemplate', "" )

            #set any relevant values
            self.SetString( self.DraftUserBoxID, user )
            self.SetString( self.DraftVersionBoxID, version )

            if task.strip() != "" and task.strip() != "None":
                self.SetString( self.DraftEntityBoxID, task )
            elif project.strip() != "" and entity.strip() != "":
                self.SetString( self.DraftEntityBoxID, "%s > %s" % (project, entity) )

            if draftTemplate.strip() != "" and draftTemplate != "None":
                self.SetString( self.DraftTemplateBoxID, draftTemplate )

        # The Submit or the Cancel button was pressed.
        elif id == self.SubmitButtonID or id == self.CancelButtonID:
            jobName = self.GetString( self.NameBoxID )
            comment = self.GetString( self.CommentBoxID )
            department = self.GetString( self.DepartmentBoxID )

            pool = self.Pools[ self.GetLong( self.PoolBoxID ) ]
            secondaryPool = self.SecondaryPools[ self.GetLong( self.SecondaryPoolBoxID ) ]
            group = self.Groups[ self.GetLong( self.GroupBoxID ) ]
            priority = self.GetLong( self.PriorityBoxID )
            machineLimit = self.GetLong( self.MachineLimitBoxID )
            taskTimeout = self.GetLong( self.TaskTimeoutBoxID )
            autoTaskTimeout = self.GetBool( self.AutoTimeoutBoxID )
            concurrentTasks = self.GetLong( self.ConcurrentTasksBoxID )
            limitConcurrentTasks = self.GetBool( self.LimitConcurrentTasksBoxID )
            isBlacklist = self.GetBool( self.IsBlacklistBoxID )
            machineList = self.GetString( self.MachineListBoxID )
            limitGroups = self.GetString( self.LimitGroupsBoxID )
            dependencies = self.GetString( self.DependenciesBoxID )
            onComplete = self.OnComplete[ self.GetLong( self.OnCompleteBoxID ) ]
            submitSuspended = self.GetBool( self.SubmitSuspendedBoxID )

            frames = self.GetString( self.FramesBoxID )
            chunkSize = self.GetLong( self.ChunkSizeBoxID )
            threads = self.GetLong( self.ThreadsBoxID )
            build = self.Builds[ self.GetLong( self.BuildBoxID ) ]
            submitScene = self.GetBool( self.SubmitSceneBoxID )
            exportProject = self.GetBool( self.ExportProjectBoxID )
            localRendering = self.GetBool( self.LocalRenderingBoxID )

            draftTemplate = self.GetString( self.DraftTemplateBoxID )
            draftUser = self.GetString( self.DraftUserBoxID )
            draftEntity = self.GetString( self.DraftEntityBoxID )
            draftVersion = self.GetString( self.DraftVersionBoxID )
            draftExtraArgs = self.GetString( self.DraftExtraArgsBoxID )

            # Save sticky settings
            try:
                config = ConfigParser.ConfigParser()
                config.add_section( "Sticky" )

                config.set( "Sticky", "Department", department )
                config.set( "Sticky", "Pool", pool )
                config.set( "Sticky", "SecondaryPool", secondaryPool )
                config.set( "Sticky", "Group", group )
                config.set( "Sticky", "Priority", str(priority) )
                config.set( "Sticky", "MachineLimit", str(machineLimit) )
                config.set( "Sticky", "IsBlacklist", str(isBlacklist) )
                config.set( "Sticky", "MachineList", machineList )
                config.set( "Sticky", "LimitGroups", limitGroups )
                config.set( "Sticky", "SubmitSuspended", str(submitSuspended) )
                config.set( "Sticky", "ChunkSize", str(chunkSize) )
                config.set( "Sticky", "Threads", str(threads) )
                config.set( "Sticky", "Build", build )
                config.set( "Sticky", "SubmitScene", str(submitScene) )
                config.set( "Sticky", "ExportProject", str(exportProject) )
                config.set( "Sticky", "LocalRendering", str(localRendering) )

                config.set( "Sticky", "DraftTemplate", draftTemplate )
                config.set( "Sticky", "DraftUser", draftUser )
                config.set( "Sticky", "DraftEntity", draftEntity )
                config.set( "Sticky", "DraftVersion", draftVersion )
                config.set( "Sticky", "DraftExtraArgs", draftExtraArgs )

                fileHandle = open( self.ConfigFile, "w" )
                config.write( fileHandle )
                fileHandle.close()
            except:
                print( "Could not write sticky settings" )

            # Close the dialog if the Cancel button was clicked
            if id == self.SubmitButtonID:
                groupBatch = False
                if exportProject:
                    scene = documents.GetActiveDocument()
                    sceneName = scene.GetDocumentName()
                    originalSceneFilename = os.path.join( scene.GetDocumentPath(), sceneName )

                    print( "Exporting scene" )
                    c4d.StatusSetSpin()
                    c4d.CallCommand( 12255 )
                    c4d.StatusClear()

                    scene = documents.GetActiveDocument()
                    sceneName = scene.GetDocumentName()
                    newSceneFilename = os.path.join( scene.GetDocumentPath(), sceneName )

                    # If the scene file name hasn't changed, that means that they canceled the export dialog.
                    if newSceneFilename == originalSceneFilename:
                        return True

                    #continueOn = gui.QuestionDialog( "After the export, the scene file path is now:\n\n" + sceneFilename + "\n\nDo you wish to continue with the submission?" )
                    #if not continueOn:
                    #	return True

                    submitScene = False # can't submit scene if it's being exported

                scene = documents.GetActiveDocument()
                sceneName = scene.GetDocumentName()
                #sceneFilename = scene.GetDocumentPath() + "/" + sceneName
                sceneFilename = os.path.join( scene.GetDocumentPath(), sceneName )
                renderData = scene.GetActiveRenderData().GetData()

                saveOutput = renderData.GetBool( c4d.RDATA_SAVEIMAGE )
                outputPath = renderData.GetFilename( c4d.RDATA_PATH )
                outputFormat = renderData.GetLong( c4d.RDATA_FORMAT )
                outputName = renderData.GetLong( c4d.RDATA_NAMEFORMAT )

                saveMP = renderData.GetBool( c4d.RDATA_MULTIPASS_ENABLE ) and renderData.GetBool( c4d.RDATA_MULTIPASS_SAVEIMAGE )
                mpPath = renderData.GetFilename( c4d.RDATA_MULTIPASS_FILENAME )
                mpFormat = renderData.GetLong( c4d.RDATA_MULTIPASS_SAVEFORMAT )
                mpOneFile = renderData.GetBool( c4d.RDATA_MULTIPASS_SAVEONEFILE )

                width = renderData.GetLong( c4d.RDATA_XRES )
                height = renderData.GetLong( c4d.RDATA_YRES )

                print( "Creating submit info file" )

                # Create the submission info file
                jobInfoFile = self.DeadlineTemp + "/c4d_submit_info.job"
                fileHandle = open( jobInfoFile, "w" )
                fileHandle.write( "Plugin=Cinema4D\n" )
                fileHandle.write( "Name=%s\n" % jobName )
                fileHandle.write( "Comment=%s\n" % comment )
                fileHandle.write( "Department=%s\n" % department )
                fileHandle.write( "Group=%s\n" % group )
                fileHandle.write( "Pool=%s\n" % pool )
                if secondaryPool == " ": # If it's a space, then no secondary pool was selected.
                    fileHandle.write( "SecondaryPool=\n" )
                else:
                    fileHandle.write( "SecondaryPool=%s\n" % secondaryPool )
                fileHandle.write( "Priority=%s\n" % priority )
                fileHandle.write( "MachineLimit=%s\n" % machineLimit )
                fileHandle.write( "TaskTimeoutMinutes=%s\n" % taskTimeout )
                fileHandle.write( "EnableAutoTimeout=%s\n" % autoTaskTimeout )
                fileHandle.write( "ConcurrentTasks=%s\n" % concurrentTasks )
                fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % limitConcurrentTasks )
                fileHandle.write( "LimitGroups=%s\n" % limitGroups )
                fileHandle.write( "OnJobComplete=%s\n" % onComplete )
                fileHandle.write( "Frames=%s\n" % frames )
                fileHandle.write( "ChunkSize=%s\n" % chunkSize )
                if submitSuspended:
                    fileHandle.write( "InitialStatus=Suspended\n" )

                if isBlacklist:
                    fileHandle.write( "Blacklist=%s\n" % machineList )
                else:
                    fileHandle.write( "Whitelist=%s\n" % machineList )

                outputFilenameLine = False
                outputDirectoryLine = False
                if saveOutput and outputPath != "":
                    outputFilename = self.GetOutputFileName( outputPath, outputFormat, outputName )
                    if outputFilename != "":
                        fileHandle.write( "OutputFilename0=%s\n" % outputFilename )
                        outputFilenameLine = True
                    else:
                        fileHandle.write( "OutputDirectory0=%s\n" % os.path.dirname( outputPath ) )
                        outputDirectoryLine = True

                if saveMP and mpPath != "":
                    if mpOneFile:
                        mpFilename = self.GetOutputFileName( mpPath, mpFormat, outputName )
                        if mpFilename != "":
                            if not outputFilenameLine and not outputDirectoryLine:
                                fileHandle.write( "OutputFilename0=%s\n" % mpFilename )
                            elif outputFilenameLine:
                                fileHandle.write( "OutputFilename1=%s\n" % mpFilename )
                        else:
                            if not outputFilenameLine and not outputDirectoryLine:
                                fileHandle.write( "OutputDirectory0=%s\n" % os.path.dirname( mpPath ) )
                            elif outputDirectoryLine:
                                fileHandle.write( "OutputDirectory1=%s\n" % os.path.dirname( mpPath ) )
                    else:
                        mPass = scene.GetActiveRenderData().GetFirstMultipass()
                        #"Post Effects":"",  not supported: NO files were made throughout my  testing so no idea what this should be
                        mPassTypePrefix ={
                                            "Ambient":"_ambient",
                                            "Diffuse":"_diffuse",
                                            "Specular":"_specular",
                                            "Shadow":"_shadow",
                                            "Reflection":"_refl",
                                            "Refraction":"_refr",
                                            "Ambient Occlusion":"_ao",
                                            "Global Illumination":"_gi",
                                            "Caustics":"_caustics",
                                            "Atmosphere":"_atmos",
                                            "Atmosphere (Multiply)":"_atmosmul",
                                            "Material Color":"_matcolor",
                                            "Material Diffusion":"_matdif",
                                            "Material Luminance":"_matlum",
                                            "Material Transparency":"mat_trans",
                                            "Material Reflection":"_matrefl",
                                            "Material Environment":"_matenv",
                                            "Material Specular":"_matspec",
                                            "Material Specular Color":"_matspeccol",
                                            "Material Normal":"_normal",
                                            "Material UVW":"_uv",
                                            "RGBA Image":"_rgb",
                                            "Motion Vector":"_motion",
                                            "Illumination":"_illum",
                                            "Depth":"_depth"
                                        }
                        count = 1
                        if not outputFilenameLine and not outputDirectoryLine:
                            count = 0
                        while mPass is not None:
                            if not mPass.GetBit(c4d.BIT_VPDISABLED):
                                try:
                                    print mpPath+str(mPassTypePrefix[mPass.GetTypeName()])

                                    mpFilename = self.GetOutputFileName( mpPath+str(mPassTypePrefix[mPass.GetTypeName()]), mpFormat, outputName )
                                    fileHandle.write( "OutputFilename%i=%s\n" % (count, mpFilename) )
                                    count += 1
                                except:
                                    pass
                            mPass=mPass.GetNext()


                #Shotgun/Draft
                extraKVPIndex = 0

                if self.GetBool( self.UseIntegrationBoxID ):
                    if self.integrationType == 0:
                        fileHandle.write( "ExtraInfo0=%s\n" % self.ShotgunJobSettings.get('TaskName', "") )
                        fileHandle.write( "ExtraInfo1=%s\n" % self.ShotgunJobSettings.get('ProjectName', "") )
                        fileHandle.write( "ExtraInfo2=%s\n" % self.ShotgunJobSettings.get('EntityName', "") )
                        fileHandle.write( "ExtraInfo3=%s\n" % self.ShotgunJobSettings.get('VersionName', "") )
                        fileHandle.write( "ExtraInfo4=%s\n" % self.ShotgunJobSettings.get('Description', "") )
                        fileHandle.write( "ExtraInfo5=%s\n" % self.ShotgunJobSettings.get('UserName', "") )

                        for key in self.ShotgunJobSettings:
                            if key != 'DraftTemplate':
                                fileHandle.write( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, self.ShotgunJobSettings[key]) )
                                extraKVPIndex += 1
                        if self.GetBool(self.UploadMovieBoxID):
                            fileHandle.write( "ExtraInfoKeyValue%s=Draft_CreateSGMovie=True\n" % (extraKVPIndex) )
                            extraKVPIndex += 1
                            groupBatch = True
                        if self.GetBool(self.UploadFilmStripBoxID):
                            fileHandle.write( "ExtraInfoKeyValue%s=Draft_CreateSGFilmstrip=True\n" % (extraKVPIndex) )
                            extraKVPIndex += 1
                            groupBatch = True
                    else:
                        fileHandle.write( "ExtraInfo0=%s\n" % self.FTrackJobSettings.get('FT_TaskName', "") )
                        fileHandle.write( "ExtraInfo1=%s\n" % self.FTrackJobSettings.get('FT_ProjectName', "") )
                        fileHandle.write( "ExtraInfo2=%s\n" % self.FTrackJobSettings.get('FT_AssetName', "") )
                        #fileHandle.write( "ExtraInfo3=%s\n" % self.FTrackJobSettings.get('VersionName', "") )
                        fileHandle.write( "ExtraInfo4=%s\n" % self.FTrackJobSettings.get('FT_Description', "") )
                        fileHandle.write( "ExtraInfo5=%s\n" % self.FTrackJobSettings.get('FT_Username', "") )
                        for key in self.FTrackJobSettings:
                            fileHandle.write( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, self.FTrackJobSettings[key]) )
                            extraKVPIndex += 1
                if self.GetBool( self.UseDraftBoxID ):
                    fileHandle.write( "ExtraInfoKeyValue%d=DraftTemplate=%s\n" % (extraKVPIndex, draftTemplate) )
                    extraKVPIndex += 1
                    fileHandle.write( "ExtraInfoKeyValue%d=DraftUsername=%s\n" % (extraKVPIndex, draftUser) )
                    extraKVPIndex += 1
                    fileHandle.write( "ExtraInfoKeyValue%d=DraftEntity=%s\n" % (extraKVPIndex, draftEntity) )
                    extraKVPIndex += 1
                    fileHandle.write( "ExtraInfoKeyValue%d=DraftVersion=%s\n" % (extraKVPIndex, draftVersion) )
                    extraKVPIndex += 1
                    fileHandle.write( "ExtraInfoKeyValue%d=DraftUploadToShotgun=%s\n" % (extraKVPIndex, str(self.GetBool( self.UploadDraftToShotgunBoxID ) and self.GetBool( self.UseIntegrationBoxID ) and self.integrationType == 0) ) )
                    extraKVPIndex += 1
                    fileHandle.write( "ExtraInfoKeyValue%d=DraftExtraArgs=%s\n" % (extraKVPIndex, draftExtraArgs ) )
                    extraKVPIndex += 1
                    groupBatch = True

                if groupBatch:
                    fileHandle.write( "BatchName=%s\n" % (jobName ) )

                fileHandle.close()

                print( "Creating plugin info file" )

                # Create the plugin info file
                pluginInfoFile = self.DeadlineTemp + "/c4d_plugin_info.job"
                fileHandle = open( pluginInfoFile, "w" )
                if not submitScene:
                    fileHandle.write( "SceneFile=%s\n" % sceneFilename )
                fileHandle.write( "Version=%s\n" % (c4d.GetC4DVersion() / 1000) )
                fileHandle.write( "Build=%s\n" % build )
                fileHandle.write( "Threads=%s\n" % threads )
                fileHandle.write( "Width=%s\n" % width )
                fileHandle.write( "Height=%s\n" % height )
                fileHandle.write( "LocalRendering=%s\n" % localRendering )

                if saveOutput and outputPath != "":
                    head, tail = os.path.split( outputPath )
                    fileHandle.write( "FilePath=%s\n" % head )
                    fileHandle.write( "FilePrefix=%s\n" % tail )

                if saveMP and mpPath != "":
                    head, tail = os.path.split( mpPath )
                    fileHandle.write( "MultiFilePath=%s\n" % head )
                    fileHandle.write( "MultiFilePrefix=%s\n" % tail )

                fileHandle.close()

                print( "Submitting job" )
                c4d.StatusSetSpin()

                # Submit the job to Deadline
                args = []
                args.append( jobInfoFile )
                args.append( pluginInfoFile )
                if submitScene:
                    args.append( sceneFilename )

                results = ""
                try:
                    results = CallDeadlineCommand( args )
                except:
                    results = "An error occurred while submitting the job to Deadline."

                c4d.StatusClear()

                gui.MessageDialog( results )

            self.Close()

        return True

    def updateDisplay(self):
        displayText = ""
        if self.integrationType == 0:
            if 'UserName' in self.ShotgunJobSettings:
                displayText += "User Name: %s\n" % self.ShotgunJobSettings[ 'UserName' ]
            if 'TaskName' in self.ShotgunJobSettings:
                displayText += "Task Name: %s\n" % self.ShotgunJobSettings[ 'TaskName' ]
            if 'ProjectName' in self.ShotgunJobSettings:
                displayText += "Project Name: %s\n" % self.ShotgunJobSettings[ 'ProjectName' ]
            if 'EntityName' in self.ShotgunJobSettings:
                displayText += "Entity Name: %s\n" % self.ShotgunJobSettings[ 'EntityName' ]
            if 'EntityType' in self.ShotgunJobSettings:
                displayText += "Entity Type: %s\n" % self.ShotgunJobSettings[ 'EntityType' ]
            if 'DraftTemplate' in self.ShotgunJobSettings:
                displayText += "Draft Template: %s\n" % self.ShotgunJobSettings[ 'DraftTemplate' ]

            self.SetString( self.IntegrationInfoBoxID, displayText )
            self.SetString( self.IntegrationVersionBoxID, self.ShotgunJobSettings.get( 'VersionName', "" ) )
            self.SetString( self.IntegrationDescriptionBoxID, self.ShotgunJobSettings.get( 'Description', "" ) )
        else:
            if 'UserName' in self.FTrackJobSettings:
                displayText += "User Name: %s\n" % self.FTrackJobSettings[ 'FT_Username' ]
            if 'TaskName' in self.FTrackJobSettings:
                displayText += "Task Name: %s\n" % self.FTrackJobSettings[ 'FT_TaskName' ]
            if 'ProjectName' in self.FTrackJobSettings:
                displayText += "Project Name: %s\n" % self.FTrackJobSettings[ 'FT_ProjectName' ]

            self.SetString( self.IntegrationInfoBoxID, displayText )
            self.SetString( self.IntegrationVersionBoxID, self.FTrackJobSettings.get( 'FT_AssetName', "" ) )
            self.SetString( self.IntegrationDescriptionBoxID, self.FTrackJobSettings.get( 'FT_Description', "" ) )

        if len(displayText)>0:
            self.Enable( self.UseIntegrationBoxID, True )
            self.SetBool( self.UseIntegrationBoxID, True )
            self.Command( self.UseDraftBoxID, None )
        else:
            self.Enable( self.UseIntegrationBoxID, False )
            self.SetBool( self.UseIntegrationBoxID, False )

    def GetOutputFileName( self, outputPath, outputFormat, outputName ):
        if outputPath == "":
            return ""

        # C4D always throws away the last extension in the file name, so we'll do that too.
        outputPrefix, tempOutputExtension = os.path.splitext( outputPath )
        outputExtension = self.GetExtensionFromFormat( outputFormat )

        # If the name requires an extension, and an extension could not be determined,
        # we simply return an empty output filename because we don't have all the info.
        if outputName == 0 or outputName == 3 or outputName == 6:
            if outputExtension == "":
                return ""

        # If the output ends with a digit, and the output name scheme doesn't start with a '.', then C4D automatically appends an underscore.
        if len( outputPrefix ) > 0 and outputPrefix[ len( outputPrefix ) - 1 ].isdigit() and outputName not in (2, 5, 6):
            outputPrefix = outputPrefix + "_"

        # Format the output filename based on the selected output name.
        if outputName == 0:
            return outputPrefix + "####." + outputExtension
        elif outputName == 1:
            return outputPrefix + "####"
        elif outputName == 2:
            return outputPrefix + ".####"
        elif outputName == 3:
            return outputPrefix + "###." + outputExtension
        elif outputName == 4:
            return outputPrefix + "###"
        elif outputName == 5:
            return outputPrefix + ".###"
        elif outputName == 6:
            return outputPrefix + ".####." + outputExtension

        return ""

    def GetExtensionFromFormat( self, outputFormat ):
        extension = ""

        # These values are pulled from coffeesymbols.h, which can be found in
        # the 'resource' folder in the C4D install directory.
        if outputFormat == 1102: # BMP
            extension = "bmp"
        elif outputFormat == 1109: # B3D
            extension = "b3d"
        elif outputFormat == 1023737: # DPX
            extension = "dpx"
        elif outputFormat == 1103: # IFF
            extension = "iff"
        elif outputFormat == 1104: # JPG
            extension = "jpg"
        elif outputFormat == 1016606: # openEXR
            extension = "exr"
        elif outputFormat == 1106: # PSD
            extension = "psd"
        elif outputFormat == 1111: # PSB
            extension = "psb"
        elif outputFormat == 1105: # PICT
            extension = "pct"
        elif outputFormat == 1023671: # PNG
            extension = "png"
        elif outputFormat == 1001379: # HDR
            extension = "hdr"
        elif outputFormat == 1107: # RLA
            extension = "rla"
        elif outputFormat == 1108: # RPF
            extension = "rpf"
        elif outputFormat == 1101: # TGA
            extension = "tga"
        elif outputFormat == 1110: # TIF (B3D Layers)
            extension = "tif"
        elif outputFormat == 1100: # TIF (PSD Layers)
            extension = "tif"
        elif outputFormat == 1024463: # IES
            extension = "ies"
        elif outputFormat == 1122: # AVI
            extension = "avi"
        elif outputFormat == 1125: # QT
            extension = "mov"
        elif outputFormat == 1150: # QT (Panarama)
            extension = "mov"
        elif outputFormat == 1151: # QT (object)
            extension = "mov"
        elif outputFormat == 1112363110: # QT (bmp)
            extension = "bmp"
        elif outputFormat == 1903454566: # QT (image)
            extension = "qtif"
        elif outputFormat == 1785737760: # QT (jp2)
            extension = "jp2"
        elif outputFormat == 1246774599: # QT (jpg)
            extension = "jpg"
        elif outputFormat == 943870035: # QT (photoshop)
            extension = "psd"
        elif outputFormat == 1346978644: # QT (pict)
            extension = "pct"
        elif outputFormat == 1347307366: # QT (png)
            extension = "png"
        elif outputFormat == 777209673: # QT (sgi)
            extension = "sgi"
        elif outputFormat == 1414088262: # QT (tiff)
            extension = "tif"

        return extension

## Class to create the submission menu item in C4D.
class SubmitC4DtoDeadlineMenu (plugins.CommandData):
    ScriptPath = ""

    def __init__( self, path ):
        self.ScriptPath = path

    def Execute( self, doc ):
        if SaveScene():
            dialog = SubmitC4DToDeadlineDialog()
            dialog.Open( c4d.DLG_TYPE_MODAL )
        return True

    def GetScriptName( self ):
        return "Submit To Deadline"

def CallDeadlineCommand( arguments, hideWindow=True ):
    # On OSX, we look for the DEADLINE_PATH file. On other platforms, we use the environment variable.
    if os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f: deadlineBin = f.read().strip()
        deadlineCommand = deadlineBin + "/deadlinecommand"
    else:
        deadlineBin = os.environ['DEADLINE_PATH']
        if os.name == 'nt':
            deadlineCommand = deadlineBin + "\\deadlinecommand.exe"
        else:
            deadlineCommand = deadlineBin + "/deadlinecommand"

    startupinfo = None
    if hideWindow and os.name == 'nt' and hasattr( subprocess, 'STARTF_USESHOWWINDOW' ): #not all python versions have this        startupinfo = subprocess.STARTUPINFO()
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])

    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        environment['PATH'] = str(deadlineBin + os.pathsep + os.environ['PATH'])

    arguments.insert( 0, deadlineCommand)

    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, cwd=deadlineBin, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment)
    proc.stdin.close()
    proc.stderr.close()

    output = proc.stdout.read()

    return output

## Global function to save the scene. Returns True if the scene has been saved and it's OK to continue.
def SaveScene():
    scene = documents.GetActiveDocument()

    # Save the scene if required.
    if scene.GetDocumentPath() == "" or scene.GetChanged():
        print( "Scene file needs to be saved" )
        c4d.CallCommand( 12098 ) # this is the ID for the Save command (from Command Manager)
        if scene.GetDocumentPath() == "":
            gui.MessageDialog( "The scene must be saved before it can be submitted to Deadline" )
            return False

    return True

## Global function used to register our submission script as a plugin.
def main( path ):
    pluginID = 1025665
    plugins.RegisterCommandPlugin( pluginID, "Submit To Deadline", 0, None, "Submit a Cinema 4D job to Deadline.", SubmitC4DtoDeadlineMenu( path ) )

## For debugging.
if __name__=='__main__':
    if SaveScene():
        dialog = SubmitC4DToDeadlineDialog()
        dialog.Open( c4d.DLG_TYPE_MODAL )
