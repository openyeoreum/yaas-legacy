# arm64v8 아키텍처와 Ubuntu를 기본 이미지로 사용
FROM arm64v8/ubuntu:latest

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul

# 시간대를 서울로 설정
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 필요한 툴 설치
RUN apt-get update -q && \
    apt-get install -yq git curl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 파이썬 설치
RUN apt-get update -q && \
    apt-get install -yq python3 python3-pip && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Node.js 설치
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get update -q && \
    apt-get install -yq nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉터리 설정
WORKDIR /yaas

# 현재 디렉터리의 내용을 컨테이너에 복사
COPY . .

# ".DS_Store" 삭제
RUN rm -f /yaas/backend/600000_Database/610000_DataBaseVolumes/.DS_Store

# backend/requirements.txt에서 파이썬 패키지 설치
RUN pip install --no-cache-dir -r backend/requirements.txt

# Svelte 설치 및 서버실행
# Vite 프로젝트 생성
RUN echo "y" | npm init vite@latest frontend -- --template svelte

# frontend 디렉터리로 이동
WORKDIR /yaas/frontend

# 의존성 설치
RUN sleep 5 && npm install

# jsconfig.json에서 "checkJs": true를 false로 변경
RUN sed -i 's/"checkJs": true/"checkJs": false/' jsconfig.json

# "npm run dev"를 기본 명령으로 설정
CMD ["npm", "run", "dev"]