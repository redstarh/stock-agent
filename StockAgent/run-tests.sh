#!/bin/bash
#
# 테스트 실행 스크립트
#

set -e

echo "======================================"
echo "   Trading System Test Runner"
echo "======================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 함수: 섹션 헤더 출력
print_section() {
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 함수: 성공 메시지
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 함수: 에러 메시지
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 인자 파싱
TEST_TYPE=${1:-all}

case $TEST_TYPE in
    backend)
        print_section "Backend Tests"
        cd backend

        # Unit Tests
        echo "🧪 Running Unit Tests..."
        pytest tests/unit -v --cov=src --cov-report=term-missing
        print_success "Unit tests completed"

        # Integration Tests
        echo ""
        echo "🔗 Running Integration Tests..."
        pytest tests/integration -v
        print_success "Integration tests completed"

        # Coverage Report
        echo ""
        echo "📊 Generating Coverage Report..."
        pytest --cov=src --cov-report=html
        print_success "Coverage report generated: htmlcov/index.html"
        ;;

    frontend)
        print_section "Frontend Tests"
        cd frontend

        # Jest Tests
        echo "⚛️  Running Jest Tests..."
        npm test -- --coverage --watchAll=false
        print_success "Jest tests completed"

        # E2E Tests
        echo ""
        echo "🎭 Running E2E Tests..."
        npx playwright test
        print_success "E2E tests completed"
        ;;

    unit)
        print_section "Unit Tests Only"

        echo "Backend Unit Tests..."
        cd backend
        pytest tests/unit -v -m unit
        print_success "Backend unit tests completed"

        cd ../frontend
        echo ""
        echo "Frontend Unit Tests..."
        npm test -- --testPathPattern='__tests__/unit' --watchAll=false
        print_success "Frontend unit tests completed"
        ;;

    integration)
        print_section "Integration Tests Only"

        echo "Backend Integration Tests..."
        cd backend
        pytest tests/integration -v -m integration
        print_success "Integration tests completed"
        ;;

    e2e)
        print_section "E2E Tests Only"
        cd frontend

        echo "🎭 Running Playwright E2E Tests..."
        npx playwright test
        print_success "E2E tests completed"

        echo ""
        echo "📊 Opening test report..."
        npx playwright show-report
        ;;

    quick)
        print_section "Quick Tests (Unit Only)"

        echo "Backend Quick Tests..."
        cd backend
        pytest tests/unit -v --maxfail=1 --tb=short

        cd ../frontend
        echo ""
        echo "Frontend Quick Tests..."
        npm test -- --bail --testPathPattern='__tests__/unit' --watchAll=false
        ;;

    coverage)
        print_section "Coverage Report"

        echo "Generating Backend Coverage..."
        cd backend
        pytest --cov=src --cov-report=html --cov-report=term
        print_success "Backend coverage: htmlcov/index.html"

        cd ../frontend
        echo ""
        echo "Generating Frontend Coverage..."
        npm test -- --coverage --watchAll=false
        print_success "Frontend coverage: coverage/lcov-report/index.html"
        ;;

    ci)
        print_section "CI Mode (All Tests)"

        # Backend
        echo "Running Backend Tests..."
        cd backend
        pytest -v --cov=src --cov-report=xml --cov-fail-under=80

        # Frontend
        cd ../frontend
        echo ""
        echo "Running Frontend Tests..."
        npm test -- --coverage --watchAll=false --ci

        echo ""
        echo "Running E2E Tests..."
        npx playwright test --reporter=github

        print_success "All CI tests completed"
        ;;

    all|*)
        print_section "Running All Tests"

        # Backend
        echo "📦 Backend Tests..."
        cd backend
        pytest -v --cov=src --cov-report=term-missing
        print_success "Backend tests completed"

        # Frontend
        cd ../frontend
        echo ""
        echo "⚛️  Frontend Tests..."
        npm test -- --coverage --watchAll=false
        print_success "Frontend tests completed"

        echo ""
        echo "🎭 E2E Tests..."
        npx playwright test
        print_success "E2E tests completed"

        echo ""
        print_section "All Tests Completed!"
        echo "Coverage Reports:"
        echo "  - Backend:  backend/htmlcov/index.html"
        echo "  - Frontend: frontend/coverage/lcov-report/index.html"
        echo "  - E2E:      frontend/playwright-report/index.html"
        ;;
esac

echo ""
echo -e "${GREEN}======================================"
echo -e "   Tests Completed Successfully! ✓"
echo -e "======================================${NC}"
echo ""
