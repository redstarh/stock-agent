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
