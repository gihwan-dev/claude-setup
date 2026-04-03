# MR Creator Prompt Template

전체 파이프라인 완료 후 draft MR을 일괄 생성하는 Codex 프롬프트 구조.
Claude가 변수를 치환한 뒤 Codex에 전달한다.

## Template

```xml
<task>
## 목적
파이프라인의 모든 작업 브랜치와 stage 브랜치에 대해 draft MR을 일괄 생성한다.

## 플랫폼
${PLATFORM}

## MR 생성 계획
${MR_PLAN}

## MR 생성 규칙
- 모든 MR은 **draft**로 생성
- MR 제목: `<type>(<scope>): <설명>` (한국어, 70자 이내)
- task MR: 해당 작업의 변경사항을 설명
- group MR: "Group X 통합" 형태
- MR body에 관련 작업 ID와 의존성 정보 포함

## 완료 기준
- MR Plan의 모든 항목에 대해 draft MR 생성
- 각 MR의 URL 수집
- PIPELINE.md의 MR Plan 상태 업데이트
</task>

<structured_output_contract>
완료 후 반드시:
1. 생성된 MR 목록 (번호, 제목, URL)
2. PIPELINE.md의 MR Plan 테이블 업데이트 (Status를 `created`로, URL 추가)
</structured_output_contract>

<action_safety>
- MR 생성과 PIPELINE.md 업데이트만 수행
- 코드 수정 금지
- 브랜치 머지 금지
</action_safety>

<default_follow_through_policy>
가장 합리적인 해석을 기본으로 삼고 계속 진행.
정보 부재가 잘못된 동작을 야기할 때만 멈춘다.
</default_follow_through_policy>
```

## 변수 치환 규칙

| 변수 | 출처 | 비고 |
|------|------|------|
| `PLATFORM` | `glab` 또는 `gh` (자동 감지) | git remote URL 기반 |
| `MR_PLAN` | PIPELINE.md의 MR Plan 테이블 | 그대로 복사 |

## 플랫폼 감지

`git remote get-url origin`으로 판별:
- `gitlab` → `glab mr create --draft`
- `github` → `gh pr create --draft`

MR body에 Task ID, Group, Dependencies를 포함하고 "머지 순서는 PIPELINE.md 참조"를 명기한다.
