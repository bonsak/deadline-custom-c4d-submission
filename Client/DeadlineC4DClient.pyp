import os, sys, subprocess, traceback

import c4d
from c4d import gui

def GetRepositoryRoot():
    # On OSX, we look for the DEADLINE_PATH file. On other platforms, we use the environment variable.
    if os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f: deadlineBin = f.read().strip()
        deadlineCommand = deadlineBin + "/deadlinecommand"
    else:
        try:
            deadlineBin = os.environ['DEADLINE_PATH']
        except KeyError:
            return ""

        if os.name == 'nt':
            deadlineCommand = deadlineBin + "\\deadlinecommand.exe"
        else:
            deadlineCommand = deadlineBin + "/deadlinecommand"

    startupinfo = None
    if os.name == 'nt' and hasattr( subprocess, 'STARTF_USESHOWWINDOW' ): #not all python versions have this
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen([deadlineCommand, "-root"], cwd=deadlineBin, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
    proc.stdin.close()
    proc.stderr.close()

    root = proc.stdout.read()
    root = root.replace("\n","").replace("\r","")
    return root

def main():
    # Get the repository root
    path = GetRepositoryRoot()

    # Get the current c4d version
    c4dversion = c4d.GetC4DVersion()

    if path != "":
        path += "/submission/Cinema4D/Main"
        path = path.replace( "\\", "/" )

        # Add the path to the system path
        if path not in sys.path:
            print( "Appending \"" + path + "\" to system path to import SubmitC4DToDeadline module" )
            sys.path.append( path )
        else:
            print( "\"%s\" is already in the system path" % path )

        # Check if version is higher than a certain number and start the corresponding main plugin
        if c4dversion > 16040:
            try:
                import SubmitC4DToDeadline17
                SubmitC4DToDeadline17.main( path )
            except:
                print traceback.format_exc()
                print( "The SubmitC4DToDeadline17.py script could not be found in the Deadline Repository." )
        else:
            try:
                import SubmitC4DToDeadline
                SubmitC4DToDeadline.main( path )
            except:
                print traceback.format_exc()
                print( "The SubmitC4DToDeadline.py script could not be found in the Deadline Repository." )

    else:
        print( "Could not find Repository root." )

if __name__=='__main__':
    main()
