import sys
sys.path.append("/yaas")

from agent.a5_Solution.a53_Translation.a531_TranslationUpdate import TranslationProcessUpdate

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