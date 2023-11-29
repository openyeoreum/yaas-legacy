import bcrypt
import pytz
from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

### 데이터베이스 시간을 서울로 지정하는 함수
def SeoulNow():

    return datetime.now(pytz.timezone('Asia/Seoul'))

### Password를 hash화 하는 함수
def HashPassword(password: str) -> bytes:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
 
    return hashed

### 해시된 비밀번호와 사용자 입력 비밀번호를 비교하는 함수
def CheckPassword(HashedPassword: bytes, UserPassword: str) -> bool:

    return bcrypt.checkpw(UserPassword.encode('utf-8'), HashedPassword)


#################
### UserFrame ###
#################
class User(Base):
    __tablename__ = "Users"

    UserId = Column(String(64), primary_key=True)
    UserDate = Column(DateTime, default=SeoulNow)
    Email = Column(String)
    _password = Column("Password", String(128))
    
    def SetPassword(self, password: str):
        self._password = HashPassword(password)

    def VerifyPassword(self, password: str) -> bool:

        return CheckPassword(self._password.encode('utf-8'), password)
    
    UserName = Column(String(64))
    UserPath = Column(Text)
    ProfileImagePath = Column(Text)

    TTSapiKey = Column(Text)
    LLMapiKey = Column(Text)
    
    history = relationship("UserHistory", backref="user")
    
class UserHistory(Base):
    __tablename__ = "UserHistorys"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    
    UserHistoryId = Column(Integer, primary_key=True, autoincrement=True)
    UserHistoryDate = Column(DateTime, default=SeoulNow)
    Email = Column(String)
    _password = Column("Password", String(128))
    
    def SetPassword(self, password: str):
        self._password = HashPassword(password)

    def VerifyPassword(self, password: str) -> bool:

        return CheckPassword(self._password.encode('utf-8'), password)
    
    UserName = Column(String(64))
    UserPath = Column(Text)
    ProfileImagePath = Column(Text)
    
    TTSapiKey = Column(Text)
    LLMapiKey = Column(Text)


#########################
### SubscriptionFrame ###
#########################
class Subscription(Base):
    __tablename__ = "Subscriptions"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    
    SubscriptionId = Column(Integer, primary_key=True, autoincrement=True)
    SubscriptionDate = Column(DateTime, default=SeoulNow)
    SubscriptionStatus = Column(String(64))
    SubscriptionAmount = Column(Integer)
    PaymentMethod = Column(String(128))
    
    history = relationship("SubscriptionHistory", backref="subscription")
    
class SubscriptionHistory(Base):
    __tablename__ = "SubscriptionHistorys"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    SubscriptionId = Column(Integer, ForeignKey('Subscriptions.SubscriptionId'))
    
    SubscriptionHistoryId = Column(Integer, primary_key=True, autoincrement=True)
    SubscriptionHistoryData = Column(DateTime, default=SeoulNow)
    SubscriptionStatus = Column(String(64))
    SubscriptionAmount = Column(Integer)
    PaymentMethod = Column(String(128))

### ProjectsStorageFrame
class ProjectsStorage(Base):
    __tablename__ = "ProjectsStorages"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    
    ProjectsStorageId = Column(Integer, primary_key=True, autoincrement=True)
    ProjectsStorageDate = Column(DateTime, default=SeoulNow)
    ProjectsStorageName = Column(String(64))
    ProjectsStoragePath = Column(Text)
    
    history = relationship("ProjectsStorageHistory", backref="projectsstorage")
    
class ProjectsStorageHistory(Base):
    __tablename__ = "ProjectsStorageHistorys"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    ProjectsStorageId = Column(Integer, ForeignKey('ProjectsStorages.ProjectsStorageId'))
    
    ProjectsStorageHistoryId = Column(Integer, primary_key=True, autoincrement=True)
    ProjectsStorageHistoryDate = Column(DateTime, default=SeoulNow)
    ProjectsStorageName = Column(String(64))
    ProjectsStoragePath = Column(Text)


