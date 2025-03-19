import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_Translation.b241_TranslationUpdate import TranslationProcessUpdate

#####################################
#####################################
##### SolutionTranslationUpdate #####
#####################################
#####################################

### 솔루션에 번역문 업데이트 ###
def SolutionTranslationUpdate(ProjectName, email, MainLang, Translation, BookGenre, Tone, BodyLength, TranslationQuality, EditMode, MessagesReview):
    
    ######################
    ### 01_Translation ###
    ######################
    TranslationProcessUpdate(ProjectName, email, MainLang, Translation, BookGenre, Tone, BodyLength, TranslationQuality, EditMode, MessagesReview = MessagesReview)