import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

function normalizePath(value) {
  return value.replace(/\\/g, '/');
}

function computeInstability(fanOut, fanIn, existing) {
  if (typeof existing === 'number' && Number.isFinite(existing)) {
    return existing;
  }

  const denominator = fanOut + fanIn;
  if (denominator === 0) {
    return 0;
  }

  return fanOut / denominator;
}

function resolveDepCruiseBin(skillRoot) {
  const localBin = path.resolve(skillRoot, 'node_modules', '.bin', 'depcruise');
  if (fs.existsSync(localBin)) {
    return localBin;
  }

  return 'depcruise';
}

export function collectDependencyMetrics({ projectRoot, skillRoot, files }) {
  const byFile = new Map();
  const unavailableMetrics = [];

  if (files.length === 0) {
    return { byFile, unavailableMetrics };
  }

  const depCruiseBin = resolveDepCruiseBin(skillRoot);

  const commandArgs = [
    ...files,
    '--no-config',
    '--metrics',
    '--output-type',
    'json',
  ];

  const runResult = spawnSync(depCruiseBin, commandArgs, {
    cwd: projectRoot,
    encoding: 'utf8',
  });

  if (runResult.status !== 0) {
    unavailableMetrics.push(
      `dependency-cruiser.failed:${(runResult.stderr || runResult.stdout || '').trim()}`,
    );
    return { byFile, unavailableMetrics };
  }

  let parsed;
  try {
    parsed = JSON.parse(runResult.stdout || '{}');
  } catch (error) {
    unavailableMetrics.push(`dependency-cruiser.invalid-json:${String(error)}`);
    return { byFile, unavailableMetrics };
  }

  const modules = Array.isArray(parsed.modules) ? parsed.modules : [];
  const moduleBySource = new Map(modules.map((item) => [normalizePath(item.source), item]));

  for (const relative of files) {
    const moduleInfo = moduleBySource.get(normalizePath(relative));

    if (!moduleInfo) {
      byFile.set(relative, {
        fanIn: 0,
        fanOut: 0,
        instability: 0,
        circular: false,
      });
      continue;
    }

    const dependencies = Array.isArray(moduleInfo.dependencies) ? moduleInfo.dependencies : [];
    const dependents = Array.isArray(moduleInfo.dependents) ? moduleInfo.dependents : [];

    const fanOut = dependencies.length;
    const fanIn = dependents.length;

    byFile.set(relative, {
      fanIn,
      fanOut,
      instability: computeInstability(fanOut, fanIn, moduleInfo.instability),
      circular: dependencies.some((dependency) => dependency?.circular === true),
    });
  }

  return {
    byFile,
    unavailableMetrics,
  };
}