####################
### ProjectFrame ###
####################
class Project(Base):
    __tablename__ = "Projects"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    ProjectsStorageId = Column(Integer, ForeignKey('ProjectsStorages.ProjectsStorageId'))

    ProjectId = Column(Integer, primary_key=True, autoincrement=True)
    ProjectDate = Column(DateTime, default=SeoulNow)
    ProjectName = Column(String(64))
    ProjectPath = Column(Text)

    ## Files
    # ScriptFile
    ScriptPath = Column(Text)
    
    IndexFile = Column(Text)
    CharacterFile = Column(Text)
    BodyFile = Column(Text)
    
    # DataFrameFile
    DataFramePath = Column(Text)
    
    # MixedAudioBookFile
    MixedAudioBookPath = Column(Text)

    VoiceLayersPath = Column(Text)
    NarratorPath = Column(Text)
    Character1Path = Column(Text)
    Character2Path = Column(Text)
    Character3Path = Column(Text)
    Character4Path = Column(Text)
    
    SFXLayersPath = Column(Text)
    SFX1Path = Column(Text)
    SFX2Path = Column(Text)
    SFX3Path = Column(Text)
    SFX4Path = Column(Text)
    SFX5Path = Column(Text)
    
    SoundLayersPath = Column(Text)
    BackgoundSoundPath = Column(Text)
    CaptionSoundPath = Column(Text)
    
    MusicLayersPath = Column(Text)
    Music1FolderPath = Column(Text)
    Music2FolderPath = Column(Text)
    
    # MasterAudioBookFile
    MasterAudioBookPath = Column(Text)
    
    AudioBookFile = Column(Text)
    
    ## Process
    # Text
    IndexText = Column(Text)
    CharacterText = Column(Text)
    BodyText = Column(Text)
    
    # Script
    IndexFrame = Column(JSON)
    PreprocessFrame = Column(JSON)
    BodyFrame = Column(JSON)
    HalfBodyFrame = Column(JSON)
    PhargraphCaptionFrame = Column(JSON)
    PhargraphTransitionFrame = Column(JSON)
    SummaryBodyFrame = Column(JSON)
    BodyContextTags = Column(JSON)
    NCEMContextTags = Column(JSON)
    CharacterContextTags = Column(JSON)
    SoundContextTags = Column(JSON)
    SFXContextTags = Column(JSON)
    
    # Context
    ContextDefine = Column(JSON)
    ContextCompletion = Column(JSON)
    NCEMDefine = Column(JSON)
    NCEMCompletion = Column(JSON)
    
    # Character
    CharacterDefine = Column(JSON)
    CharacterCompletion = Column(JSON)
    CharacterMultiQuery = Column(JSON)
    
    # Music
    MusicTagging = Column(JSON)
    MusicMultiQuery = Column(JSON)
    
    # Sound
    SoundTagging = Column(JSON)
    SoundMatching = Column(JSON)
    SoundMultiQuery = Column(JSON)
    
    # SFX
    SFXMatching = Column(JSON)
    SFXMultiQuery = Column(JSON)
    
    # MultiQuery
    CharacterMultiQuery = Column(JSON)
    SoundMultiQuery = Column(JSON)
    SFXMultiQuery = Column(JSON)
    
    # Translation
    TranslationKo = Column(JSON)
    TranslationEn = Column(JSON)
    TranslationJa = Column(JSON)
    TranslationZh = Column(JSON)
    TranslationEs = Column(JSON)
    
    # Correction
    CorrectionKo = Column(JSON)
    CorrectionEn = Column(JSON)
    CorrectionJa = Column(JSON)
    CorrectionZh = Column(JSON)
    CorrectionEs = Column(JSON)
    
    # Selection-Generation
    VoiceGenerationKo = Column(JSON)
    VoiceGenerationEn = Column(JSON)
    VoiceGenerationJa = Column(JSON)
    VoiceGenerationZh = Column(JSON)
    VoiceGenerationEs = Column(JSON)
    MusicSelection = Column(JSON)
    SoundSelection = Column(JSON)
    SFXSelectionKo = Column(JSON)
    SFXSelectionEn = Column(JSON)
    SFXSelectionJa = Column(JSON)
    SFXSelectionZh = Column(JSON)
    SFXSelectionEs = Column(JSON)
    
    # Mixing-Mastering
    MixingMasteringKo = Column(JSON)
    MixingMasteringEn = Column(JSON)
    MixingMasteringJa = Column(JSON)
    MixingMasteringZh = Column(JSON)
    MixingMasteringEs = Column(JSON)
    
    history = relationship("ProjectHistory", backref="project")

