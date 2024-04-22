import sys
sys.path.append("/yaas")

from backend.b4_Creation.b42_Generator.b422_VoiceLayerGenerator import VoiceLayerGenerator
from backend.b4_Creation.b42_Generator.b422_VoiceLayerSplitGenerator import VoiceLayerUpdate
from backend.b4_Creation.b41_Selector.b411_MusicLayerSelector import MusicLayerUpdate

###########################
###########################
##### AudiobookUpdate #####
###########################
###########################

### Creation에 오디오북 제작 및 업데이트 ###
def CreationAudioBookUpdate(projectName, email, voiceDataSet, mainLang, intro, mode = "Manual", macro = "Manual", account = "None", voiceFileGen = "on", split = "Manual", messagesReview = "off"):
    
    #####################
    ### 01_VoiceLayer ###
    #####################
    if split == "Manual":
        VoiceLayerGenerator(projectName, email, voiceDataSet, MainLang = mainLang, Mode = mode, Macro = macro, Account = account, MessagesReview = messagesReview)
        MusicLayerUpdate(projectName, email, MainLang = mainLang, Intro = intro)
    else:
        VoiceLayerUpdate(projectName, email, voiceDataSet, MainLang = mainLang, Mode = mode, Macro = macro, Account = account, VoiceFileGen = voiceFileGen, MessagesReview = messagesReview)
        MusicLayerUpdate(projectName, email, MainLang = mainLang, Intro = intro)
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '노인을위한나라는있다' # '데미안', '빨간머리앤', '웹3.0메타버스', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법'
    voiceDataSet = "TypeCastVoiceDataSet"
    mainLang = "Ko"
    intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    voiceFileGen = "off" # 'on', 'off'
    macro = "Manual"
    account = "None"
    split = "Manual"
    messagesReview = "off"
    #########################################################################
    
    ### Step6 : 크리에이션이 오디오북 제작 ###
    CreationAudioBookUpdate(projectName, email, voiceDataSet, mainLang, macro = macro, account = account, voiceFileGen = voiceFileGen, split = split, messagesReview = messagesReview)