import os
import io
import json
import math
import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from google.cloud import speech
from pydub import AudioSegment
from pydub.silence import detect_nonsilent


#########################
##### InputList 생성 #####
#########################
## 음성파일을 STT로 단어별 시간 계산하기
def VoiceTimeStemps(voiceLayerPath, LanguageCode):
    # 환경 변수 설정 또는 코드 내에서 직접 경로 지정
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/yaas/backend/b4_Creation/b42_Generator/speechtotext-415411-4c2386f811df.json"

    # 클라이언트 생성
    client = speech.SpeechClient()

    # 오디오 파일 읽기
    with io.open(voiceLayerPath, 'rb') as AudioFile:
        GenedVoice = AudioFile.read()

    # 오디오 파일 설정
    audio = speech.RecognitionAudio(content = GenedVoice)
    config = speech.RecognitionConfig(
        encoding = speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz = 44100,
        language_code = LanguageCode,
        enable_word_time_offsets = True
    )

    # 음성 인식 요청 및 응답 처리
    response = client.recognize(config = config, audio = audio)

    # 각 단어의 시작 및 종료 타임스탬프 출력
    voiceTimeStemps = []
    Voices = []
    RecordIdList = []
    Id = 1
    for result in response.results:
        for alternative in result.alternatives:
            for wordInfo in alternative.words:
                word = wordInfo.word
                # total_seconds() 호출로 변환
                start_time = wordInfo.start_time.total_seconds() if wordInfo.start_time else 0
                end_time = wordInfo.end_time.total_seconds() if wordInfo.end_time else 0
                voiceTimeStemps.append({"낭독기록번호": Id, "낭독기록": word, "시작": start_time, "끝": end_time})
                Voices.append({"낭독기록번호": Id, "낭독기록": word})
                RecordIdList.append(Id)
                Id += 1
                
    return voiceTimeStemps, Voices, RecordIdList

