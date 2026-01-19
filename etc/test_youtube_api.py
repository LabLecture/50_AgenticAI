# test_youtube_api.py (수정본)
from youtube_transcript_api import YouTubeTranscriptApi

try:
    video_id = "fToUPQ_WRaY"
    
    print("=== 새로운 API 방식으로 테스트 ===\n")
    
    # list() 메서드로 자막 목록 가져오기
    print("1. 자막 목록 가져오기...")
    ytt_api = YouTubeTranscriptApi()
    transcript_list = ytt_api.list(video_id)
    
    print(f"✅ 사용 가능한 자막 객체: {transcript_list}")
    print(f"타입: {type(transcript_list)}\n")
    
    # TranscriptList는 iterable이므로 리스트로 변환하거나 반복문 사용
    transcripts = list(transcript_list)  # 리스트로 변환
    print(f"자막 개수: {len(transcripts)}\n")
    
    for i, t in enumerate(transcripts):
        print(f"  [{i}] {t.language} ({t.language_code}) - 자동생성: {t.is_generated}")
    
    # 첫 번째 자막 가져오기
    if transcripts:
        print(f"\n2. 첫 번째 자막 fetch() 실행...")
        first_transcript = transcripts[0]
        print(f"선택된 자막: {first_transcript.language} ({first_transcript.language_code})")
        
        data = first_transcript.fetch()
        
        print(f"✅ 성공! 자막 수: {len(data)}")
        print(f"첫 번째 자막: {data[0]}")
        print(f"\n전체 텍스트 (앞 200자):")
        full_text = " ".join([item.text for item in data])
        print(full_text[:200])
    else:
        print("❌ 사용 가능한 자막이 없습니다.")
    
except Exception as e:
    print(f"❌ 실패: {type(e).__name__} - {e}")
    import traceback
    traceback.print_exc()