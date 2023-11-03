import os
import sys
import json
sys.path.append("/yaas")

from backend.b1_Api.b14_Models import Prompt
from backend.b1_Api.b13_Database import get_db

def GetPromptDataPath(relativePath='../../b5_Database/b54_PromptData/'):
    CurrentDir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CurrentDir, relativePath)

def LoadJsonFrame(filepath):
    with open(filepath, 'r') as file:
        DataFrame = json.load(file)
    return DataFrame

def AddPromptToDB():
    with get_db() as db:
        
        # JSON 데이터 불러오기
        PromptDataPath = GetPromptDataPath()
        
        indexDefinePreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-01_IndexDefinePreprocess.json")
        indexDefineDivisionPreprocess = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-02_IndexDefineDivisionPreprocess.json")
        indexDefine = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-03_IndexDefine.json")
        captionDefine = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-04_CaptionDefine.json")
        bodySummary = LoadJsonFrame(PromptDataPath + "/b541_ScriptPrompt/b541-05_BodySummary.json")
        bodyCharacterDefine = LoadJsonFrame(PromptDataPath + "/b542_BodyDefinePrompt/b542-01_BodyCharacterDefine.json")
        bodyCharacterAnnotation = LoadJsonFrame(PromptDataPath + "/b542_BodyDefinePrompt/b542-02_BodyCharacterAnnotation.json")
        # bodyContextDefine = LoadJsonFrame(PromptDataPath + "/b542_BodyDefinePrompt/b542-03_BodyContextDefine.json")
        # splitedBodyCharacterDefine = LoadJsonFrame(PromptDataPath + "/b543_SplitedBodyDefinePrompt/b543-01_SplitedBodyCharacterDefine.json")
        # splitedBodyContextDefine = LoadJsonFrame(PromptDataPath + "/b543_SplitedBodyDefinePrompt/b543-02_SplitedBodyContextDefine.json")
        # phargraphTransitionDefine = LoadJsonFrame(PromptDataPath + "/b543_SplitedBodyDefinePrompt/b543-03_PhargraphTransitionDefine.json")
        # characterTagging = LoadJsonFrame(PromptDataPath + "/b544_TaggingPrompt/b544-01_CharacterTagging.json")
        # musicTagging = LoadJsonFrame(PromptDataPath + "/b544_TaggingPrompt/b544-02_MusicTagging.json")
        # soundTagging = LoadJsonFrame(PromptDataPath + "/b544_TaggingPrompt/b544-03_SoundTagging.json")
        # characterMatching = LoadJsonFrame(PromptDataPath + "/b545_MatchingPrompt/b545-01_CharacterMatching.json")
        # soundMatching = LoadJsonFrame(PromptDataPath + "/b545_MatchingPrompt/b545-02_SoundMatching.json")
        # sFXMatching = LoadJsonFrame(PromptDataPath + "/b545_MatchingPrompt/b545-03_SFXMatching.json")
        # characterMultiQuery = LoadJsonFrame(PromptDataPath + "/b546_MultiQueryPrompt/b546-01_CharacterMultiQuery.json")
        # soundMultiQuery = LoadJsonFrame(PromptDataPath + "/b546_MultiQueryPrompt/b546-02_SoundMultiQuery.json")
        # sFXMultiQuery = LoadJsonFrame(PromptDataPath + "/b546_MultiQueryPrompt/b546-03_SFXMultiQuery.json")
        # translationKo = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-01_TranslationKo.json")
        # translationEn = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-02_TranslationEn.json")
        # translationJa = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-03_TranslationJa.json")
        # translationZh = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-04_TranslationZh.json")
        # translationEs = LoadJsonFrame(PromptDataPath + "/b547_TranslationPrompt/b547-05_TranslationEs.json")
        # correctionKo = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-01_CorrectionKo.json")
        # correctionEn = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-02_CorrectionEn.json")
        # correctionJa = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-03_CorrectionJa.json")
        # correctionZh = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-04_CorrectionZh.json")
        # correctionEs = LoadJsonFrame(PromptDataPath + "/b548_CorrectionPrompt/b548-05_CorrectionEs.json")
        # voiceGenerationKo = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-01_VoiceGenerationKo.json")
        # voiceGenerationEn = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-02_VoiceGenerationEn.json")
        # voiceGenerationJa = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-03_VoiceGenerationJa.json")
        # voiceGenerationZh = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-04_VoiceGenerationZh.json")
        # voiceGenerationEs = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-05_VoiceGenerationEs.json")
        # musicSelection = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-06_MusicSelection.json")
        # soundSelection = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-07_SoundSelection.json")
        # sFXSelectionKo = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-08_SFXSelectionKo.json")
        # sFXSelectionEn = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-09_SFXSelectionEn.json")
        # sFXSelectionJa = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-10_SFXSelectionJa.json")
        # sFXSelectionZh = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-11_SFXSelectionZh.json")
        # sFXSelectionEs = LoadJsonFrame(PromptDataPath + "/b549_Selection-GenerationPrompt/b549-12_SFXSelectionEs.json")
        # mixingMasteringKo = LoadJsonFrame(PromptDataPath + "/b5410_Mixing-MasteringPrompt/b5410-01_Mixing-MasteringKo.json")
        # mixingMasteringEn = LoadJsonFrame(PromptDataPath + "/b5410_Mixing-MasteringPrompt/b5410-02_Mixing-MasteringEn.json")
        # mixingMasteringJa = LoadJsonFrame(PromptDataPath + "/b5410_Mixing-MasteringPrompt/b5410-03_Mixing-MasteringJa.json")
        # mixingMasteringZh = LoadJsonFrame(PromptDataPath + "/b5410_Mixing-MasteringPrompt/b5410-04_Mixing-MasteringZh.json")
        # mixingMasteringEs = LoadJsonFrame(PromptDataPath + "/b5410_Mixing-MasteringPrompt/b5410-05_Mixing-MasteringEs.json")

        # DB Commit
        prompt = Prompt(
            IndexDefinePreprocess = indexDefinePreprocess,
            IndexDefineDivisionPreprocess = indexDefineDivisionPreprocess,
            IndexDefine = indexDefine,
            CaptionDefine = captionDefine,
            BodySummary = bodySummary,
            BodyCharacterDefine = bodyCharacterDefine,
            BodyCharacterAnnotation = bodyCharacterAnnotation,
            # BodyContextDefine = bodyContextDefine,
            # SplitedBodyCharacterDefine = splitedBodyCharacterDefine,
            # SplitedBodyContextDefine = splitedBodyContextDefine,
            # PhargraphTransitionDefine = phargraphTransitionDefine,
            # CharacterTagging = characterTagging,
            # MusicTagging = musicTagging,
            # SoundTagging = soundTagging,
            # CharacterMatching = characterMatching,
            # SoundMatching = soundMatching,
            # SFXMatching = sFXMatching,
            # CharacterMultiQuery = characterMultiQuery,
            # SoundMultiQuery = soundMultiQuery,
            # SFXMultiQuery = sFXMultiQuery,
            # TranslationKo = translationKo,
            # TranslationEn = translationEn,
            # TranslationJa = translationJa,
            # TranslationZh = translationZh,
            # TranslationEs = translationEs,
            # CorrectionKo = correctionKo,
            # CorrectionEn = correctionEn,
            # CorrectionJa = correctionJa,
            # CorrectionZh = correctionZh,
            # CorrectionEs = correctionEs,
            # VoiceGenerationKo = voiceGenerationKo,
            # VoiceGenerationEn = voiceGenerationEn,
            # VoiceGenerationJa = voiceGenerationJa,
            # VoiceGenerationZh = voiceGenerationZh,
            # VoiceGenerationEs = voiceGenerationEs,
            # MusicSelection = musicSelection,
            # SoundSelection = soundSelection,
            # SFXSelectionKo = sFXSelectionKo,
            # SFXSelectionEn = sFXSelectionEn,
            # SFXSelectionJa = sFXSelectionJa,
            # SFXSelectionZh = sFXSelectionZh,
            # SFXSelectionEs = sFXSelectionEs,
            # MixingMasteringKo = mixingMasteringKo,
            # MixingMasteringEn = mixingMasteringEn,
            # MixingMasteringJa = mixingMasteringJa,
            # MixingMasteringZh = mixingMasteringZh,
            # MixingMasteringEs = mixingMasteringEs
            )
        
        db.add(prompt)
        db.commit()
         
if __name__ == "__main__":   
    
    AddPromptToDB()