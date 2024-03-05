import os
import io
import json
import re
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
def VoiceTimeStempsProcessFilter(Response, AlphabetList, LastNumber, NumberWordList):
    # Error1: json 형식이 아닐 때의 예외 처리
    try:
        Json = json.loads(Response)
        outputJson = Json['매칭']
    except json.JSONDecodeError:
        return "JSONDecode에서 오류 발생: JSONDecodeError"
    # Error2: 결과가 list가 아닐 때의 예외 처리
    if not isinstance(outputJson, list):
        return "JSONType에서 오류 발생: JSONTypeError"
    # Error3: 결과와 시작의 알파벳이 다를 때의 예외 처리
    for i in range(len(AlphabetList)):
        if AlphabetList[i] != outputJson[i]['알파벳']:
            return "Response의 리스트와 본문의 알파벳이 일치하지 않음: JSONMatchingError"
    # Error4: 결과에 마지막 문장이 포함될 때의 예외 처리
    if int(outputJson[-1]['숫자']) == LastNumber:
        return "Response에 LastNumber가 포함됨: JSONCountError"
    # Error5: 앞단어 - 숫자 - 뒷단어 순서가 잘못 되었을때의 예외 처리
    for output in outputJson:
        outputText = output['매칭확인']
        # 정규 표현식을 사용하여 대괄호 안의 숫자 추출
        number = int(re.findall(r'\[(\d+)\]', outputText)[0]) if re.findall(r'\[(\d+)\]', outputText) else -99
        # 대괄호와 숫자를 제거하고 나머지 문자열 분할
        parts = re.split(r'\[\d+\]', outputText)

        if [parts[0].strip()] + [number] + [parts[1].strip()] in NumberWordList:
            output['숫자'] = number
        elif [parts[0].strip()] + [number + 1] + [parts[1].strip()] in NumberWordList:
            output['숫자'] = number + 1
        elif [parts[0].strip()] + [number - 1] + [parts[1].strip()] in NumberWordList:
            output['숫자'] = number - 1
        else:
            return "Response에 앞단어 - 숫자 - 뒷단어 표기가 틀림: JSONOutputError"

    return outputJson

