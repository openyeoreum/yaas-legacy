import sys
sys.path.append("/yaas")

from agent.a2_Solution.a23_Script.a232_BookScriptGen.a2321_BookScriptGenUpdate import BookScriptGenProcessUpdate

################################
################################
##### SolutionScriptUpdate #####
################################
################################

### 솔루션에 북스크립트 업데이트 ###
def SolutionScriptUpdate(ProjectName, email, Script, Intention, MessagesReview):
    
    #######################
    ### 01_ScriptUpload ###
    #######################
    
    if Script == "" or Script == "None":
        # ScriptUpload(ProjectName, email)
        pass
    
    ########################
    ### 02_BookScriptGen ###
    ########################
        
    elif Script == "BookScript":
        BookScriptGenProcessUpdate(ProjectName, email, Intention, MessagesReview = MessagesReview)

    ###########################
    ### 03_InstantScriptGen ###
    ###########################

    else:
        # InstantScriptGenProcessUpdate(ProjectName, email, Script)
        pass