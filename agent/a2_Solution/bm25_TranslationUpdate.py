import sys
sys.path.append("/yaas")

from agent.a2_Solution.a24_Translation.a241_TranslationUpdate import TranslationProcessUpdate

#####################################
#####################################
##### SolutionTranslationUpdate #####
#####################################
#####################################

### 솔루션에 번역문 업데이트 ###
def SolutionTranslationUpdate(ProjectName, email, MainLang, Translation, BookGenre, Tone, BodyLength, Editing, Refinement, KinfolkStyleRefinement, EditMode, MessagesReview):
    
    ######################
    ### 01_Translation ###
    ######################
    TranslationProcessUpdate(ProjectName, email, MainLang, Translation, BookGenre, Tone, BodyLength, Editing, Refinement, KinfolkStyleRefinement, EditMode, MessagesReview = MessagesReview)