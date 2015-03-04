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
    if path != "":
        path += "/submission/Cinema4D/Main"
        path = path.replace( "\\", "/" )

        # Add the path to the system path
        if path not in sys.path:
            print( "Appending \"" + path + "\" to system path to import SubmitC4DToDeadline module" )
            sys.path.append( path )
        else:
            print( "\"%s\" is already in the system path" % path )
        
        # Import the script and call the main() function
        try:
            import SubmitC4DToDeadline
            SubmitC4DToDeadline.main( path )
        except:
            print traceback.format_exc()
            print( "The SubmitC4DToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )
    else:
        print( "Could not find Repository root. Make sure the Deadline client applications are installed on this machine, and that the Monitor can connect to the Repository." )
        
if __name__=='__main__':
    main()
