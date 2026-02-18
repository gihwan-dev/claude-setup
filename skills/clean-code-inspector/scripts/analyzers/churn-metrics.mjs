import { spawnSync } from 'node:child_process';

function normalizePath(value) {
  return value.replace(/\\/g, '/');
}

export function collectChurnMetrics({ projectRoot, files, windowDays = 90 }) {
  const byFile = new Map();
  const unavailableMetrics = [];

  if (files.length === 0) {
    return { byFile, unavailableMetrics };
  }

  const args = [
    '-C',
    projectRoot,
    'log',
    '--numstat',
    '--pretty=format:__COMMIT__',
    `--since=${windowDays}.days`,
    '--',
    ...files,
  ];

  const result = spawnSync('git', args, {
    encoding: 'utf8',
  });

  if (result.status !== 0) {
    unavailableMetrics.push(`git.log-failed:${(result.stderr || result.stdout || '').trim()}`);
    return { byFile, unavailableMetrics };
  }

  const totals = new Map();
  for (const file of files) {
    totals.set(file, { churnLines: 0, churnTouches: 0 });
  }

  const lines = (result.stdout || '').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed === '__COMMIT__') {
      continue;
    }

    const parts = trimmed.split('\t');
    if (parts.length < 3) {
      continue;
    }

    const [addedRaw, deletedRaw, filePathRaw] = parts;
    const filePath = normalizePath(filePathRaw);
    if (!totals.has(filePath)) {
      continue;
    }

    const added = addedRaw === '-' ? 0 : Number(addedRaw);
    const deleted = deletedRaw === '-' ? 0 : Number(deletedRaw);
    const value = totals.get(filePath);

    value.churnLines += (Number.isFinite(added) ? added : 0) + (Number.isFinite(deleted) ? deleted : 0);
    value.churnTouches += 1;
  }

  for (const [file, metric] of totals) {
    byFile.set(file, metric);
  }

  return {
    byFile,
    unavailableMetrics,
  };
}
