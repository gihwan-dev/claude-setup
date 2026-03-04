# 좋은 코멘트 리서치 요약

이 문서는 `commter` 스킬이 따르는 코멘트 작성 기준의 근거를 정리한다.

## 핵심 결론

1. 코멘트는 구현 번역이 아니라 의도를 전달해야 한다.
- Google TypeScript Style Guide는 코드를 반복 설명하는 주석보다,
  의도와 설계를 설명하는 문서를 권장한다.

2. 공개 API와 복잡 로직은 JSDoc/주석으로 문서화해야 한다.
- Google 가이드는 최상위 export와 복잡한 함수에 대한 문서화를 요구한다.
- 특히 호출자가 알아야 하는 제약, 부작용, 예외를 우선 설명해야 한다.

3. JSDoc 태그는 계약(Contract) 설명에 집중해야 한다.
- JSDoc 공식 문서는 `@param`, `@returns` 태그를 통해
  인자 의미와 반환값 의미를 분명히 하도록 안내한다.
- TypeScript 문서는 JSDoc 지원 태그를 명시하므로,
  지원되는 태그 중심으로 문서화해야 한다.

4. 좋은 코멘트의 품질은 일관성/완전성/가독성으로 평가된다.
- 체계적 문헌 리뷰(SLR)에서는 코멘트 품질 핵심 속성으로
  consistency, completeness, readability를 제시한다.
- 즉 "최신 코드와 일치하는지", "빠진 맥락이 없는지", "읽기 쉬운지"가 중요하다.

5. 불필요한 코멘트는 유지보수 비용을 올린다.
- Linux kernel coding style은 잘못 쓰인 코멘트가 혼란을 만든다고 지적하며,
  무엇을 하는지보다 왜 그렇게 하는지 설명하라고 권장한다.

## 실행 가능한 규칙

- 주석 추가 전: 이름 개선/함수 추출로 설명 가능하면 먼저 코드 구조를 개선한다.
- 주석 추가 시: "왜", "제약", "부작용", "의사결정 근거" 중 최소 1개를 담는다.
- 주석 수정 시: diff 범위 내 변경과 불일치하면 즉시 갱신한다.
- 주석 제거 시: 코드와 동일 문장 반복, 오래된 TODO, 오해를 유도하는 설명을 삭제한다.

## 참고 링크

- Google TypeScript Style Guide (Comments & Documentation):
  [https://google.github.io/styleguide/tsguide.html#comments-and-documentation](https://google.github.io/styleguide/tsguide.html#comments-and-documentation)
- JSDoc `@param`:
  [https://jsdoc.app/tags-param](https://jsdoc.app/tags-param)
- JSDoc `@returns`:
  [https://jsdoc.app/tags-returns](https://jsdoc.app/tags-returns)
- TypeScript Handbook - JSDoc Reference:
  [https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html)
- SLR: Software Code Comment Quality Assessment (2024):
  [https://www.sciencedirect.com/science/article/pii/S0950584924001580](https://www.sciencedirect.com/science/article/pii/S0950584924001580)
- Linux kernel coding style (Commenting):
  [https://docs.kernel.org/process/coding-style.html#commenting](https://docs.kernel.org/process/coding-style.html#commenting)
