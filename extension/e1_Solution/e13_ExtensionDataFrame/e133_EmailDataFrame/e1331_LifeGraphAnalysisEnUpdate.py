import os
import re
import json
import tiktoken
import time
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, OpenAI_LLMresponse, ANTHROPIC_LLMresponse
from extension.e1_Solution.e11_General.e111_GetDBtable import GetExtensionPromptFrame
from extension.e1_Solution.e11_General.e111_GetDBtable import GetLifeGraph
from extension.e1_Solution.e13_ExtensionDataFrame.e131_ExtensionDataCommit.e1311_ExtensionDataFrameCommit import LoadExtensionOutputMemory, SaveExtensionOutputMemory, AddExistedLifeGraphContextDefineToDB, AddLifeGraphContextDefineContextChunksToDB, AddLifeGraphContextDefineLifeDataContextTextsToDB, LifeGraphContextDefineCountLoad, InitLifeGraphContextDefine, LifeGraphContextDefineCompletionUpdate, UpdatedLifeGraphContextDefine

#########################
##### InputList 생성 #####
#########################
## LifeGraphTranslationKo 로드
def LoadLifeGraphsEn(lifeGraphSetName, latestUpdateDate):
    lifeGraph = GetLifeGraph(lifeGraphSetName, latestUpdateDate)
    LifeGraphsEn = lifeGraph.LifeGraphTranslationEn[1]['LifeGraphsEn'][1:]
    ContextChunks = lifeGraph.LifeGraphContextDefine[1]['ContextChunks'][1:]
    
    return LifeGraphsEn, ContextChunks

## LoadLifeGraphsEn의 inputList 치환
def SaveInputListToTxt(InputList, InputFileNames):
    # 폴더 경로
    EmailDataPath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e412_EmailData"
    EmailPromptFolder = "e4121_01_FirstEmailCreationPrompts"
    FolderPath = os.path.join(EmailDataPath, EmailPromptFolder)

    # 폴더 생성
    if not os.path.exists(FolderPath):
        os.makedirs(FolderPath)
        print(f"[ 폴더 생성: {FolderPath}] ")
    else:
        print(f"[ 폴더 이미 존재: {FolderPath} ]")
    
    # 프롬프트 불러오기
    EmailPromptFile = 'e4121_01_FirstEmailCreationPrompt.txt'
    PromptPath = os.path.join(EmailDataPath, EmailPromptFile)
    with open(PromptPath, 'r') as file:
        EmailPrompt = file.read()

    # 각 항목을 텍스트 파일로 저장
    for i in range(len(InputList)):
        FilePath = os.path.join(FolderPath, f"{InputFileNames[i]['Date']}_{InputFileNames[i]['Name']}_{InputFileNames[i]['Age']}_FirstEmail.txt")
        _EmailPrompt = EmailPrompt.replace('<<<<Paste the life graph>>>>', f"{InputList[i]['Continue']}")
        with open(FilePath, 'w') as file:
            file.write(_EmailPrompt)
        
## LoadLifeGraphsEn의 inputList 치환
def LoadLifeGraphsEnToInputList(lifeGraphSetName, latestUpdateDate):
    LifeGraphsEn, ContextChunks = LoadLifeGraphsEn(lifeGraphSetName, latestUpdateDate)
    
    InputList = []
    InputFileNames = []
    for i in range(len(LifeGraphsEn)):
        Id = LifeGraphsEn[i]['LifeGraphId']
        LifeGraphDate = LifeGraphsEn[i]['LifeGraphDate']
        Name = LifeGraphsEn[i]['Name']
        Age = LifeGraphsEn[i]['Age']
        if LifeGraphsEn[i]['Residence'] != "None":
            Residence = ', '.join(LifeGraphsEn[i]['Residence']['Area'])
        else:
            Residence = ''
        LifeData = LifeGraphsEn[i]['LifeData']
        
        LifeDataIdList = []
        AgeList = []
        ScoreList = []
        ChunkList = []
        PurposeList = []
        ReasonList = []
        QuestionList = []
        
        for ContextChunk in ContextChunks[i]['ContextChunks']:
            LifeDataIdList.append(ContextChunk['ChunkId'] - 1)
            PurposeList.append(ContextChunk['Purpose'])
            ReasonList.append(ContextChunk['Reason'])
            QuestionList.append(ContextChunk['Question'])
            
        for LifeDataId in LifeDataIdList:
            AgeList.append(f"{LifeData[LifeDataId]['StartAge']}-{LifeData[LifeDataId]['EndAge']}")
            ScoreList.append(LifeData[LifeDataId]['Score'])
            ChunkList.append(LifeData[LifeDataId]['ReasonEn'])
                
        InputTitleText = f"Date: {LifeGraphDate}\nAuthor: {Name}\nAge: {Age}\nEstimated Nationality: {Residence}\n\n"
        InputBodyList = []
        for j in range(len(LifeDataIdList)):
            InputBodyList.append(f"[Age] {AgeList[j]}\n[Happiness Index] {ScoreList[j]}\n[Content] {ChunkList[j]}\n[Purpose] {PurposeList[j]}\n[Reason] {ReasonList[j]}\n[Author's Questions to be solved] {QuestionList[j]}")

        InputBodyText = '\n\n'.join(InputBodyList)
        InputText = InputTitleText + InputBodyText
        
        InputDic = {'Id': Id, 'Continue': InputText}
        InputList.append(InputDic)
        
        InputFileNameDic = {'Date': LifeGraphDate, 'Name': Name, 'Age': Age}
        InputFileNames.append(InputFileNameDic)
        
    SaveInputListToTxt(InputList, InputFileNames)
        
    return InputList

if __name__ == "__main__":
    
    ############################ 하이퍼 파라미터 설정 ############################
    lifeGraphSetName = "CourseraMeditation"
    latestUpdateDate = 23120601
    LifeGraphDataFramePath = "/yaas/extension/e4_Database/e41_DatabaseFeedback/e411_LifeGraphData/"
    messagesReview = "on"
    mode = "Master"
    #########################################################################
    
    LoadLifeGraphsEnToInputList(lifeGraphSetName, latestUpdateDate)