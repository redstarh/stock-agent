#!/usr/bin/env python3
"""
Sprint 생성 및 이슈 할당
"""

import requests
from requests.auth import HTTPBasicAuth
from jira_config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY

def get_board_id():
    """Board ID 조회"""
    url = f"{JIRA_URL}/rest/agile/1.0/board"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

    params = {'projectKeyOrId': JIRA_PROJECT_KEY}
    response = requests.get(url, auth=auth, params=params)

    if response.status_code == 200:
        boards = response.json()['values']
        if boards:
            return boards[0]['id']
    return None

def create_sprint(board_id: int, sprint_name: str, goal: str = ''):
    """Sprint 생성"""
    url = f"{JIRA_URL}/rest/agile/1.0/sprint"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {'Content-Type': 'application/json'}

    payload = {
        'name': sprint_name,
        'goal': goal,
        'originBoardId': board_id
    }

    response = requests.post(url, auth=auth, headers=headers, json=payload)

    if response.status_code == 201:
        sprint = response.json()
        print(f"✓ Sprint 생성: {sprint_name} (ID: {sprint['id']})")
        return sprint['id']
    else:
        print(f"✗ Sprint 생성 실패: {sprint_name}")
        print(response.text)
        return None

def main():
    board_id = get_board_id()

    if not board_id:
        print("✗ Board를 찾을 수 없습니다.")
        return

    print(f"Board ID: {board_id}\n")

    # Sprint 생성
    sprints = [
        ('Sprint 1', '기반 구축: 환경 설정, DB, 인증'),
        ('Sprint 2', '핵심 거래: 계좌, 주문, 포트폴리오, Market Data'),
        ('Sprint 3', 'Frontend MVP: 인증, 주문, 포트폴리오, 차트'),
        ('Sprint 4', '실전 거래: Broker 연동, 리스크 관리'),
        ('Sprint 5', '고급 기능: 분석, 백테스팅, 배포')
    ]

    sprint_ids = []
    for name, goal in sprints:
        sprint_id = create_sprint(board_id, name, goal)
        if sprint_id:
            sprint_ids.append(sprint_id)

    print(f"\n✓ {len(sprint_ids)}개 Sprint 생성 완료")
    print("\nSprint IDs (환경 변수 업데이트):")
    for i, sid in enumerate(sprint_ids, 1):
        print(f"SPRINT_{i}_ID={sid}")

if __name__ == '__main__':
    main()
