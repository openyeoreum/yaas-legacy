import os
import io
import json
import numpy as np
import webrtcvad
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
                Id += 1
                
    return voiceTimeStemps, Voices

######################
##### Filter 조건 #####
######################
## 음성파일을 STT로 단어별 시간 계산하기
def VoiceTimeStempsProcessFilter(Response, AlphabetList, LastNumber):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        Json = json.loads(Response)
        outputJson = Json['매칭']
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(outputJson, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # Error3: 결과가 list가 아닐 때의 예외 처리
    if len(AlphabetList) != len(outputJson):
        return "Response의 리스트 개수와 문장(분할) 수가 다름: JSONCountError"
    # Error4: 결과에 마지막 문장이 포함될 때의 예외 처리
    if int(outputJson[-1]['숫자']) == LastNumber:
        return "Response에 LastNumber가 포함됨: JSONCountError"

    return outputJson

## Input1과 Input2를 입력으로 받아 최종 Input 생성
def InputText(Input1, Input2):
    # InputText1 생성
    InputText1 = ""
    Alphabet = "A"  # 시작 알파벳
    AlphabetList = []
    for i in range(len(Input1)):
        if i > 0:  # 첫 번째 문장이 아니라면 앞에 알파벳을 추가한다
            InputText1 += f" [{Alphabet}] "
            AlphabetList.append(Alphabet)
            Alphabet = chr(ord(Alphabet) + 1)  # 다음 알파벳으로 업데이트
        InputText1 += Input1[i]['낭독문장']
        
    # InputText2 생성
    InputText2 = ""
    for i, record in enumerate(Input2):
        if i > 0:  # 첫 번째 기록이 아니라면 앞에 숫자를 추가한다
            InputText2 += f" [{i}] "
        InputText2 += record['낭독기록']
    LastNumber = i
    
    # 최종 Input 생성
    Input = "<낭독원문>\n" + str(InputText1) + "\n\n" + "<낭독STT단어문>\n" + str(InputText2)
    
    return Input, AlphabetList, LastNumber

## VoiceSplit 프롬프트 요청
def VoiceSplitProcess(projectName, email, Input1, Input2, Process = "VoiceSplit", MessagesReview = "off"):
    ## Input1과 Input2를 입력으로 받아 최종 Input 생성
    Input, AlphabetList, LastNumber = InputText(Input1, Input2)
    ## memoryCounter 생성
    memoryCounter = f"\n\n최종주의사항\n1) 매우 중요한 작업임으로, 알파벳 [{'], ['.join(AlphabetList)}] 모두 신중하게 매칭!\n2) <낭독원문>의 문장과 <낭독STT단어문>의 단어가 자주 다르게 작성, 이 경우 <낭독STT단어문>의 앞 뒤 기록으로 유추하여 <낭독원문>의 [알파벳]과 [숫자]를 매칭!\n3) 매칭 순서가 밀리거나 누락되지 않도록 하나씩 하나씩, 신중하게 매칭!\n\n"

    for _ in range(10):
        # Response 생성
        Response, Usage, Model = LLMresponse(projectName, email, Process, Input, 0, Mode = "Master", MemoryCounter = memoryCounter, messagesReview = MessagesReview)
        ResponseJson = VoiceTimeStempsProcessFilter(Response, AlphabetList, LastNumber)
        
        if isinstance(ResponseJson, str):
            print(f"Project: {projectName} | Process: {Process} | {ResponseJson}")
        else:
            break
        
    return ResponseJson

## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps 커팅 데이터 구축
def VoiceTimeStempsClassification(VoiceTimeStemps, ResponseJson):
    SplitTimeList = []
    for Response in ResponseJson:
        CurrentTime = int(Response['숫자'])
        CurrentSplitTime = VoiceTimeStemps[CurrentTime]['시작']
        SplitTimeList.append(CurrentSplitTime)
        
    return SplitTimeList

## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps(음성 파일에서 커팅되어야 할 부분) 구축
def VoiceFileSplit(VoiceLayerPath, SplitTimeList):
    # 오디오 파일 로드
    audio = AudioSegment.from_wav(VoiceLayerPath)
    
    def find_optimal_split_point(audio, split_time, detail = False):
        # 주변 평균값 탐색을 위한 초기화
        metrics = []
        step = 0.05 if not detail else 0.01  # 세밀한 분석을 위한 단계 조정
        range_end = 0.3 if not detail else 0.05  # 세밀한 분석을 위한 범위 조정

        for delta in np.arange(-range_end, range_end + step, step):
            start = int((split_time + delta) * 1000)  # milliseconds
            end = int((split_time + delta + (0.1 if not detail else 0.02)) * 1000)  # milliseconds
            segment = audio[start:end]
            
            # segment 데이터를 처리할 수 있는 형태로 변환
            segment_samples = np.abs(np.array(segment.get_array_of_samples()))
            average = np.mean(segment_samples)
            
            metrics.append((start / 1000, average))
        
        # 평균값을 고려하여 가장 적합한 분할 지점 찾기
        metrics.sort(key=lambda x: x[1])  # 평균값이 낮은 순으로 정렬
        optimal_split_point, min_value = metrics[0][0], metrics[0][1]

        # 연속적인 0값들의 구간 찾기 및 처리
        if min_value == 0:
            zero_intervals = []
            current_interval = []
            for time, value in metrics:
                if value == 0:
                    if not current_interval:
                        current_interval = [time, time]
                    else:
                        current_interval[1] = time
                else:
                    if current_interval:
                        zero_intervals.append(tuple(current_interval))
                        current_interval = []
            if current_interval:
                zero_intervals.append(tuple(current_interval))

            if zero_intervals:
                longest_interval = max(zero_intervals, key=lambda x: x[1] - x[0])
                optimal_split_point = sum(longest_interval) / 2
        elif min_value != 0 and not detail:
            # 세밀한 분석을 위해 다시 호출
            return find_optimal_split_point(audio, optimal_split_point, detail = True)

        return optimal_split_point

    # 최종 분할 지점을 저장할 리스트
    split_points = []
    for split_time in SplitTimeList:
        optimal_split_point = find_optimal_split_point(audio, split_time)
        split_points.append(optimal_split_point)

    # 파일 분할 및 저장
    start_point = 0
    split_points.append(audio.duration_seconds)  # 마지막 부분 포함하기 위해 추가
    for i, split_point in enumerate(split_points):
        end_point = int(split_point * 1000)  # milliseconds로 변환
        segment = audio[start_point:end_point]
        # 페이드인/아웃 적용
        segment = segment.fade_in(duration = 30).fade_out(duration = 30)  # 0.03초 페이드인, 0.03초 페이드아웃
        # 무음 추가
        silence = AudioSegment.silent(duration = 30)  # 0.03초 무음
        segment = silence + segment + silence  # 무음 - 세그먼트 - 무음
        
        ExportPathText = VoiceLayerPath.replace(".wav", "")
        if ExportPathText[-1] == 'M':
            ExportPathText = ExportPathText.replace("M", "")
            ExportPath = ExportPathText + f"_({i})M.wav"
        else:
            ExportPath = ExportPathText + f"_({i}).wav"
        segment.export(ExportPath, format = "wav")
        print(f"Segment {i} exported: Start at {start_point / 1000:.5f}, end at {split_point:.5f} with fades and silence")
        start_point = end_point
        
    # 파일 분할이 완료된 후 원본 오디오 파일 삭제
    os.remove(VoiceLayerPath)

## VoiceSplit 최종 함수
def VoiceSplit(projectName, email, name, VoiceLayerPath, Input, LanguageCode = "ko-KR", MessagesReview = "off"):

    print(f"VoiceSplit: progress, {name} waiting 15 second")
    ## 음성파일을 STT로 단어별 시간 계산하기
    voiceTimeStemps, Input2 = VoiceTimeStemps(VoiceLayerPath, LanguageCode)
    ## VoiceSplit 프롬프트 요청
    ResponseJson = VoiceSplitProcess(projectName, email, Input, Input2, Process = "VoiceSplit", MessagesReview = MessagesReview)
    ## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps 커팅 데이터 구축
    SplitTimeList = VoiceTimeStempsClassification(voiceTimeStemps, ResponseJson)
    ## VoiceSplit 프롬프트 요청을 바탕으로 SplitTimeStemps(음성 파일에서 커팅되어야 할 부분) 구축
    VoiceFileSplit(VoiceLayerPath, SplitTimeList)

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    VoiceLayerPath = "/yaas/storage/s1_Yeoreum/s14_VoiceStorage/테스트(가)_0_연우(중간톤, 피치다운).wav"
    LanguageCode = "ko-KR"
    #########################################################################