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
import os
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
