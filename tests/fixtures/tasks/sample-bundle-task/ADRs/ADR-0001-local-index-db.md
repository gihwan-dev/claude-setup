# ADR-0001 local index db

## Context

session log query latency가 높다.

## Decision

local SQLite index DB를 둔다.

## Consequence

query latency는 줄고 ingest 단계가 추가된다.
