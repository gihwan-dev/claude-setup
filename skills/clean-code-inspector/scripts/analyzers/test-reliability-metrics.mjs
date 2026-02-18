import fs from 'node:fs';
import path from 'node:path';
import fg from 'fast-glob';

function normalizePath(value) {
  return value.replace(/\\/g, '/');
}

function safeReadJson(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
  } catch {
    return null;
  }
}

function resolveCoverageEntry(coverageJson, projectRoot, relativePath) {
  if (!coverageJson || typeof coverageJson !== 'object') {
    return null;
  }

  const normalizedRelative = normalizePath(relativePath);
  const absolutePath = normalizePath(path.resolve(projectRoot, relativePath));

  const keys = [
    normalizedRelative,
    `./${normalizedRelative}`,
    absolutePath,
    absolutePath.replace(`${normalizePath(projectRoot)}/`, ''),
  ];

  for (const key of keys) {
    const entry = coverageJson[key];
    if (entry && typeof entry === 'object') {
      return entry;
    }
  }

  return null;
}

function resolveMutationData(mutationJson, projectRoot, files) {
  const byFile = new Map();

  if (!mutationJson || typeof mutationJson !== 'object') {
    return byFile;
  }

  const globalScore = mutationJson.metrics?.mutationScore;

  const fileEntries = mutationJson.files && typeof mutationJson.files === 'object'
    ? Object.entries(mutationJson.files)
    : [];

  for (const [filePathRaw, info] of fileEntries) {
    if (!info || typeof info !== 'object') {
      continue;
    }

    const normalized = normalizePath(filePathRaw);
    const relative = normalized.startsWith(normalizePath(projectRoot))
      ? normalizePath(path.relative(projectRoot, normalized))
      : normalized;

    const mutants = Array.isArray(info.mutants) ? info.mutants : [];
    if (mutants.length > 0) {
      const relevant = mutants.filter((mutant) => mutant?.status !== 'Ignored');
      const killed = relevant.filter((mutant) => mutant?.status === 'Killed').length;
      const total = relevant.length;
      byFile.set(relative, total > 0 ? (killed / total) * 100 : null);
      continue;
    }

    const score = info.metrics?.mutationScore;
    if (typeof score === 'number') {
      byFile.set(relative, score);
    }
  }

  if (typeof globalScore === 'number') {
    for (const file of files) {
      if (!byFile.has(file)) {
        byFile.set(file, globalScore);
      }
    }
  }

  return byFile;
}

export async function collectTestReliabilityMetrics({ projectRoot, files }) {
  const byFile = new Map();
  const unavailableMetrics = [];

  if (files.length === 0) {
    return { byFile, unavailableMetrics };
  }

  const coverageCandidates = await fg(
    [
      'coverage/coverage-summary.json',
      '**/coverage/coverage-summary.json',
      '**/coverage-summary.json',
    ],
    {
      cwd: projectRoot,
      dot: false,
      absolute: true,
      ignore: ['**/node_modules/**', '**/dist/**', '**/build/**', '**/.next/**'],
    },
  );

  const mutationCandidates = await fg(
    [
      '**/reports/mutation/mutation-report.json',
      '**/mutation-report.json',
      '**/stryker-report.json',
      '**/mutation/mutation-report.json',
    ],
    {
      cwd: projectRoot,
      dot: false,
      absolute: true,
      ignore: ['**/node_modules/**', '**/dist/**', '**/build/**', '**/.next/**'],
    },
  );

  const coverageJson = coverageCandidates.length > 0 ? safeReadJson(coverageCandidates[0]) : null;
  const mutationJson = mutationCandidates.length > 0 ? safeReadJson(mutationCandidates[0]) : null;

  if (!coverageJson) {
    unavailableMetrics.push('coverage-summary.not-found');
  }

  if (!mutationJson) {
    unavailableMetrics.push('mutation-report.not-found');
  }

  const mutationByFile = resolveMutationData(mutationJson, projectRoot, files);

  for (const relativePath of files) {
    const coverageEntry = coverageJson
      ? resolveCoverageEntry(coverageJson, projectRoot, relativePath)
      : null;

    byFile.set(relativePath, {
      lineCoverage:
        typeof coverageEntry?.lines?.pct === 'number' ? coverageEntry.lines.pct : null,
      branchCoverage:
        typeof coverageEntry?.branches?.pct === 'number' ? coverageEntry.branches.pct : null,
      mutationScore: mutationByFile.has(relativePath) ? mutationByFile.get(relativePath) : null,
    });
  }

  return {
    byFile,
    unavailableMetrics,
  };
}