class ProjectHistory(Base):
    __tablename__ = "ProjectHistorys"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    ProjectsStorageId = Column(Integer, ForeignKey('ProjectsStorages.ProjectsStorageId'))
    ProjectId = Column(Integer, ForeignKey('Projects.ProjectId'))
    
    ProjectHistoryId = Column(Integer, primary_key=True, autoincrement=True)
    ProjectDate = Column(DateTime, default=SeoulNow)
    ProjectName = Column(String(64))
    ProjectPath = Column(Text)

    ## Files
    # ScriptFile
    ScriptPath = Column(Text)
    
    IndexFile = Column(Text)
    CharacterFile = Column(Text)
    BodyFile = Column(Text)
    
    # MixedAudioBookFile
    MixedAudioBookPath = Column(Text)

    VoiceLayersPath = Column(Text)
    NarratorPath = Column(Text)
    Character1Path = Column(Text)
    Character2Path = Column(Text)
    Character3Path = Column(Text)
    Character4Path = Column(Text)
    
    SFXLayersPath = Column(Text)
    SFX1Path = Column(Text)
    SFX2Path = Column(Text)
    SFX3Path = Column(Text)
    SFX4Path = Column(Text)
    SFX5Path = Column(Text)
    
    SoundLayersPath = Column(Text)
    BackgoundSoundPath = Column(Text)
    CaptionSoundPath = Column(Text)
    
    MusicLayersFolderPath = Column(Text)
    Music1FolderPath = Column(Text)
    Music2FolderPath = Column(Text)
    
    # MasterAudioBookFile
    MasterAudioBookPath = Column(Text)
    
    AudioBookFile = Column(Text)
    
    ## Process
    # Script
    IndexFrameStatus = Column(String(64))
    PreprocessFrameStatus = Column(String(64))
    BodyFrameStatus = Column(String(64))
    HalfBodyFrameStatus = Column(String(64))
    PhargraphCaptionFrameStatus = Column(String(64))
    PhargraphTransitionFrameStatus = Column(String(64))
    SummaryBodyFrameStatus = Column(String(64))
    BodyContextTagsStatus = Column(String(64))
    NCEMContextTagsStatus = Column(String(64))
    CharacterContextTagsStatus = Column(String(64))
    SoundContextTagsStatus = Column(String(64))
    SFXContextTagsStatus = Column(String(64))
    
    # Context
    ContextDefineStatus = Column(JSON(64))
    ContextCompletionStatus = Column(JSON(64))
    NCEMDefineStatus = Column(JSON(64))
    NCEMCompletionStatus = Column(JSON(64))
    
    # Character
    CharacterDefineStatus = Column(JSON(64))
    CharacterCompletionStatus = Column(JSON(64))
    CharacterMultiQueryStatus = Column(JSON(64))
    
    # Music
    MusicTaggingStatus = Column(JSON(64))
    MusicMultiQueryStatus = Column(JSON(64))
    
    # Sound
    SoundTaggingStatus = Column(JSON(64))
    SoundMatchingStatus = Column(JSON(64))
    SoundMultiQueryStatus = Column(JSON(64))
    
    # SFX
    SFXMatchingStatus = Column(JSON(64))
    SFXMultiQueryStatus = Column(JSON(64))
    
    # MultiQuery
    CharacterMultiQueryStatus = Column(String(64))
    SoundMultiQueryStatus = Column(String(64))
    SFXMultiQueryStatus = Column(String(64))
    
    # Translation
    TranslationKoStatus = Column(String(64))
    TranslationEnStatus = Column(String(64))
    TranslationJaStatus = Column(String(64))
    TranslationZhStatus = Column(String(64))
    TranslationEsStatus = Column(String(64))
    
    # Correction
    CorrectionKoStatus = Column(String(64))
    CorrectionEnStatus = Column(String(64))
    CorrectionJaStatus = Column(String(64))
    CorrectionZhStatus = Column(String(64))
    CorrectionEsStatus = Column(String(64))
    
    # Selection-Generation
    VoiceGenerationKoStatus = Column(String(64))
    VoiceGenerationEnStatus = Column(String(64))
    VoiceGenerationJaStatus = Column(String(64))
    VoiceGenerationZhStatus = Column(String(64))
    VoiceGenerationEsStatus = Column(String(64))
    MusicSelectionStatus = Column(String(64))
    SoundSelectionStatus = Column(String(64))
    SFXSelectionKoStatus = Column(String(64))
    SFXSelectionEnStatus = Column(String(64))
    SFXSelectionJaStatus = Column(String(64))
    SFXSelectionZhStatus = Column(String(64))
    SFXSelectionEsStatus = Column(String(64))
    
    # Mixing-Mastering
    MixingMasteringKoStatus = Column(String(64))
    MixingMasteringEnStatus = Column(String(64))
    MixingMasteringJaStatus = Column(String(64))
    MixingMasteringZhStatus = Column(String(64))
    MixingMasteringEsStatus = Column(String(64))


