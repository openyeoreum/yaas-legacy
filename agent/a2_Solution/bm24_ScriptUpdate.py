import sys
sys.path.append("/yaas")

from agent.a2_Solution.a23_Script.a232_BookScriptGen.a2321_BookScriptGenUpdate import BookScriptGenProcessUpdate
from agent.a2_Solution.a23_Script.a233_ScriptSegmentation.a2331_ScriptSegmentation import ScriptSegmentationProcessUpdate

################################
################################
##### SolutionScriptUpdate #####
################################
################################

### 솔루션에 북스크립트 업데이트 ###
def SolutionScriptUpdate(ProjectName, email, Script, Intention, NextSolution, AutoTemplate, MessagesReview):

    ###########################
    ### 01_InstantScriptGen ###
    ###########################

    if not Script in ["", "None", "BookScript", "Upload"]:
        # InstantScriptGenProcessUpdate(ProjectName, email, Script)
        pass

    ########################
    ### 02_BookScriptGen ###
    ########################
        
    elif Script == "BookScript":
        BookScriptGenProcessUpdate(ProjectName, email, Intention, MessagesReview = MessagesReview)

    #############################
    ### 03_ScriptSegmentation ###
    #############################
    
    elif Script == "Upload":
        ScriptSegmentationProcessUpdate(ProjectName, email, NextSolution, AutoTemplate, MessagesReview = MessagesReview)