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