###################
### PromptFrame ###
###################
class Prompt(Base):
    __tablename__ = "Prompts"

    PromptId = Column(Integer, primary_key=True, autoincrement=True)
    PromptDate = Column(DateTime, default=SeoulNow)

    # ScriptPrompt
    IndexDefinePreprocess = Column(JSON)
    IndexDefineDivisionPreprocess = Column(JSON)
    IndexDefine = Column(JSON)
    # PreprocessBody = Column(JSON)
    CaptionPhargraph = Column(JSON)
    TransitionPhargraph = Column(JSON)
    BodySummary = Column(JSON)
    TransitionPhargraph = Column(JSON)
    
    # ContextPrompt
    ContextDefine = Column(JSON)
    ContextCompletion = Column(JSON)
    NCEMDefine = Column(JSON)
    NCEMCompletion = Column(JSON)

    # CharacterPrompt
    CharacterDefine = Column(JSON)
    CharacterCompletion = Column(JSON)
    # CharacterMultiQuery = Column(JSON)
    
    # # MusicPrompt
    # MusicTagging = Column(JSON)
    # MusicMultiQuery = Column(JSON)
    
    # # SoundPrompt
    # SoundTagging = Column(JSON)
    # SoundMatching = Column(JSON)
    # SoundMultiQuery = Column(JSON)
    
    # SFXPrompt
    SFXMatching = Column(JSON)
    SFXMultiQuery = Column(JSON)
    
    # TranslationPrompt
    TranslationKo = Column(JSON)
    # TranslationEn = Column(JSON)
    # TranslationJa = Column(JSON)
    # TranslationZh = Column(JSON)
    # TranslationEs = Column(JSON)
    
    # CorrectionPrompt
    CorrectionKo = Column(JSON)
    # CorrectionEn = Column(JSON)
    # CorrectionJa = Column(JSON)
    # CorrectionZh = Column(JSON)
    # CorrectionEs = Column(JSON)
    
    # # Selection-GenerationPrompt
    # VoiceGenerationKo = Column(JSON)
    # VoiceGenerationEn = Column(JSON)
    # VoiceGenerationJa = Column(JSON)
    # VoiceGenerationZh = Column(JSON)
    # VoiceGenerationEs = Column(JSON)
    
    # MusicSelection = Column(JSON)
    # SoundSelection = Column(JSON)
    
    # SFXSelectionKo = Column(JSON)
    # SFXSelectionEn = Column(JSON)
    # SFXSelectionJa = Column(JSON)
    # SFXSelectionZh = Column(JSON)
    # SFXSelectionEs = Column(JSON)
    
    # # Mixing-MasteringPrompt
    # MixingMasteringKo = Column(JSON)
    # MixingMasteringEn = Column(JSON)
    # MixingMasteringJa = Column(JSON)
    # MixingMasteringZh = Column(JSON)
    # MixingMasteringEs = Column(JSON)


