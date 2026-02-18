import fs from 'node:fs';
import path from 'node:path';
import escomplex from 'typhonjs-escomplex';
import { parse } from '@typescript-eslint/typescript-estree';

function walkAst(node, visitor) {
  if (!node || typeof node !== 'object') {
    return;
  }

  visitor(node);

  for (const key of Object.keys(node)) {
    if (
      key === 'parent' ||
      key === 'loc' ||
      key === 'range' ||
      key === 'tokens' ||
      key === 'comments'
    ) {
      continue;
    }

    const value = node[key];
    if (Array.isArray(value)) {
      for (const item of value) {
        walkAst(item, visitor);
      }
    } else if (value && typeof value === 'object') {
      walkAst(value, visitor);
    }
  }
}

function countIgnoreDirectives(sourceCode) {
  const matches = sourceCode.match(/@ts-ignore|@ts-expect-error/g);
  return matches ? matches.length : 0;
}

function getParserOptions(filePath) {
  return {
    comment: true,
    jsx: filePath.endsWith('.tsx') || filePath.endsWith('.jsx'),
    loc: true,
    range: false,
    errorOnUnknownASTType: false,
  };
}

export function collectAstStructuralMetrics({ projectRoot, files }) {
  const result = new Map();
  const unavailableMetrics = [];

  for (const relativePath of files) {
    const absolutePath = path.resolve(projectRoot, relativePath);

    let sourceCode;
    try {
      sourceCode = fs.readFileSync(absolutePath, 'utf8');
    } catch {
      unavailableMetrics.push(`ast.read-failed:${relativePath}`);
      continue;
    }

    let ast = null;
    try {
      ast = parse(sourceCode, getParserOptions(relativePath));
    } catch {
      unavailableMetrics.push(`ast.parse-failed:${relativePath}`);
    }

    let complexityReport = null;
    try {
      complexityReport = escomplex.analyzeModule(sourceCode);
    } catch {
      unavailableMetrics.push(`escomplex.failed:${relativePath}`);
    }

    let importCount = 0;
    let stateCount = 0;
    let anyCount = 0;
    let assertionCount = 0;

    if (ast) {
      walkAst(ast, (node) => {
        if (node.type === 'ImportDeclaration') {
          importCount += 1;
        }

        if (node.type === 'CallExpression') {
          const callee = node.callee;
          if (callee?.type === 'Identifier' && (callee.name === 'useState' || callee.name === 'useReducer')) {
            stateCount += 1;
          }

          if (
            callee?.type === 'MemberExpression' &&
            callee.property?.type === 'Identifier' &&
            (callee.property.name === 'useState' || callee.property.name === 'useReducer')
          ) {
            stateCount += 1;
          }
        }

        if (node.type === 'TSAnyKeyword') {
          anyCount += 1;
        }

        if (node.type === 'TSAsExpression' || node.type === 'TSTypeAssertion') {
          assertionCount += 1;
        }
      });
    }

    const logicalLoc = complexityReport?.aggregate?.sloc?.logical ?? null;
    const physicalLocFromComplexity = complexityReport?.aggregate?.sloc?.physical ?? null;
    const nonEmptyLines = sourceCode
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean).length;

    const metrics = {
      locLogical: logicalLoc,
      locPhysical: physicalLocFromComplexity ?? nonEmptyLines,
      importCount,
      stateCount,
      anyCount,
      assertionCount,
      tsIgnoreCount: countIgnoreDirectives(sourceCode),
      halsteadVolume: complexityReport?.aggregate?.halstead?.volume ?? null,
      maintainabilityIndex: complexityReport?.maintainability ?? null,
      cyclomaticApprox: complexityReport?.aggregate?.cyclomatic ?? null,
    };

    result.set(relativePath, metrics);
  }

  return {
    byFile: result,
    unavailableMetrics,
  };
}
