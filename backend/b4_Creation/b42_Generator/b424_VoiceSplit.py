import io
import os
import sys
sys.path.append("/yaas")

from backend.b2_Solution.b24_DataFrame.b241_DataCommit.b2411_LLMLoad import LoadLLMapiKey, LLMresponse
from google.cloud import speech
from pydub import AudioSegment

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

def VoiceTimeStempsClassification(projectName, email, Input1, Input2, Process = "VoiceSplit"):
    Input = "<낭독문>\n" + str(Input1) + "\n\n" + "<낭독기록>\n" + str(Input2)
    print(Input)
    TimeStempsClassification = LLMresponse(projectName, email, Process, Input, 0)
    print(TimeStempsClassification)
# # 오디오 파일 로드
# audio = AudioSegment.from_wav("/yaas/storage/s1_Yeoreum/s14_VoiceStorage/156_준호(중간톤).wav")

# # 0.8초까지의 오디오 추출 (pydub에서 시간은 밀리초 단위로 취급됩니다)
# cut_audio = audio[:2900]

# # 추출한 오디오 저장
# cut_audio.export("/yaas/storage/s1_Yeoreum/s14_VoiceStorage/156_준호_cut.wav", format="wav")

# from pydub import AudioSegment
# from pydub.silence import detect_nonsilent

# # 오디오 파일 로드
# audio = AudioSegment.from_wav("/yaas/storage/s1_Yeoreum/s14_VoiceStorage/156_준호(중간톤).wav")

# # 비정적인 부분, 즉 소리가 있는 구간 찾기
# # min_silence_len은 정적으로 간주할 최소 길이 (밀리초),
# # silence_thresh는 소리 수준이 이 값보다 낮을 때 정적으로 간주 (-dBFS)
# nonsilent_chunks = detect_nonsilent(
#     audio,
#     min_silence_len=50,  # 정적으로 간주할 최소 길이: 1000ms = 1초
#     silence_thresh=-40    # 정적으로 간주할 소리 수준: -40 dBFS
# )

# # 소리가 있는 구간의 시작과 끝 시간 출력
# for start, end in nonsilent_chunks:
#     print(f"Start: {start} ms, End: {end} ms")

if __name__ == "__main__":

    ############################ 하이퍼 파라미터 설정 ############################
    email = "yeoreum00128@gmail.com"
    projectName = "웹3.0메타버스"
    voiceDataSet = "TypeCastVoiceDataSet"
    mainLang = 'Ko'
    mode = "Manual"
    macro = "Manual"
    #########################################################################
    voiceTimeStemps, Input2 = VoiceTimeStemps("/yaas/storage/s1_Yeoreum/s14_VoiceStorage/테스트(가)_0_지훈(일반, 피치다운).wav", 'ko-KR')
    Input1 = [{'낭독문장번호': 1, '낭독문장': '뿐만 아니라, 여름은 최근 창업진흥원에서 주관하는 대회에서 대상을 수상하며, 그들의 혁신적인 기술과 사회적 기여를 인정받았다.'}, {'낭독문장번호': 2, '낭독문장': '이준영 대표는 수상 소감에서 "이 상은 단지 우리의 기술적 성과만을 인정하는 것이 아니라, 우리가 추구하는 가치와 비전에 대한 공감을 의미합니다.'}, {'낭독문장번호': 3, '낭독문장': '우리는 앞으로도 지식의 접근성을 높이고, 누구나 쉽게 지식을 소비할 수 있는 환경을 만드는 것을 목표로 삼고 있습니다.'}, {'낭독문장번호': 4, '낭독문장': '라고 전했다.'}]
    VoiceTimeStempsClassification(projectName, email, Input1, Input2, Process = "VoiceSplit")
    