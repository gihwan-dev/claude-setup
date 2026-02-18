import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { parse } from '@typescript-eslint/typescript-estree';
import {
  dedupeSorted,
  isCandidateFile,
  normalizeSlashes,
  resolveImportPath,
  splitTargetFiles,
} from './path-utils.mjs';

const DEFAULT_CLOSURE_LIMIT = 300;

function runGit(projectRoot, args) {
  const result = spawnSync('git', ['-C', projectRoot, ...args], {
    encoding: 'utf8',
  });

  if (result.status !== 0) {
    return {
      ok: false,
      output: '',
      error: (result.stderr || result.stdout || 'git command failed').trim(),
    };
  }

  return {
    ok: true,
    output: result.stdout || '',
    error: '',
  };
}

function parseFileListOutput(rawOutput) {
  return rawOutput
    .split('\n')
    .map((line) => normalizeSlashes(line.trim()))
    .filter(Boolean);
}

function resolveChangedFilesByMode({ projectRoot, mode, target }) {
  if (mode === 'files') {
    return {
      files: splitTargetFiles(target),
      warnings: [],
    };
  }

  const modeToArgs = {
    working: ['diff', '--name-only'],
    staged: ['diff', '--cached', '--name-only'],
    branch: ['diff', `${target}...HEAD`, '--name-only'],
    range: ['diff', target, '--name-only'],
  };

  const args = modeToArgs[mode] || modeToArgs.working;

  if ((mode === 'branch' || mode === 'range') && !target) {
    return {
      files: [],
      warnings: [`mode=${mode} requires --target`],
    };
  }

  const gitResult = runGit(projectRoot, args);
  if (!gitResult.ok) {
    return {
      files: [],
      warnings: [`failed to resolve changed files: ${gitResult.error}`],
    };
  }

  return {
    files: parseFileListOutput(gitResult.output),
    warnings: [],
  };
}

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

function collectImportsFromSource(sourceCode, filePath) {
  const imports = [];

  let ast;
  try {
    ast = parse(sourceCode, {
      comment: true,
      jsx: filePath.endsWith('.tsx') || filePath.endsWith('.jsx'),
      loc: true,
      range: false,
      errorOnUnknownASTType: false,
    });
  } catch {
    return imports;
  }

  walkAst(ast, (node) => {
    if (node.type === 'ImportDeclaration' && typeof node.source?.value === 'string') {
      imports.push(node.source.value);
      return;
    }

    if (
      (node.type === 'ExportNamedDeclaration' || node.type === 'ExportAllDeclaration') &&
      typeof node.source?.value === 'string'
    ) {
      imports.push(node.source.value);
      return;
    }

    if (node.type === 'CallExpression') {
      const firstArg = node.arguments?.[0];
      const hasStringArg = firstArg && firstArg.type === 'Literal' && typeof firstArg.value === 'string';
      if (!hasStringArg) {
        return;
      }

      const callee = node.callee;
      if (callee?.type === 'Import' || (callee?.type === 'Identifier' && callee.name === 'require')) {
        imports.push(firstArg.value);
      }
    }
  });

  return imports;
}

function buildImportClosure({ projectRoot, seedFiles, maxFiles = DEFAULT_CLOSURE_LIMIT }) {
  const queue = [...seedFiles];
  const visited = new Set();
  const warnings = [];
  let truncated = false;

  while (queue.length > 0) {
    const relative = queue.shift();
    if (visited.has(relative)) {
      continue;
    }

    visited.add(relative);

    if (visited.size >= maxFiles) {
      if (queue.length > 0) {
        truncated = true;
      }
      break;
    }

    const absolute = path.resolve(projectRoot, relative);
    if (!fs.existsSync(absolute)) {
      continue;
    }

    let sourceCode;
    try {
      sourceCode = fs.readFileSync(absolute, 'utf8');
    } catch {
      warnings.push(`failed to read file: ${relative}`);
      continue;
    }

    const imports = collectImportsFromSource(sourceCode, relative);
    for (const source of imports) {
      const resolvedRelative = resolveImportPath(projectRoot, relative, source);
      if (!resolvedRelative || visited.has(resolvedRelative)) {
        continue;
      }
      queue.push(resolvedRelative);
    }
  }

  return {
    files: dedupeSorted([...visited]),
    truncated,
    warnings,
  };
}

export function resolveAnalysisTargets({
  projectRoot,
  mode = 'working',
  target = '',
  closureLimit = DEFAULT_CLOSURE_LIMIT,
}) {
  const changed = resolveChangedFilesByMode({ projectRoot, mode, target });
  const normalizedChanged = changed.files
    .map((file) => normalizeSlashes(file))
    .filter((file) => isCandidateFile(file));

  const seedFiles = dedupeSorted(normalizedChanged);

  if (seedFiles.length === 0) {
    return {
      seedFiles: [],
      targetFiles: [],
      truncated: false,
      warnings: changed.warnings,
    };
  }

  const closure = buildImportClosure({
    projectRoot,
    seedFiles,
    maxFiles: closureLimit,
  });

  return {
    seedFiles,
    targetFiles: closure.files,
    truncated: closure.truncated,
    warnings: [...changed.warnings, ...closure.warnings],
  };
}
