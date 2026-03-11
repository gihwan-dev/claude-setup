# Technical Specification

- index DB는 local SQLite를 사용한다.
- timeline normalization은 ingest 이후 별도 단계로 수행한다.
- `ADR-0001`에 local index DB 결정을 위임한다.
