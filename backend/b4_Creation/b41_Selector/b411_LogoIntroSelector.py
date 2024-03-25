import os
import unicodedata
import json
import requests
import time
import random
import re
import copy
import sys
sys.path.append("/yaas")

from tqdm import tqdm
from pydub import AudioSegment
from collections import defaultdict
from sqlalchemy.orm.attributes import flag_modified
from backend.b1_Api.b14_Models import User
from backend.b1_Api.b13_Database import get_db
from backend.b2_Solution.b21_General.b211_GetDBtable import GetProject, GetVoiceDataSet


##########################
##### VoiceLayer 생성 #####
##########################
## LoadVoiceLayer 로드
def LoadVoiceLayer(projectName, email, MainLang = 'Ko'):
    project = GetProject(projectName, email)
    
    ## MainLang의 언어별 SelectionGenerationKoChunks 불러오기
    if MainLang == 'Ko':
        SelectionGenerationBookContext = project.SelectionGenerationKo[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
    if MainLang == 'En':
        SelectionGenerationBookContext = project.SelectionGenerationEn[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
    # if MainLang == 'Ja':
        # SelectionGenerationBookContext = project.SelectionGenerationJa[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
    # if MainLang == 'Zh':
        # SelectionGenerationBookContext = project.SelectionGenerationZh[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
    # if MainLang == 'Es':
        # SelectionGenerationBookContext = project.SelectionGenerationEs[1]['SelectionGeneration' + MainLang + 'BookContext'][1]
    
    ## MainLang의 언어별 VoiceLayer 불러오기
    VoiceLayer = project.MixingMasteringKo[1]['AudioBookLayers' + MainLang]
    
    return SelectionGenerationBookContext, VoiceLayer

def LogoIntroSelector(projectName, email, MainLang = 'Ko'):
    
    SelectionGenerationBookContext, VoiceLayer = LoadVoiceLayer(projectName, email, MainLang = MainLang)
    
    print(SelectionGenerationBookContext['Vector']['ContextCompletion']['Genre']['Genre'])

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "노인을위한나라는있다"
    mainLang = 'Ko'
    #########################################################################
    
    LogoIntroSelector(projectName, email, MainLang = mainLang)