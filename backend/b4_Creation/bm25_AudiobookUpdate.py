import sys
sys.path.append("/yaas")

from backend.b4_Creation.b42_Generator.b422_VoiceLayerGenerator import VoiceLayerGenerator

###########################
###########################
##### AudiobookUpdate #####
###########################
###########################

### DAW에 오디오북 제작 및 업데이트 ###
def CreationAudioBookUpdate(projectName, email, voiceDataSet, mode = "Manual"):
    
    #####################
    ### 01_VoiceLayer ###
    #####################
    VoiceLayerGenerator(projectName, email, voiceDataSet, Mode = mode)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '노인을위한나라는있다' # '데미안', '빨간머리앤', '웹3.0메타버스', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법'
    voiceDataSet = "TypeCastVoiceDataSet"
    #########################################################################
    
    ### Step6 : 크리에이션이 오디오북 제작 ###
    CreationAudioBookUpdate(projectName, email, voiceDataSet)