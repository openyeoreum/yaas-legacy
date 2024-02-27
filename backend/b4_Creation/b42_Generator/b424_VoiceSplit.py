import os
import io
import json
import numpy as np
import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from google.cloud import speech
from pydub import AudioSegment

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
        # EndTime = Response['낭독기록번호리스트'][-1]
        CurrentSplitTime = VoiceTimeStemps[CurrentTime - 1]['시작']
        SplitTimeList.append(CurrentSplitTime)
    SplitTimeList = SplitTimeList[1:]
        
    return SplitTimeList

## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps(음성 파일에서 커팅되어야 할 부분) 구축
def VoiceFileSplit(VoiceLayerPath, SplitTimeList):
    # 오디오 파일 로드
    audio = AudioSegment.from_wav(VoiceLayerPath)
    
    # 분할된 파일 저장할 기본 경로
    base_export_path = "/yaas/"
    
    # 최종 분할 지점을 저장할 리스트
    split_points = []
    
    for split_time in SplitTimeList:
        # 주변 평균값 탐색을 위한 초기화
        averages = []
        
        for delta in np.arange(-0.5, 0.5, 0.05):
            start = int((split_time + delta) * 1000)  # milliseconds
            end = int((split_time + delta + 0.1) * 1000)  # milliseconds
            segment = audio[start:end]
            average = np.mean(np.abs(segment.get_array_of_samples()))
            averages.append((start / 1000, average))
        
        # 가장 낮은 평균값 찾기
        averages.sort(key=lambda x: x[1])
        min_avg_time, _ = averages[0]
        
        # 최적 분할 지점 계산
        optimal_split_point = min_avg_time
        split_points.append(optimal_split_point)
    
    # 파일 분할 및 저장
    start_point = 0
    split_points.append(audio.duration_seconds)  # 마지막 부분 포함하기 위해 추가
    for i, split_point in enumerate(split_points):
        end_point = int(split_point * 1000)  # milliseconds로 변환
        segment = audio[start_point:end_point]
        # 페이드인/아웃 적용
        segment = segment.fade_in(duration = 50).fade_out(duration = 50)  # 0.5초 페이드인, 0.05초 페이드아웃
        # 무음 추가
        silence = AudioSegment.silent(duration = 50)  # 0.05초 무음
        segment = silence + segment + silence  # 무음 - 세그먼트 - 무음
        
        export_path = base_export_path + f"split_{i}.wav"
        segment.export(export_path, format="wav")
        print(f"Segment {i} exported: Start at {start_point / 1000:.5f}, end at {split_point:.5f} with fades and silence")
        start_point = end_point

## VoiceSplit 최종 함수
def VoiceSplit(projectName, email, VoiceLayerPath, Input, LanguageCode):

    voiceTimeStemps, Input2, RecordIdList = VoiceTimeStemps(VoiceLayerPath, LanguageCode)
    Filter = VoiceSplitProcess(projectName, email, Input, Input2, RecordIdList, Process = "VoiceSplit")
    SplitTimeList = VoiceTimeStempsClassification(voiceTimeStemps, Filter)
    VoiceFileSplit(VoiceLayerPath, SplitTimeList)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    VoiceLayerPath = "/yaas/storage/s1_Yeoreum/s14_VoiceStorage/테스트(가)_0_연우(중간톤, 피치다운).wav"
    LanguageCode = "ko-KR"
    #########################################################################
    Input = [{'낭독문장번호': 1, '낭독문장': '뿐만 아니라, 여름은 최근 창업진흥원에서 주관하는 대회에서 대상을 수상하며'}, {'낭독문장번호': 2, '낭독문장': '그들의 혁신적인 기술과 사회적 기여를 인정받았다.'}, {'낭독문장번호': 3, '낭독문장': '이준영 대표는 수상 소감에서 "이 상은 단지 우리의 기술적 성과만을 인정하는 것이 아니라, 우리가 추구하는 가치와 비전에 대한 공감을 의미합니다.'}, {'낭독문장번호': 4, '낭독문장': '우리는 앞으로도 지식의 접근성을 높이고, 누구나 쉽게 지식을 소비할 수 있는 환경을 만드는 것을 목표로 삼고 있습니다.'}, {'낭독문장번호': 5, '낭독문장': '라고 전했다.'}]

    VoiceSplit(projectName, email, VoiceLayerPath, Input, LanguageCode)
    
    # 파일 경로 설정
    files = [
        "/yaas/split_0.wav",
        "/yaas/split_1.wav",
        "/yaas/split_2.wav",
        "/yaas/split_3.wav",
        "/yaas/split_4.wav"
    ]

    # 무음 추가를 위한 오디오 세그먼트 생성
    silence_short = AudioSegment.silent(duration = 200)  # 0.2초의 무음
    silence_long = AudioSegment.silent(duration = 800)  # 0.7초의 무음

    # 첫 번째 오디오 파일 로드
    combined = AudioSegment.from_wav(files[0])

    # 나머지 오디오 파일들을 순회하며 조건에 맞는 무음 추가 후 합치기
    for index, file in enumerate(files[1:], start=1):
        audio = AudioSegment.from_wav(file)
        # 0과 1, 3과 4 사이는 0.2초 무음, 1과 2, 2와 3 사이는 0.7초 무음
        if index == 1 or index == 4:  # 조건에 따라 무음 길이 변경
            combined += silence_short + audio
        else:
            combined += silence_long + audio

    # 합친 오디오 파일 저장
    combined.export("/yaas/combined_file.wav", format="wav")