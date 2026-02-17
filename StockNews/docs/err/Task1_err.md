# Task [1] 프로젝트 초기 설정 — 발견된 오류

## ERR-1: pyproject.toml build-backend 오류
- **위치**: `backend/pyproject.toml`
- **증상**: `pip install -e ".[dev]"` 실행 시 `Cannot import 'setuptools.backends._legacy'` 에러
- **원인**: `build-backend = "setuptools.backends._legacy:_Backend"` 가 존재하지 않는 모듈
- **수정**: `build-backend = "setuptools.build_meta"` 로 변경
- **상태**: ✅ 수정 완료

## ERR-2: setuptools 패키지 자동 탐색 충돌
- **위치**: `backend/pyproject.toml`
- **증상**: `Multiple top-level packages discovered in a flat-layout: ['app', 'alembic']`
- **원인**: `alembic/` 디렉토리가 패키지로 인식되어 `app` 과 충돌
- **수정**: `[tool.setuptools.packages.find]` 섹션 추가, `include = ["app*"]` 명시
- **상태**: ✅ 수정 완료

## ERR-3: Python 버전 불일치
- **위치**: `backend/pyproject.toml`, `backend/ruff.toml`
- **증상**: 시스템에 Python 3.11 미설치, Python 3.13만 사용 가능
- **원인**: 설계서 기준 Python 3.11이나 실제 환경은 3.13
- **수정**: `requires-python = ">=3.12"`, `target-version = "py313"` 으로 변경
- **상태**: ✅ 수정 완료
- **참고**: StockNews-v1.0.md Section 3의 Python 버전 기술 업데이트 필요

## ERR-4: vite.config.ts TypeScript 타입 오류
- **위치**: `frontend/vite.config.ts`
- **증상**: `'test' does not exist in type 'UserConfigExport'` [2769]
- **원인**: vitest v4에서 `/// <reference types="vitest" />` 방식 미동작
- **수정**: `import { defineConfig } from 'vitest/config'` 으로 변경
- **상태**: ✅ 수정 완료
