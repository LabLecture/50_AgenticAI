# youtube_mcp_server.py 소스
import re
import sys 
from mcp.server.fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi

# [1]. FastMCP 프레임워크 초기화
mcp = FastMCP("YouTube Summarizer") # 서버 이름을 지정하면 클라이언트 연결 시 식별자로 사용

def extract_video_id(url: str) -> str:
    """유튜브 URL에서 비디오 고유 ID(11자리)를 추출하는 유틸리티 함수"""
    pattern = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(pattern, url)
    return match.group(1) if match else None

# [2]. MCP 도구(Tool) 등록
# @mcp.tool() 데코레이터는 아래 함수를 AI가 호출 가능한 '도구'로 변환.
# 함수의 Docstring(주석)은 AI가 "이 도구를 언제 써야 할지" 판단하는 설명서로 필수
@mcp.tool()
def get_youtube_transcript(video_url: str) -> str:
    """유튜브 URL을 입력받아 해당 영상의 자막 전체를 추출합니다."""
    
    video_id = extract_video_id(video_url)
    if not video_id:
        return "에러: 유효한 유튜브 URL이 아닙니다."

    try:
        ytt_api = YouTubeTranscriptApi()            # 인스턴스 생성
        transcript_list = ytt_api.list(video_id)    # 자막 목록 조회
        
        try:
            transcript = transcript_list.find_generated_transcript(['ko'])
        except:
            transcript = list(transcript_list)[0]
            
        data = transcript.fetch()   # 실제 자막 텍스트 데이터 획득 
        
        texts = []
        for item in data:
            if hasattr(item, 'text'):
                texts.append(item.text)
            else:
                texts.append(item['text'])
        
        full_text = " ".join(texts)

        return full_text if full_text.strip() else "자막 내용이 비어 있습니다."
    
    except Exception as e:
        return f"자막 추출 실패: {str(e)}"

if __name__ == "__main__":      
    mcp.run()       # MCP 서버 실행