#######################
### TrainingDataset ###
#######################
class TrainingDataset(Base):
    __tablename__ = "TrainingDatasets"
    
    UserId = Column(String(64), ForeignKey('Users.UserId'))
    ProjectsStorageId = Column(Integer, ForeignKey('ProjectsStorages.ProjectsStorageId'))
    ProjectId = Column(Integer, ForeignKey('Projects.ProjectId'))
    ProjectName = Column(String(64))

    TrainingDatasetId = Column(Integer, primary_key=True, autoincrement=True)
    TrainingDatasetDate = Column(DateTime, default=SeoulNow)

    # ScriptDataset
    IndexDefinePreprocess = Column(JSON)
    IndexDefineDivisionPreprocess = Column(JSON)
    IndexDefine = Column(JSON)
    PreprocessBody = Column(JSON)
    CaptionPhargraph = Column(JSON)
    TransitionPhargraph = Column(JSON)
    BodySummary = Column(JSON)
    TransitionPhargraph = Column(JSON)
    
    # ContextDataset
    ContextDefine = Column(JSON)
    ContextCompletion = Column(JSON)
    NCEMDefine = Column(JSON)
    NCEMCompletion = Column(JSON)

    # CharacterDataset
    CharacterDefine = Column(JSON)
    CharacterCompletion = Column(JSON)
    # CharacterMultiQuery = Column(JSON)
    
    # # MusicDataset
    # MusicTagging = Column(JSON)
    # MusicMultiQuery = Column(JSON)
    
    # # SoundDataset
    # SoundTagging = Column(JSON)
    # SoundMatching = Column(JSON)
    # SoundMultiQuery = Column(JSON)
    
    # SFXDataset
    SFXMatching = Column(JSON)
    SFXMultiQuery = Column(JSON)

    # MultiQueryDataset
    CharacterMultiQuery = Column(JSON)
    SoundMultiQuery = Column(JSON)
    SFXMultiQuery = Column(JSON)
    
    # TranslationDataset
    TranslationKo = Column(JSON)
    TranslationEn = Column(JSON)
    TranslationJa = Column(JSON)
    TranslationZh = Column(JSON)
    TranslationEs = Column(JSON)
    
    # CorrectionDataset
    CorrectionKo = Column(JSON)
    CorrectionEn = Column(JSON)
    CorrectionJa = Column(JSON)
    CorrectionZh = Column(JSON)
    CorrectionEs = Column(JSON)
    
    # # Selection-GenerationDataset
    # VoiceGenerationKo = Column(JSON)
    # VoiceGenerationEn = Column(JSON)
    # VoiceGenerationJa = Column(JSON)
    # VoiceGenerationZh = Column(JSON)
    # VoiceGenerationEs = Column(JSON)
    
    # MusicSelection = Column(JSON)
    # SoundSelection = Column(JSON)
    
    # SFXSelectionKo = Column(JSON)
    # SFXSelectionEn = Column(JSON)
    # SFXSelectionJa = Column(JSON)
    # SFXSelectionZh = Column(JSON)
    # SFXSelectionEs = Column(JSON)
    
    # # Mixing-MasteringDataset
    # MixingMasteringKo = Column(JSON)
    # MixingMasteringEn = Column(JSON)
    # MixingMasteringJa = Column(JSON)
    # MixingMasteringZh = Column(JSON)
    # MixingMasteringEs = Column(JSON)


#####################
### VoiceDatabase ###
#####################
class Voice(Base):
    __tablename__ = "Voices"

    VoiceId = Column(Integer, primary_key=True, autoincrement=True)
    VoiceDate = Column(DateTime, default=SeoulNow)
    VoiceName = Column(String(64))
    
    # VoiceGeneralPointTag
    Genre = Column(String(64))
    Gender = Column(String(64))
    Age = Column(Integer)
    Personality = Column(String(64))
    Emotion = Column(String(64))
    
    # VoiceOptionTag
    TTSPlatform = Column(String(64))
    TTSName = Column(String(64))
    TTSEmotion = Column(String(64))
    TTSLanguage = Column(String(64))
    TTSSpeed = Column(Float)
    TTSPitch = Column(Integer)
    

