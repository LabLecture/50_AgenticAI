# 회사PC에 OpenClaw 설치하기
https://codingopera.tistory.com/86#google_vignette

## 1. WSL 2 (Windows Subsystem for Linux) 설치

## 2. Node.js를 설치하려고 하는데, 이건 WSL의 Ubuntu에서 설치하는 건가?
내용을 기초로 openclaw를 회사PC에 설치하려고 해. 
첫번째 WSL 2를 설치했고, Node.js를 설치하려고 하는데, 이건 WSL의 Ubuntu에서 설치하는 건가?

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

## 3. Chocolatey (패키지 매니저) windows 설치
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

## 4. Google Gemini API 발급 (기존에 했음)
https://aistudio.google.com/u/1/prompts/new_chat

## 5. OpenClaw 설치 단계 (windows)
