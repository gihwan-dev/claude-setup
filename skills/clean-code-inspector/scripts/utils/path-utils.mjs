import path from 'node:path';

const JS_TS_EXTENSIONS = ['.ts', '.tsx', '.js', '.jsx', '.mts', '.cts', '.mjs', '.cjs'];

const EXCLUDE_PATTERNS = [
  'node_modules/',
  '/node_modules/',
  '.d.ts',
  '.stories.tsx',
  '.stories.ts',
  '.stories.jsx',
  '.stories.js',
  'dist/',
  '/dist/',
  'build/',
  '/build/',
  '.next/',
  '/.next/',
  'coverage/',
  '/coverage/',
  '*.config.ts',
  '*.config.js',
  '*.config.mjs',
  '*.config.cjs',
];

export function normalizeSlashes(value) {
  return value.replace(/\\/g, '/');
}

export function isSupportedSourceFile(filePath) {
  const normalized = normalizeSlashes(filePath);
  return JS_TS_EXTENSIONS.some((ext) => normalized.endsWith(ext));
}

export function isExcludedPath(filePath) {
  const normalized = normalizeSlashes(filePath);

  for (const pattern of EXCLUDE_PATTERNS) {
    if (pattern.startsWith('*')) {
      const suffix = pattern.slice(1);
      if (normalized.endsWith(suffix)) {
        return true;
      }
      continue;
    }

    if (normalized.includes(pattern)) {
      return true;
    }
  }

  return false;
}

export function isCandidateFile(filePath) {
  return isSupportedSourceFile(filePath) && !isExcludedPath(filePath);
}

export function toRelativePath(projectRoot, filePath) {
  const resolved = path.resolve(projectRoot, filePath);
  const relative = path.relative(projectRoot, resolved);
  return normalizeSlashes(relative);
}

export function toAbsolutePath(projectRoot, relativePath) {
  return path.resolve(projectRoot, relativePath);
}

export function dedupeSorted(values) {
  return [...new Set(values)].sort((a, b) => a.localeCompare(b));
}

export function fileExistsSafe(fsModule, filePath) {
  try {
    return fsModule.existsSync(filePath);
  } catch {
    return false;
  }
}

export function resolveImportPath(projectRoot, importerRelativePath, importSource) {
  if (!importSource || typeof importSource !== 'string') {
    return null;
  }

  if (!importSource.startsWith('.')) {
    return null;
  }

  const importerAbsolute = path.resolve(projectRoot, importerRelativePath);
  const importerDir = path.dirname(importerAbsolute);
  const candidateBase = path.resolve(importerDir, importSource);

  const candidates = [
    candidateBase,
    ...JS_TS_EXTENSIONS.map((ext) => `${candidateBase}${ext}`),
    ...JS_TS_EXTENSIONS.map((ext) => path.join(candidateBase, `index${ext}`)),
  ];

  for (const candidateAbsolute of candidates) {
    const relative = normalizeSlashes(path.relative(projectRoot, candidateAbsolute));
    if (!relative || relative.startsWith('..')) {
      continue;
    }

    if (!isCandidateFile(relative)) {
      continue;
    }

    return relative;
  }

  return null;
}

export function splitTargetFiles(rawTarget) {
  if (!rawTarget) {
    return [];
  }

  return rawTarget
    .split(/[\s,]+/g)
    .map((item) => item.trim())
    .filter(Boolean);
}
