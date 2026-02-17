# Jira Import 가이드

> **프로젝트 URL**: https://stockagent.atlassian.net/jira/software/projects/SCRUM/boards/1

---

## 📋 목차

1. [방법 1: CSV Import (수동)](#방법-1-csv-import-수동)
2. [방법 2: REST API (자동화)](#방법-2-rest-api-자동화)
3. [API Token 생성](#api-token-생성)
4. [Python 스크립트](#python-스크립트)
5. [문제 해결](#문제-해결)

---

## 방법 1: CSV Import (수동)

### Step 1: Jira 프로젝트 설정 확인

```bash
# 프로젝트 정보
Project: SCRUM
Board: https://stockagent.atlassian.net/jira/software/projects/SCRUM/boards/1
```

### Step 2: CSV 파일 준비

```bash
# CSV 파일 위치
/Users/redstar/AgentDev/jira-import.csv

# 인코딩 확인 (UTF-8이어야 함)
file -I jira-import.csv
```

### Step 3: Jira CSV Import UI 사용

#### 3-1. Settings 접근

1. **Jira 프로젝트 페이지 접속**
   ```
   https://stockagent.atlassian.net/jira/software/projects/SCRUM
   ```

2. **프로젝트 설정 이동**
   - 왼쪽 사이드바 하단 → `Project settings` 클릭
   - 또는 URL: `https://stockagent.atlassian.net/jira/software/projects/SCRUM/settings`

#### 3-2. External System Import

⚠️ **중요**: Jira Cloud는 CSV direct import를 지원하지 않습니다.
대신 **Jira Importer** 앱을 사용하거나 **REST API**를 사용해야 합니다.

#### 3-3. Jira Importer 앱 사용

1. **Marketplace에서 앱 설치**
   ```
   Settings → Apps → Find new apps → "CSV Importer"
   ```

2. **추천 앱**:
   - **CSV & Excel Importer** (무료 트라이얼)
   - **Advanced Roadmaps** (내장, Epic 관리)

3. **Import 실행**
   - Apps → CSV Importer → Upload CSV
   - 필드 매핑 확인
   - Preview → Import

---

## 방법 2: REST API (자동화) ⭐ 추천

### 장점
- ✅ 완전 자동화
- ✅ Epic Link 자동 설정
- ✅ Sprint 자동 할당
- ✅ 에러 처리
- ✅ 재실행 가능

---

## API Token 생성

### Step 1: Atlassian 계정 설정

1. **Atlassian 계정 페이지 접속**
   ```
   https://id.atlassian.com/manage-profile/security/api-tokens
   ```

2. **API Token 생성**
   - `Create API token` 클릭
   - Label: `Trading System Import` (설명용)
   - `Create` 클릭
   - ⚠️ **토큰 복사 (한 번만 표시됨)**

3. **토큰 안전하게 저장**
   ```bash
   # 환경 변수로 저장
   echo "export JIRA_API_TOKEN='your-token-here'" >> ~/.zshrc
   source ~/.zshrc
   ```

### Step 2: 사용자 이메일 확인

```bash
# Jira 로그인 이메일 주소
# 예: your-email@example.com
```

---

## Python 스크립트

### 파일 구조

```
AgentDev/
├── jira-import.csv           # CSV 데이터
├── jira_import.py            # Import 스크립트
├── jira_config.py            # 설정 파일
└── requirements.txt          # 의존성
```

### requirements.txt 생성

```bash
cat > requirements.txt << 'EOF'
requests==2.31.0
python-dotenv==1.0.0
pandas==2.1.0
EOF
```

### 환경 변수 파일 (.env)

```bash
cat > .env << 'EOF'
# Jira 설정
JIRA_URL=https://stockagent.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=SCRUM

# Sprint 설정 (선택)
SPRINT_1_ID=1
SPRINT_2_ID=2
SPRINT_3_ID=3
SPRINT_4_ID=4
SPRINT_5_ID=5
EOF
```

⚠️ **.gitignore에 추가**
```bash
echo ".env" >> .gitignore
```

---

## 스크립트 파일

### 1. jira_config.py

```python
"""
Jira 설정 및 유틸리티
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Jira 연결 정보
JIRA_URL = os.getenv('JIRA_URL', 'https://stockagent.atlassian.net')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'SCRUM')

# API 엔드포인트
API_BASE = f"{JIRA_URL}/rest/api/3"
ISSUE_ENDPOINT = f"{API_BASE}/issue"
SEARCH_ENDPOINT = f"{API_BASE}/search"

# 우선순위 매핑
PRIORITY_MAP = {
    'Highest': '1',
    'High': '2',
    'Medium': '3',
    'Low': '4',
    'Lowest': '5'
}

# 이슈 타입 매핑
ISSUE_TYPE_MAP = {
    'Epic': '10000',
    'Story': '10001',
    'Task': '10002',
    'Sub-task': '10003'
}

# 컴포넌트 매핑
COMPONENT_MAP = {
    'Backend': 'Backend',
    'Frontend': 'Frontend',
    'Infrastructure': 'Infrastructure',
    'Integration': 'Integration',
    'Analytics': 'Analytics',
    'QA': 'QA',
    'Data': 'Data'
}

def validate_config():
    """설정 검증"""
    if not JIRA_EMAIL:
        raise ValueError("JIRA_EMAIL이 설정되지 않았습니다.")
    if not JIRA_API_TOKEN:
        raise ValueError("JIRA_API_TOKEN이 설정되지 않았습니다.")
    print(f"✓ Jira URL: {JIRA_URL}")
    print(f"✓ Project: {JIRA_PROJECT_KEY}")
    print(f"✓ Email: {JIRA_EMAIL}")
```

---

### 2. jira_import.py

```python
#!/usr/bin/env python3
"""
Jira Issue Import Script
CSV 파일을 읽어서 Jira에 Epic, Story, Task를 생성합니다.
"""

import csv
import requests
from requests.auth import HTTPBasicAuth
import time
import json
from typing import Dict, List, Optional
import sys

from jira_config import (
    JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY,
    ISSUE_ENDPOINT, SEARCH_ENDPOINT, PRIORITY_MAP, ISSUE_TYPE_MAP,
    COMPONENT_MAP, validate_config
)


class JiraImporter:
    def __init__(self):
        validate_config()
        self.auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self.epic_map = {}  # Epic 이름 → Epic Key 매핑
        self.story_map = {}  # Story 이름 → Story Key 매핑

    def test_connection(self) -> bool:
        """Jira 연결 테스트"""
        try:
            response = requests.get(
                f"{JIRA_URL}/rest/api/3/myself",
                auth=self.auth,
                headers=self.headers
            )
            if response.status_code == 200:
                user = response.json()
                print(f"✓ Jira 연결 성공: {user.get('displayName')}")
                return True
            else:
                print(f"✗ Jira 연결 실패: {response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"✗ 연결 오류: {e}")
            return False

    def get_project_components(self) -> Dict[str, str]:
        """프로젝트 컴포넌트 ID 조회"""
        url = f"{JIRA_URL}/rest/api/3/project/{JIRA_PROJECT_KEY}/components"
        response = requests.get(url, auth=self.auth, headers=self.headers)

        if response.status_code == 200:
            components = response.json()
            return {c['name']: c['id'] for c in components}
        return {}

    def create_component_if_not_exists(self, component_name: str) -> Optional[str]:
        """컴포넌트가 없으면 생성"""
        existing = self.get_project_components()

        if component_name in existing:
            return existing[component_name]

        # 컴포넌트 생성
        url = f"{JIRA_URL}/rest/api/3/component"
        payload = {
            "name": component_name,
            "project": JIRA_PROJECT_KEY,
            "description": f"{component_name} component"
        }

        response = requests.post(
            url,
            auth=self.auth,
            headers=self.headers,
            json=payload
        )

        if response.status_code == 201:
            comp = response.json()
            print(f"  ✓ 컴포넌트 생성: {component_name}")
            return comp['id']
        else:
            print(f"  ✗ 컴포넌트 생성 실패: {component_name}")
            return None

    def create_issue(self, issue_data: Dict) -> Optional[str]:
        """이슈 생성"""
        issue_type = issue_data['Issue Type']
        summary = issue_data['Summary']

        # 기본 payload
        payload = {
            "fields": {
                "project": {"key": JIRA_PROJECT_KEY},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": issue_data.get('Description', '')
                                }
                            ]
                        }
                    ]
                },
                "issuetype": {"name": issue_type}
            }
        }

        # 우선순위
        if issue_data.get('Priority'):
            payload['fields']['priority'] = {
                'name': issue_data['Priority']
            }

        # Story Points (Custom Field - 확인 필요)
        if issue_data.get('Story Points'):
            try:
                # Story Points 필드는 프로젝트마다 다를 수 있음
                # customfield_10016이 일반적이지만 확인 필요
                payload['fields']['customfield_10016'] = int(issue_data['Story Points'])
            except:
                pass

        # Labels
        if issue_data.get('Labels'):
            labels = [l.strip() for l in issue_data['Labels'].split(';')]
            payload['fields']['labels'] = labels

        # Component
        if issue_data.get('Component'):
            comp_id = self.create_component_if_not_exists(issue_data['Component'])
            if comp_id:
                payload['fields']['components'] = [{'id': comp_id}]

        # Epic Link (Story/Task의 경우)
        if issue_type in ['Story', 'Task'] and issue_data.get('Epic Link'):
            epic_key = self.epic_map.get(issue_data['Epic Link'])
            if epic_key:
                # Epic Link는 customfield_10014가 일반적 (확인 필요)
                payload['fields']['customfield_10014'] = epic_key

        # Parent (Task의 경우 Story)
        if issue_type == 'Task' and issue_data.get('Epic Link'):
            # Task의 Epic Link 컬럼에 Story 이름이 있는 경우
            story_key = self.story_map.get(issue_data['Epic Link'])
            if story_key:
                payload['fields']['parent'] = {'key': story_key}

        # API 요청
        try:
            response = requests.post(
                ISSUE_ENDPOINT,
                auth=self.auth,
                headers=self.headers,
                json=payload
            )

            if response.status_code == 201:
                issue = response.json()
                issue_key = issue['key']
                print(f"  ✓ 생성: {issue_key} - {summary}")
                return issue_key
            else:
                print(f"  ✗ 실패: {summary}")
                print(f"    상태 코드: {response.status_code}")
                print(f"    응답: {response.text}")
                return None

        except Exception as e:
            print(f"  ✗ 오류: {summary} - {e}")
            return None

    def import_from_csv(self, csv_file: str):
        """CSV 파일에서 이슈 import"""
        print(f"\n📄 CSV 파일 읽기: {csv_file}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        print(f"총 {len(rows)}개 이슈 발견\n")

        # Phase 1: Epic 생성
        print("=" * 60)
        print("Phase 1: Epic 생성")
        print("=" * 60)

        epics = [row for row in rows if row['Issue Type'] == 'Epic']
        for epic in epics:
            issue_key = self.create_issue(epic)
            if issue_key:
                self.epic_map[epic['Summary']] = issue_key
            time.sleep(0.5)  # Rate limiting

        print(f"\n✓ Epic {len(self.epic_map)}개 생성 완료\n")

        # Phase 2: Story 생성
        print("=" * 60)
        print("Phase 2: Story 생성")
        print("=" * 60)

        stories = [row for row in rows if row['Issue Type'] == 'Story']
        for story in stories:
            issue_key = self.create_issue(story)
            if issue_key:
                self.story_map[story['Summary']] = issue_key
            time.sleep(0.5)

        print(f"\n✓ Story {len(self.story_map)}개 생성 완료\n")

        # Phase 3: Task 생성
        print("=" * 60)
        print("Phase 3: Task 생성")
        print("=" * 60)

        tasks = [row for row in rows if row['Issue Type'] == 'Task']
        task_count = 0
        for task in tasks:
            issue_key = self.create_issue(task)
            if issue_key:
                task_count += 1
            time.sleep(0.5)

        print(f"\n✓ Task {task_count}개 생성 완료\n")

        # 요약
        print("=" * 60)
        print("Import 완료!")
        print("=" * 60)
        print(f"Epic: {len(self.epic_map)}개")
        print(f"Story: {len(self.story_map)}개")
        print(f"Task: {task_count}개")
        print(f"\n프로젝트 URL: {JIRA_URL}/jira/software/projects/{JIRA_PROJECT_KEY}")


def main():
    """메인 함수"""
    csv_file = 'jira-import.csv'

    if not os.path.exists(csv_file):
        print(f"✗ CSV 파일이 없습니다: {csv_file}")
        sys.exit(1)

    importer = JiraImporter()

    # 연결 테스트
    if not importer.test_connection():
        print("\n✗ Jira 연결에 실패했습니다.")
        print("  1. JIRA_EMAIL이 올바른지 확인하세요.")
        print("  2. JIRA_API_TOKEN이 유효한지 확인하세요.")
        print("  3. 프로젝트 접근 권한이 있는지 확인하세요.")
        sys.exit(1)

    # 확인 프롬프트
    print("\n⚠️  Jira에 이슈를 생성합니다.")
    print(f"   프로젝트: {JIRA_PROJECT_KEY}")
    print(f"   URL: {JIRA_URL}")

    confirm = input("\n계속하시겠습니까? (yes/no): ")
    if confirm.lower() != 'yes':
        print("취소되었습니다.")
        sys.exit(0)

    # Import 실행
    importer.import_from_csv(csv_file)


if __name__ == '__main__':
    main()
```

---

### 3. Custom Field ID 확인 스크립트 (jira_fields.py)

```python
#!/usr/bin/env python3
"""
Jira Custom Field ID 확인
Epic Link, Story Points 등의 Custom Field ID를 확인합니다.
"""

import requests
from requests.auth import HTTPBasicAuth
from jira_config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN

def get_custom_fields():
    """모든 Custom Field 조회"""
    url = f"{JIRA_URL}/rest/api/3/field"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        fields = response.json()

        print("=" * 80)
        print("Custom Fields")
        print("=" * 80)

        custom_fields = [f for f in fields if f['id'].startswith('customfield_')]

        for field in custom_fields:
            print(f"ID: {field['id']}")
            print(f"Name: {field['name']}")
            print(f"Type: {field.get('schema', {}).get('type', 'N/A')}")
            print("-" * 80)

        # 주요 필드 자동 감지
        print("\n" + "=" * 80)
        print("주요 Custom Fields (자동 감지)")
        print("=" * 80)

        for field in custom_fields:
            name = field['name'].lower()
            if 'epic' in name and 'link' in name:
                print(f"Epic Link: {field['id']} ({field['name']})")
            elif 'story' in name and 'point' in name:
                print(f"Story Points: {field['id']} ({field['name']})")
            elif 'sprint' in name:
                print(f"Sprint: {field['id']} ({field['name']})")
    else:
        print(f"✗ 필드 조회 실패: {response.status_code}")
        print(response.text)


if __name__ == '__main__':
    get_custom_fields()
```

---

## 실행 방법

### Step 1: 환경 설정

```bash
cd /Users/redstar/AgentDev

# Python 가상 환경 생성 (선택)
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### Step 2: .env 파일 설정

```bash
# .env 파일 편집
nano .env

# 또는 직접 입력
cat > .env << 'EOF'
JIRA_URL=https://stockagent.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=SCRUM
EOF
```

### Step 3: Custom Field ID 확인

```bash
# Custom Field ID 조회
python jira_fields.py

# 출력 예시:
# Epic Link: customfield_10014
# Story Points: customfield_10016
```

**중요**: `jira_import.py`의 다음 라인을 확인된 ID로 수정:
```python
# Line 139: Epic Link
payload['fields']['customfield_10014'] = epic_key

# Line 162: Story Points
payload['fields']['customfield_10016'] = int(issue_data['Story Points'])
```

### Step 4: Import 실행

```bash
# 연결 테스트 및 Import
python jira_import.py
```

**실행 과정**:
```
✓ Jira 연결 성공: Your Name
📄 CSV 파일 읽기: jira-import.csv
총 131개 이슈 발견

============================================================
Phase 1: Epic 생성
============================================================
  ✓ 생성: SCRUM-1 - MVP 개발
  ✓ 생성: SCRUM-2 - 실전 거래 연동
  ✓ 생성: SCRUM-3 - 고급 기능
  ✓ 생성: SCRUM-4 - 인프라 & 배포
  ✓ 생성: SCRUM-5 - 테스트 & 품질 관리

✓ Epic 5개 생성 완료

============================================================
Phase 2: Story 생성
============================================================
  ✓ 생성: SCRUM-6 - 개발 환경 설정
  ...

✓ Story 27개 생성 완료

============================================================
Phase 3: Task 생성
============================================================
  ✓ 생성: SCRUM-33 - 프로젝트 디렉토리 구조 생성
  ...

✓ Task 99개 생성 완료

============================================================
Import 완료!
============================================================
Epic: 5개
Story: 27개
Task: 99개

프로젝트 URL: https://stockagent.atlassian.net/jira/software/projects/SCRUM
```

---

## Sprint 설정 (선택)

### Sprint 자동 생성 스크립트 (jira_sprints.py)

```python
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
```

---

## 문제 해결

### 1. 인증 오류 (401 Unauthorized)

**증상**:
```
✗ Jira 연결 실패: 401
```

**해결**:
```bash
# API Token 재확인
echo $JIRA_API_TOKEN

# 이메일 주소 확인
echo $JIRA_EMAIL

# 새 API Token 생성
# https://id.atlassian.com/manage-profile/security/api-tokens
```

### 2. 권한 오류 (403 Forbidden)

**증상**:
```
✗ 이슈 생성 실패: 403
```

**해결**:
- Jira 프로젝트에서 이슈 생성 권한 확인
- Project Settings → Permissions
- 계정이 Developer/Administrator 역할인지 확인

### 3. Custom Field ID 오류

**증상**:
```json
{"errors":{"customfield_10016":"Field does not exist"}}
```

**해결**:
```bash
# 1. Custom Field ID 확인
python jira_fields.py

# 2. jira_import.py 수정
# Epic Link: customfield_XXXXX
# Story Points: customfield_YYYYY
```

### 4. Epic Link 설정 안됨

**원인**: Epic Link는 일반 필드가 아닌 Custom Field

**해결**:
```python
# jira_import.py에서 Epic Link 필드 확인
# Line 139 수정:
payload['fields']['customfield_10014'] = epic_key  # ID 확인 필요
```

### 5. Rate Limiting

**증상**:
```
429 Too Many Requests
```

**해결**:
```python
# jira_import.py에서 sleep 시간 증가
time.sleep(1.0)  # 0.5 → 1.0초
```

---

## 검증 체크리스트

### Import 후 확인 사항

```bash
✓ 확인 항목:
  - [ ] Epic 5개 생성 확인
  - [ ] Story 27개 생성 확인
  - [ ] Task 99개 생성 확인
  - [ ] Epic Link 연결 확인
  - [ ] Priority 설정 확인
  - [ ] Component 할당 확인
  - [ ] Labels 설정 확인
  - [ ] Story Points 입력 확인

Jira에서 확인:
  - [ ] Backlog에서 Epic 계층 구조 확인
  - [ ] Board에서 이슈 보기
  - [ ] Filter로 Epic별 Story 확인
```

### Jira Query (JQL)

```sql
-- 모든 Epic 조회
project = SCRUM AND issuetype = Epic

-- Epic별 Story 조회
project = SCRUM AND "Epic Link" = SCRUM-1

-- Sprint 1 이슈 조회
project = SCRUM AND sprint = "Sprint 1"

-- Backend 컴포넌트
project = SCRUM AND component = Backend

-- Highest 우선순위
project = SCRUM AND priority = Highest
```

---

## 고급 기능

### 1. Bulk Update (일괄 수정)

```python
def bulk_update_sprint(issue_keys: List[str], sprint_id: int):
    """여러 이슈를 Sprint에 한번에 할당"""
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {'Content-Type': 'application/json'}

    payload = {'issues': issue_keys}

    response = requests.post(url, auth=auth, headers=headers, json=payload)
    return response.status_code == 204
```

### 2. CSV 업데이트 (기존 이슈 수정)

```python
def update_issue(issue_key: str, fields: Dict):
    """기존 이슈 업데이트"""
    url = f"{ISSUE_ENDPOINT}/{issue_key}"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {'Content-Type': 'application/json'}

    payload = {'fields': fields}

    response = requests.put(url, auth=auth, headers=headers, json=payload)
    return response.status_code == 204
```

### 3. 롤백 (생성된 이슈 삭제)

```python
def delete_all_issues():
    """프로젝트의 모든 이슈 삭제 (주의!)"""
    jql = f"project = {JIRA_PROJECT_KEY}"
    url = f"{SEARCH_ENDPOINT}?jql={jql}&maxResults=1000"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)

    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        issues = response.json()['issues']

        for issue in issues:
            issue_key = issue['key']
            delete_url = f"{ISSUE_ENDPOINT}/{issue_key}"
            requests.delete(delete_url, auth=auth)
            print(f"✓ 삭제: {issue_key}")
```

---

## 참고 자료

### Jira REST API 문서
- **API 문서**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/
- **Issue 생성**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/#api-rest-api-3-issue-post
- **Agile API**: https://developer.atlassian.com/cloud/jira/software/rest/intro/

### 유용한 링크
- **API Token 관리**: https://id.atlassian.com/manage-profile/security/api-tokens
- **Jira Query Language**: https://support.atlassian.com/jira-service-management-cloud/docs/use-advanced-search-with-jira-query-language-jql/

---

## 요약

### 추천 방법: Python 스크립트 (자동화)

```bash
# 1. 환경 설정
pip install -r requirements.txt
nano .env  # API 정보 입력

# 2. Custom Field 확인
python jira_fields.py

# 3. Import 실행
python jira_import.py

# 4. Sprint 생성 (선택)
python jira_sprints.py
```

### 장점
- ✅ 완전 자동화
- ✅ 에러 처리
- ✅ Epic Link 자동 설정
- ✅ 재실행 가능
- ✅ 대량 처리 (131개 이슈)

---

**작성일**: 2026-02-07
**업데이트**: Import 후 검증 완료 시
