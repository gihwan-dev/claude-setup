## Structure-First Authoring

### Structure preflight

- 기존 TS/JS/React 코드 파일을 수정할 때는 fast lane 여부를 보기 전에 `structure preflight`를 먼저 수행한다.
- `structure preflight`는 최소 아래 세 가지를 고정한다.
  - 대상 파일 역할 분류 (`component`, `view`, `hook`, `provider`, `view-model`, `composable`, `middleware`, `service`, `use-case`, `repository`, `controller`, `util`, `adapter`)
  - 예상 post-change LOC
  - `split-first` 필요 여부
- `split-first`가 켜지면 기존 파일에 그대로 append하지 않고, 같은 slice 안에서 분해하거나 범위 초과 시 `blocked + exact split proposal`로 되돌린다.

### Split-First Triggers

- 아래 중 하나라도 해당하면 `split-first`다.
  - 대상 파일이 soft limit에 근접하거나 이미 초과했다.
  - 이번 변경이 새 책임을 추가한다.
  - util/service/use-case/repository 성격 코드를 component/view 파일에 붙이려 한다.
  - 반복 stateful 또는 branch-heavy 로직을 기존 파일에 더 얹으려 한다.

### Strong Mode

- soft limit 근접/초과 파일에는 append를 허용하지 않는다.
- 이미 soft limit를 넘긴 파일에 additive diff를 더하면 `FAIL`이다.
- hard limit 초과와 책임 혼합은 항상 `FAIL`이다.
- 기존 레거시 과대 파일을 건드리지 않는 경우에만 advisory를 허용한다.

### Scope Discipline

- 루트 메모리는 짧게 유지하고, 세부 구조 규칙은 specialized agent/skill contract와 machine-readable policy로 관리한다.
- user-facing long-running surface는 계속 `design-task`, `implement-task`만 유지한다.
- 새 task의 source of truth는 `task.yaml` bundle이며, `PLAN.md`는 legacy fallback compatibility로만 유지한다.