## Input1과 Input2를 입력으로 받아 최종 Input 생성
def InputText(SplitSents, SplitWords, SameNum):
    # AlphabetList 생성
    Alphabet = "A"
    AlphabetList = []
    AlphabetABSentList = []
    AlphabetABWordList = []

    # 분석 및 리스트 생성
    for i in range(len(SplitSents)):
        if i > 0:
            # 알파벳 추가 및 인덱스 계산
            AlphabetABSentList.append(Alphabet)
            BeforeWord = SplitSents[i-1]['낭독문장'].strip().split()
            AfterWord = SplitSents[i]['낭독문장'].strip().split()
            try:
                AlphabetABWordList.append([BeforeWord[-2], BeforeWord[-1], Alphabet, AfterWord[0], AfterWord[1]])
            except IndexError:
                AlphabetABWordList.append([None, BeforeWord[-1], Alphabet, AfterWord[0], None])
            AlphabetList.append(Alphabet)
            if i < len(SplitSents) - 1:
                Alphabet = chr(ord(Alphabet) + 1)
        AlphabetABSentList.append(SplitSents[i]['낭독문장'])
    
    # SEAlphabetList 생성
    SEAlphabetList = ['Start'] + AlphabetList + ['End']

    # print(f'AlphabetList: {AlphabetList}\n')
    # print(f'AlphabetABSentList: {AlphabetABSentList}\n')
    # print(f'AlphabetABWordList: {AlphabetABWordList}\n')

    # NumberList 생성
    NumberABSentList = []
    NumberABWordList = []
    NumberWordList = []
    for i in range(len(SplitWords)):
        if i > 0:  # 첫 번째 기록이 아니라면 앞에 숫자를 추가한다
            NumberABSentList.append(i)
            # 리스트의 시작과 끝을 연결하기 위해 인덱스 계산
            Before2Index = (i-2) % len(SplitWords)
            Before1Index = (i-1) % len(SplitWords)
            After1Index = (i+1) % len(SplitWords)
            NumberABWordList.append([SplitWords[Before2Index]['낭독기록'], SplitWords[Before1Index]['낭독기록'], i, SplitWords[i]['낭독기록'], SplitWords[After1Index]['낭독기록']])
            NumberWordList.append([SplitWords[Before1Index]['낭독기록'], i, SplitWords[i]['낭독기록']])
        NumberABSentList.append(SplitWords[i]['낭독기록'])
    LastNumber = i

    # print(f'NumberABSentList: {NumberABSentList}\n\n')
    # print(f'NumberABWordList: {NumberABWordList}\n\n')

    ## AlphabetList와 NumberList 일치요소 찾기 ##
    SameAlphabet = []
    NotSameAlphabet = AlphabetList.copy()
    SameDic = {} # 빈 딕셔너리로 초기화
    ShortMatchingCount = 0
    MiddleMatchingCount = 0
    _MiddleMatchingCount = 0
    LongMatchingCount = 0
    BeforeAlphabet = None
    for AlphabetABWord in AlphabetABWordList:
        for NumberABWord in NumberABWordList:
            if SameDic == {}:
                for i in [1, 3]:
                    if NumberABWord[i] == AlphabetABWord[i]:
                        ShortMatchingCount += 1
                for i in [0, 1, 3]:
                    if NumberABWord[i] in AlphabetABWord[i]:
                        MiddleMatchingCount += 1
                for i in [1, 3, 4]:
                    if NumberABWord[i] in AlphabetABWord[i]:
                        _MiddleMatchingCount += 1
                for i in [0, 1, 3, 4]:
                    if NumberABWord[i] in AlphabetABWord[i]:
                        LongMatchingCount += 1
                if ShortMatchingCount == 2:
                    SameAlphabet.append(AlphabetABWord[2])
                    NotSameAlphabet.remove(AlphabetABWord[2])
                    # 딕셔너리에 키와 값을 추가
                    SameDic[AlphabetABWord[2]] = NumberABWord[2]
                    BeforeAlphabet = AlphabetABWord[2]
                elif MiddleMatchingCount == 3:
                    SameAlphabet.append(AlphabetABWord[2])
                    NotSameAlphabet.remove(AlphabetABWord[2])
                    SameDic[AlphabetABWord[2]] = NumberABWord[2]
                    BeforeAlphabet = AlphabetABWord[2]
                elif _MiddleMatchingCount == 3:
                    SameAlphabet.append(AlphabetABWord[2])
                    NotSameAlphabet.remove(AlphabetABWord[2])
                    SameDic[AlphabetABWord[2]] = NumberABWord[2]
                    BeforeAlphabet = AlphabetABWord[2]
                elif LongMatchingCount >= SameNum: # 테스트 후 3으로 변경
                    SameAlphabet.append(AlphabetABWord[2])
                    NotSameAlphabet.remove(AlphabetABWord[2])
                    SameDic[AlphabetABWord[2]] = NumberABWord[2]
                    BeforeAlphabet = AlphabetABWord[2]
                ShortMatchingCount = 0
                MiddleMatchingCount = 0
                _MiddleMatchingCount = 0
                LongMatchingCount = 0
                
            elif SameDic != {}:
                if SameDic[BeforeAlphabet] <= NumberABWord[2]:
                    for i in [1, 3]:
                        if NumberABWord[i] == AlphabetABWord[i]:
                            ShortMatchingCount += 1
                    for i in [0, 1, 3]:
                        if NumberABWord[i] in AlphabetABWord[i]:
                            MiddleMatchingCount += 1
                    for i in [1, 3, 4]:
                        if NumberABWord[i] in AlphabetABWord[i]:
                            _MiddleMatchingCount += 1
                    for i in [0, 1, 3, 4]:
                        if NumberABWord[i] in AlphabetABWord[i]:
                            LongMatchingCount += 1
                    if ShortMatchingCount == 2:
                        SameAlphabet.append(AlphabetABWord[2])
                        NotSameAlphabet.remove(AlphabetABWord[2])
                        # 딕셔너리에 키와 값을 추가
                        SameDic[AlphabetABWord[2]] = NumberABWord[2]
                        BeforeAlphabet = AlphabetABWord[2]
                    elif MiddleMatchingCount == 3:
                        SameAlphabet.append(AlphabetABWord[2])
                        NotSameAlphabet.remove(AlphabetABWord[2])
                        SameDic[AlphabetABWord[2]] = NumberABWord[2]
                        BeforeAlphabet = AlphabetABWord[2]
                    elif _MiddleMatchingCount == 3:
                        SameAlphabet.append(AlphabetABWord[2])
                        NotSameAlphabet.remove(AlphabetABWord[2])
                        SameDic[AlphabetABWord[2]] = NumberABWord[2]
                        BeforeAlphabet = AlphabetABWord[2]
                    elif LongMatchingCount >= SameNum: # 테스트 후 3으로 변경
                        SameAlphabet.append(AlphabetABWord[2])
                        NotSameAlphabet.remove(AlphabetABWord[2])
                        SameDic[AlphabetABWord[2]] = NumberABWord[2]
                        BeforeAlphabet = AlphabetABWord[2]
                    ShortMatchingCount = 0
                    MiddleMatchingCount = 0
                    _MiddleMatchingCount = 0
                    LongMatchingCount = 0

    # SameAlphabet에 Start, End 붙히기
    SESameDic = SameDic.copy()
    if AlphabetList[0] in SameAlphabet:
        # 딕셔너리의 시작 부분에 'Start' 추가
        SESameDic = {'Start': 0, **SameDic}
        SameAlphabet = ['Start'] + SameAlphabet
    if AlphabetList[-1] in SameAlphabet:
        SameAlphabet = SameAlphabet + ['End']
        # 딕셔너리의 끝 부분에 'End' 추가
        SESameDic['End'] = LastNumber + 1
        
    # SameAlphabet과 SameNumber에 RangeList 만들기
    SameAlphabetRange = []
    SameNumberRange = []
    for i in range(len(SameAlphabet)):
        if i > 0:
            for j in range(len(SEAlphabetList)):
                if SameAlphabet[i] == SEAlphabetList[j]:
                    if SameAlphabet[i-1] == SEAlphabetList[j-1]:
                        SameAlphabetRange.append(SameAlphabet[i-1] + '-' + SameAlphabet[i])
                        SameNumberRange.append([SESameDic[SameAlphabet[i-1]], SESameDic[SameAlphabet[i]]])
    if SameNumberRange == []:
        SameNumberRange = [[None, None]]
    # SameNumberRange 앞 뒤 데이터의 마지막 값과 첫 값이 같으면 합치는 로직
    MergedSameNumberRange = []
    for currentRange in SameNumberRange:
        if not MergedSameNumberRange:
            MergedSameNumberRange.append(currentRange)
        else:
            lastRange = MergedSameNumberRange[-1]
            # 현재 범위의 시작 값이 이전 범위의 끝 값과 같다면 합침
            if lastRange[1] == currentRange[0]:
                MergedSameNumberRange[-1] = [lastRange[0], currentRange[1]]
            else:
                MergedSameNumberRange.append(currentRange)
                
    # print(f'SameAlphabet: {SameAlphabet}\n\n')
    # print(f'SameAlphabetRange: {SameAlphabetRange}\n\n')
    # print(f'MergedSameNumberRange: {MergedSameNumberRange}\n\n')
    # print(f'NotSameAlphabet: {NotSameAlphabet}\n\n')
    # print(f'SameDic: {SameDic}\n\n')
    # print(f'SESameDic: {SESameDic}\n\n')
    
    # NotSameAlphabetSentList 생성 (Input으로 들어갈 문장)
    NotSameAlphabetSentList = []
    SeenSentences = {}
    for i, item in enumerate(AlphabetABSentList):
        if item in NotSameAlphabet:
            # Add the sentence before the alphabet if it hasn't been added already
            if AlphabetABSentList[i-1] not in SeenSentences:
                NotSameAlphabetSentList.append(AlphabetABSentList[i-1])
                SeenSentences[AlphabetABSentList[i-1]] = True
            # Add the alphabet
            NotSameAlphabetSentList.append(item.replace(item, f' [{item}] '))
            # Add the sentence after the alphabet if it exists and hasn't been added already
            if i+1 < len(AlphabetABSentList) and AlphabetABSentList[i+1] not in SeenSentences:
                NotSameAlphabetSentList.append(AlphabetABSentList[i+1])
                SeenSentences[AlphabetABSentList[i+1]] = True
                
    # print(f'NotSameAlphabetSentList: {NotSameAlphabetSentList}\n\n')

    # NotSameNumberWordList 생성 (Input으로 들어갈 문장)
    NotSameNumberWordList = []
    NumberABSentList = [0] + NumberABSentList + [LastNumber + 1]
    RemoveSwitch = 0
    RemoveRangeCount = 0
    RemoveRange = MergedSameNumberRange[RemoveRangeCount]
    for ABWord in NumberABSentList:
        if ABWord == RemoveRange[0]:
            RemoveSwitch = 1
        if ABWord == RemoveRange[1]:
            RemoveSwitch = 0
            RemoveRangeCount += 1
            if RemoveRangeCount < len(MergedSameNumberRange):
                RemoveRange = MergedSameNumberRange[RemoveRangeCount]
        if RemoveSwitch == 0:
            if isinstance(ABWord, int):
                ABWord = f' [{ABWord}] '
                lastNumber = ABWord
            NotSameNumberWordList.append(ABWord)
    for alphabet in SameAlphabet:
        if f' [{SESameDic[alphabet]}] ' in NotSameNumberWordList:
            NotSameNumberWordList.remove(f' [{SESameDic[alphabet]}] ')
    if f' [{LastNumber + 1}] ' in NotSameNumberWordList:
        NotSameNumberWordList.remove(f' [{LastNumber + 1}] ')

    # print(f'NotSameNumberWordList: {NotSameNumberWordList}\n\n')
    
    # 최종 Input 생성
    Input = "<낭독원문>\n" + ''.join(NotSameAlphabetSentList) + "\n\n" + "<낭독STT단어문>\n" + ''.join(NotSameNumberWordList)
    
    # 최종 RawResponse 생성
    RawResponse = [{'알파벳': key, '숫자': value} for key, value in SameDic.items()]
    
    return Input, NotSameAlphabet, lastNumber, NumberWordList, AlphabetList, RawResponse