#####################
### MusicDatabase ###
#####################
class Music(Base):
    __tablename__ = "Musics"

    MusicId = Column(Integer, primary_key=True, autoincrement=True)
    MusicDate = Column(DateTime, default=SeoulNow)
    MusicName = Column(String(64))
    MusicFile = Column(Text)
    Seconds = Column(Float)
    
    # MusicGeneralPointTag
    Genre = Column(String(64))
    Gender = Column(String(64))
    Age = Column(Integer)
    Personality = Column(String(64))
    Emotion = Column(String(64))
    
    # MusicSituationPointTag
    Environment = Column(String(64))
    Situation = Column(String(64))
    Era = Column(String(64))
    Culture = Column(String(64))
    
    # MusicClassificationTag
    LoopMusic = Column(String(16))
    TitleMusic = Column(String(16))
    TitleMusic = Column(String(16))
    PartMusic = Column(String(16))
    ChapterMusic = Column(String(16))


#####################
### SoundDatabase ###
#####################
class Sound(Base):
    __tablename__ = "Sounds"

    SoundId = Column(Integer, primary_key=True, autoincrement=True)
    SoundDate = Column(DateTime, default=SeoulNow)
    SoundName = Column(String(64))
    SoundFile = Column(Text)
    Seconds = Column(Float)
    
    # SoundGeneralPointTag
    Genre = Column(String(64))
    Gender = Column(String(64))
    Age = Column(Integer)
    Personality = Column(String(64))
    Emotion = Column(String(64))
    
    # SoundSituationPointTag
    Environment = Column(String(64))
    Situation = Column(String(64))
    Era = Column(String(64))
    Culture = Column(String(64))
    
    # SoundClassificationTag
    IndexSound = Column(String(16))
    CaptionSound = Column(String(16))


####################
### LoopDatabase ###
####################
class Loop(Base):
    __tablename__ = "Loops"

    LoopId = Column(Integer, primary_key=True, autoincrement=True)
    LoopDate = Column(DateTime, default=SeoulNow)
    LoopName = Column(String(64))
    LoopFile = Column(Text)
    Seconds = Column(Float)
    
    # LoopGeneralPointTag
    Genre = Column(String(64))
    Gender = Column(String(64))
    Age = Column(Integer)
    Personality = Column(String(64))
    Emotion = Column(String(64))
    
    # LoopSituationPointTag
    Environment = Column(String(64))
    Situation = Column(String(64))
    Era = Column(String(64))
    Culture = Column(String(64))
    
    # LoopClassificationTag
    EnvSound = Column(String(16))
    BGM = Column(String(16))


###################
### SFXDatabase ###
###################
class SFX(Base):
    __tablename__ = "SFXs"

    SFXId = Column(Integer, primary_key=True, autoincrement=True)
    SFXDate = Column(DateTime, default=SeoulNow)
    SFXName = Column(String(64))
    SFXpFile = Column(Text)
    Seconds = Column(Float)
    
    # SFXGeneralPointTag
    Genre = Column(String(64))
    Gender = Column(String(64))
    Age = Column(Integer)
    Personality = Column(String(64))
    Emotion = Column(String(64))
    
    # SFXSituationPointTag
    Environment = Column(String(64))
    Situation = Column(String(64))
    Era = Column(String(64))
    Culture = Column(String(64))
    
    # SFXClassificationTag
    Action = Column(String(16))
    Tools = Column(String(16))
    ArtificialObjects = Column(String(16))
    NatureObjects = Column(String(16))
    SpaceElements = Column(String(16))
    environment = Column(String(16))
    situation = Column(String(16))
    SoundEffects = Column(String(16))
    ETC = Column(String(16))