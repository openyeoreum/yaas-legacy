import sys
sys.path.append("/yaas")

from backend.b4_Creation.b42_Generator.b422_VoiceLayerSplitGenerator import VoiceLayerUpdate
from backend.b4_Creation.b41_Selector.b411_MusicLayerSelector import MusicLayerUpdate

###########################
###########################
##### AudiobookUpdate #####
###########################
###########################

### Creation에 오디오북 제작 및 업데이트 ###
def CreationAudioBookUpdate(projectName, email, narrator, cloneVoiceName, readingStyle, voiceReverbe, mainLang, intro, audiobookSplitting = "Auto", endMusicVolume = -10, mode = "Manual", macro = "Manual", bracket = "Manual", volumeEqual = "Mixing", account = "None", voiceEnhance = "off", voiceFileGen = "on", bitrate = "320k", messagesReview = "off"):
    
    #####################
    ### 01_VoiceLayer ###
    #####################
    VoiceLayerUpdate(projectName, email, Narrator = narrator, CloneVoiceName = cloneVoiceName, ReadingStyle = readingStyle, VoiceReverbe = voiceReverbe, MainLang = mainLang, Mode = mode, Macro = macro, Bracket = bracket, VolumeEqual = volumeEqual, Account = account, VoiceEnhance = voiceEnhance, VoiceFileGen = voiceFileGen, MessagesReview = messagesReview)
    MusicLayerUpdate(projectName, email, CloneVoiceName = cloneVoiceName, MainLang = mainLang, Intro = intro, AudiobookSplitting = audiobookSplitting, EndMusicVolume = endMusicVolume, VolumeEqual = volumeEqual, Bitrate = bitrate)
    
if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = '노인을위한나라는있다' # '데미안', '빨간머리앤', '웹3.0메타버스', '나는선비로소이다', '나는노비로소이다', '카이스트명상수업', '우리는행복을진단한다', '웹3.0메타버스', '살아서천국극락낙원에가는방법'
    narrator = "VoiceActor" # 'VoiceActor', 'VoiceClone'
    readingStyle = "AllCharacters"
    cloneVoiceName = "저자명"
    voiceEnhance = "off" # 'on', 'off'
    voiceReverbe = "on" # 'on', 'off' : on 은 인덱스와 대화문에 리버브 적용, off 는 리버브 미적용
    mainLang = "Ko"
    intro = "off" # Intro = ['한국출판문화산업진흥원' ...]
    audiobookSplitting = "Auto" # 'Auto', 'Manual' : Auto 는 오디오북 자동 분할, Manual 은 오디오북 수동 분할
    endMusicVolume = -10
    voiceFileGen = "off" # 'on', 'off'
    macro = "Manual"
    bracket = "Manual"
    volumeEqual = "Mixing"
    account = "None"
    messagesReview = "off"
    #########################################################################
    
    ### Step6 : 크리에이션이 오디오북 제작 ###
    CreationAudioBookUpdate(projectName, email, narrator, cloneVoiceName, readingStyle, voiceReverbe, mainLang, macro = macro, bracket = bracket, volumeEqual = volumeEqual, account = account, voiceEnhance = voiceEnhance, voiceFileGen = voiceFileGen, messagesReview = messagesReview)