## VoiceSplit 프롬프트 요청
def VoiceSplitProcess(projectName, email, SplitSents, SplitWords, Process = "VoiceSplit", MessagesReview = "off"):
    ## Input1과 Input2를 입력으로 받아 최종 Input 생성
    Input, NotSameAlphabet, lastNumber, NumberWordList, AlphabetList, RawResponse = InputText(SplitSents, SplitWords, 3)
    ## memoryCounter 생성
    memoryCounter = f"\n\n최종주의사항: [알파벳]과 [숫자]를 매칭할때 [알파벳]의 앞뒤 부분과 [숫자]의 앞뒤 부분을 통해서 자세히 살펴보고 매칭!, 알파벳 [{'], ['.join(NotSameAlphabet)}] 신중하게 매칭!\n\n"

    # print(f'Input: {Input}\n\n')
    # print(f'NotSameAlphabet: {NotSameAlphabet}\n\n')
    # print(f'lastNumber: {lastNumber}\n\n')
    # print(f'NumberWordList: {NumberWordList}\n\n')
    # print(f'AlphabetList: {AlphabetList}\n\n')
    # print(f'RawResponse: {RawResponse}\n\n')
    
    if NotSameAlphabet != []:
        for _ in range(5):
            # Response 생성
            Response, Usage, Model = LLMresponse(projectName, email, Process, Input, 0, Mode = "Master", MemoryCounter = memoryCounter, messagesReview = MessagesReview)
            ResponseJson = VoiceTimeStempsProcessFilter(Response, NotSameAlphabet, lastNumber, NumberWordList)
            
            if isinstance(ResponseJson, str):
                print(f"Project: {projectName} | Process: {Process} | {ResponseJson}")
            else:
                ResponseJson += RawResponse
                ResponseJson = sorted(ResponseJson, key = lambda x: x['알파벳'])
                break
    else:
        ResponseJson = RawResponse
        
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
        range_end = 0.35 if not detail else 0.05  # 세밀한 분석을 위한 범위 조정

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
def VoiceSplit(projectName, email, name, VoiceLayerPath, SplitSents, LanguageCode = "ko-KR", MessagesReview = "off"):

    print(f"VoiceSplit: progress, {name} waiting 15 second")
    ## 음성파일을 STT로 단어별 시간 계산하기
    voiceTimeStemps, SplitWords = VoiceTimeStemps(VoiceLayerPath, LanguageCode)
    ## VoiceSplit 프롬프트 요청
    ResponseJson = VoiceSplitProcess(projectName, email, SplitSents, SplitWords, Process = "VoiceSplit", MessagesReview = MessagesReview)
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