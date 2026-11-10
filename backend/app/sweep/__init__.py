"""조합 탐색. 전략의 파라미터·기간 조합을 여러 개 백테스트하고 결과 요약을 계속 쌓는다.

저장 위치는 `backend/sweeps/<전략 id>/`이다.

    results.jsonl         조합 하나당 한 줄. 정의, 성과 요약, 일별 자산
    trades/<id>.jsonl     조합의 거래(`trade`)와 체결(`fill`) 기록
"""