######################
##### Filter 조건 #####
######################
## 음성파일을 STT로 단어별 시간 계산하기
def VoiceTimeStempsProcessFilter(Response, RecordIdList):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        Json = json.loads(Response)
        outputJson = Json['낭독']
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(outputJson, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # Error3: outputJson와 Input의 수가 다를때 예외 처리
    outputJsonList = []
    for output in outputJson:
        outputJsonList += output['낭독기록번호리스트']
    if outputJsonList != RecordIdList:
        return "JSON 수가 다름: JSONCountError"

    return outputJson

## VoiceSplit 프롬프트 요청 및 결과물 Json화
def VoiceSplitProcess(projectName, email, Input1, Input2, RecordIdList, Process = "VoiceSplit"):
    # Input 생성
    Input = "<낭독문>\n" + str(Input1) + "\n\n" + "<낭독기록>\n" + str(Input2)

    for _ in range(10):
        # Response 생성
        Response, Usage, Model = LLMresponse(projectName, email, Process, Input, 0)
        print(Model)
        print(Response)
        Filter = VoiceTimeStempsProcessFilter(Response, RecordIdList)
        
        if isinstance(Filter, str):
            print(f"Project: {projectName} | Process: {Process} | {Filter}")
        else:
            break
        
    return Filter

## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps(음성 파일에서 커팅되어야 할 부분) 구축
def VoiceTimeStempsClassification(VoiceTimeStemps, Filter):
    SplitTimeList = []
    for Response in Filter:
        CurrentTime = Response['낭독기록번호리스트'][0]
        EndTime = Response['낭독기록번호리스트'][-1]
        
        CurrentSplitTime = VoiceTimeStemps[CurrentTime - 1]['시작']
        
        SplitTimeList.append(CurrentSplitTime)
        
    SplitTimeList = SplitTimeList[1:]
        
    return SplitTimeList

## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps(음성 파일에서 커팅되어야 할 부분) 구축

def find_nearest_silence(audio, target_time, min_silence_len=100, silence_thresh=-40):
    """
    주어진 시간 근처에서 가장 가까운 무음 구간을 찾아 그 중앙을 반환합니다.
    
    Parameters:
    - audio: AudioSegment 객체
    - target_time: 타겟 시간 (초)
    - min_silence_len: 감지할 최소 무음 길이 (밀리초)
    - silence_thresh: 무음으로 간주할 최소 데시벨 수준
    
    Returns:
    - 중앙 무음 시간 (밀리초)
    """
    nonsilent_parts = detect_nonsilent(
        audio, 
        min_silence_len=min_silence_len, 
        silence_thresh=silence_thresh
    )
    
    # 타겟 시간을 밀리초로 변환
    target_time_ms = target_time * 1000
    nearest_silence_center = None
    smallest_diff = float('inf')
    
    # 가장 가까운 무음 구간 찾기
    for nonsilent in nonsilent_parts:
        start, end = nonsilent
        if start <= target_time_ms <= end:
            # 타겟 시간이 무음 구간 내부에 있는 경우
            nearest_silence_center = (start + end) / 2
            break
        else:
            # 가장 가까운 무음 구간 찾기
            diff = min(abs(target_time_ms - start), abs(target_time_ms - end))
            if diff < smallest_diff:
                smallest_diff = diff
                nearest_silence_center = (start + end) / 2
    
    return nearest_silence_center

def VoiceFileSplit(VoiceLayerPath, SplitTimeList, base_export_path="/yaas/", min_silence_len=100, silence_thresh=-40):
    # 오디오 파일 로드
    audio = AudioSegment.from_wav(VoiceLayerPath)
    
    split_points = [0]  # 첫 번째 분할 지점 추가
    for split_time in SplitTimeList:
        # 가장 가까운 무음 구간 중앙 찾기
        nearest_silence_center = find_nearest_silence(audio, split_time, min_silence_len, silence_thresh)
        if nearest_silence_center is not None:
            split_points.append(nearest_silence_center)
    
    split_points.append(len(audio))  # 마지막 분할 지점 추가

    # 오디오 분할 및 파일로 저장
    for i in range(len(split_points)-1):
        start_ms, end_ms = split_points[i], split_points[i+1]
        segment = audio[start_ms:end_ms]
        export_path = os.path.join(base_export_path, f"segment_{i+1}.wav")
        segment.export(export_path, format="wav")
        print(f"Exported: {export_path}")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    voiceDataSet = "TypeCastVoiceDataSet"
    mainLang = 'Ko'
    mode = "Manual"
    macro = "Manual"
    VoiceLayerPath = "/yaas/storage/s1_Yeoreum/s14_VoiceStorage/테스트(가)_0_지훈(일반, 피치다운).wav"
    LanguageCode = "ko-KR"
    #########################################################################
    voiceTimeStemps, Input2, RecordIdList = VoiceTimeStemps(VoiceLayerPath, LanguageCode)
    Input1 = [{'낭독문장번호': 1, '낭독문장': '뿐만 아니라, 여름은 최근 창업진흥원에서 주관하는 대회에서 대상을 수상하며, 그들의 혁신적인 기술과 사회적 기여를 인정받았다.'}, {'낭독문장번호': 2, '낭독문장': '이준영 대표는 수상 소감에서 "이 상은 단지 우리의 기술적 성과만을 인정하는 것이 아니라, 우리가 추구하는 가치와 비전에 대한 공감을 의미합니다.'}, {'낭독문장번호': 3, '낭독문장': '우리는 앞으로도 지식의 접근성을 높이고, 누구나 쉽게 지식을 소비할 수 있는 환경을 만드는 것을 목표로 삼고 있습니다.'}, {'낭독문장번호': 4, '낭독문장': '라고 전했다.'}]
    Filter = VoiceSplitProcess(projectName, email, Input1, Input2, RecordIdList, Process = "VoiceSplit")
    print(Filter)
    SplitTimeList = VoiceTimeStempsClassification(voiceTimeStemps, Filter)
    print(SplitTimeList)
    VoiceFileSplit(VoiceLayerPath, SplitTimeList)