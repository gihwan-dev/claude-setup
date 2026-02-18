#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { ensureToolchain } from './ensure-toolchain.mjs';

const DEFAULT_PROFILE = 'balanced';
const DEFAULT_WINDOW_DAYS = 90;
const DEFAULT_CLOSURE_LIMIT = 300;
const AXIS_WEIGHTS = {
  complexity: 35,
  typeSafety: 30,
  testReliability: 20,
  changeRisk: 15,
};

function parseArgs(argv) {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const skillRoot = path.resolve(scriptDir, '..');
  const options = {
    projectRoot: process.cwd(),
    mode: 'working',
    target: '',
    windowDays: DEFAULT_WINDOW_DAYS,
    profile: DEFAULT_PROFILE,
    out: '',
    outUnavailable: '',
    closureLimit: DEFAULT_CLOSURE_LIMIT,
    skillRoot,
    autoInstall: true,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];

    switch (arg) {
      case '--project-root':
        options.projectRoot = path.resolve(next);
        i += 1;
        break;
      case '--mode':
        options.mode = next;
        i += 1;
        break;
      case '--target':
        options.target = next;
        i += 1;
        break;
      case '--window-days':
        options.windowDays = Number(next);
        i += 1;
        break;
      case '--profile':
        options.profile = next;
        i += 1;
        break;
      case '--out':
        options.out = path.resolve(next);
        i += 1;
        break;
      case '--out-unavailable':
        options.outUnavailable = path.resolve(next);
        i += 1;
        break;
      case '--closure-limit':
        options.closureLimit = Number(next);
        i += 1;
        break;
      case '--skill-root':
        options.skillRoot = path.resolve(next);
        i += 1;
        break;
      case '--auto-install':
        options.autoInstall = next !== 'false';
        i += 1;
        break;
      case '--help':
      case '-h':
        printHelp();
        process.exit(0);
        break;
      default:
        throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!options.out) {
    options.out = path.resolve(options.projectRoot, '.clean-code-inspector/quantitative-metrics.json');
  }

  if (!options.outUnavailable) {
    options.outUnavailable = path.resolve(
      options.projectRoot,
      '.clean-code-inspector/unavailable-metrics.json',
    );
  }

  if (!Number.isFinite(options.windowDays) || options.windowDays <= 0) {
    options.windowDays = DEFAULT_WINDOW_DAYS;
  }

  if (!Number.isFinite(options.closureLimit) || options.closureLimit <= 0) {
    options.closureLimit = DEFAULT_CLOSURE_LIMIT;
  }

  return options;
}

function printHelp() {
  console.log(
    [
      'Usage: node collect-quantitative-metrics.mjs',
      '--project-root <path>',
      '--mode <working|staged|branch|range|files>',
      '--target <value>',
      '--window-days <N>',
      '--profile <balanced|static|strict>',
      '--out <path>',
      '--out-unavailable <path>',
      '--closure-limit <N>',
      '--skill-root <path>',
      '--auto-install <true|false>',
    ].join(' '),
  );
}

function round(value, digits = 2) {
  if (!Number.isFinite(value)) {
    return null;
  }
  const p = 10 ** digits;
  return Math.round(value * p) / p;
}

function clamp(value, min, max) {
  if (!Number.isFinite(value)) {
    return min;
  }
  return Math.min(max, Math.max(min, value));
}

function mean(values) {
  const numbers = values.filter((value) => Number.isFinite(value));
  if (numbers.length === 0) {
    return null;
  }

  return numbers.reduce((acc, value) => acc + value, 0) / numbers.length;
}

function gradeFromScore(score) {
  if (!Number.isFinite(score)) {
    return 'N/A';
  }
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  if (score >= 50) return 'E';
  return 'F';
}

function normalizePath(value) {
  return value.replace(/\\/g, '/');
}

function splitTargetFiles(rawTarget) {
  if (!rawTarget) {
    return [];
  }

  return rawTarget
    .split(/[\s,]+/g)
    .map((item) => item.trim())
    .filter(Boolean);
}

function isCandidateFile(filePath) {
  const normalized = normalizePath(filePath);

  if (
    !/\.(ts|tsx|js|jsx|mts|cts|mjs|cjs)$/.test(normalized) ||
    normalized.endsWith('.d.ts') ||
    normalized.endsWith('.stories.tsx') ||
    normalized.endsWith('.stories.ts') ||
    normalized.endsWith('.stories.jsx') ||
    normalized.endsWith('.stories.js')
  ) {
    return false;
  }

  if (
    normalized.includes('/node_modules/') ||
    normalized.includes('node_modules/') ||
    normalized.includes('/dist/') ||
    normalized.includes('dist/') ||
    normalized.includes('/build/') ||
    normalized.includes('build/') ||
    normalized.includes('/.next/') ||
    normalized.includes('.next/')
  ) {
    return false;
  }

  if (
    normalized.endsWith('.config.ts') ||
    normalized.endsWith('.config.js') ||
    normalized.endsWith('.config.mjs') ||
    normalized.endsWith('.config.cjs')
  ) {
    return false;
  }

  return true;
}

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

function resolveAnalysisTargetsFallback({ projectRoot, mode, target }) {
  const warnings = ['import-closure.disabled:missing-ast-toolchain'];

  if (mode === 'files') {
    const seedFiles = [...new Set(splitTargetFiles(target).map((file) => normalizePath(file)).filter(isCandidateFile))];
    return {
      seedFiles,
      targetFiles: seedFiles,
      truncated: false,
      warnings,
    };
  }

  const modeToArgs = {
    working: ['diff', '--name-only'],
    staged: ['diff', '--cached', '--name-only'],
    branch: ['diff', `${target}...HEAD`, '--name-only'],
    range: ['diff', target, '--name-only'],
  };

  if ((mode === 'branch' || mode === 'range') && !target) {
    warnings.push(`mode=${mode} requires --target`);
    return {
      seedFiles: [],
      targetFiles: [],
      truncated: false,
      warnings,
    };
  }

  const args = modeToArgs[mode] || modeToArgs.working;
  const gitResult = runGit(projectRoot, args);
  if (!gitResult.ok) {
    warnings.push(`failed-to-resolve-changed-files:${gitResult.error}`);
    return {
      seedFiles: [],
      targetFiles: [],
      truncated: false,
      warnings,
    };
  }

  const seedFiles = [...new Set(
    gitResult.output
      .split('\n')
      .map((line) => normalizePath(line.trim()))
      .filter(Boolean)
      .filter(isCandidateFile),
  )].sort((a, b) => a.localeCompare(b));

  return {
    seedFiles,
    targetFiles: seedFiles,
    truncated: false,
    warnings,
  };
}

async function loadModule(modulePath, unavailableMetrics, label) {
  try {
    return await import(modulePath);
  } catch (error) {
    unavailableMetrics.push(`${label}.module-load-failed:${String(error)}`);
    return null;
  }
}

function initializeMetrics() {
  return {
    cyclomatic: null,
    cognitive: null,
    halsteadVolume: null,
    maintainabilityIndex: null,
    locLogical: null,
    locPhysical: null,
    importCount: null,
    stateCount: null,
    anyCount: null,
    assertionCount: null,
    tsIgnoreCount: null,
    lineCoverage: null,
    branchCoverage: null,
    mutationScore: null,
    churnLines: null,
    churnTouches: null,
    fanIn: null,
    fanOut: null,
    instability: null,
    circular: null,
    typeDiagnosticCount: null,
  };
}

function mergeFileMetrics(targetFiles, ...sources) {
  const map = new Map();

  for (const file of targetFiles) {
    map.set(file, initializeMetrics());
  }

  for (const source of sources) {
    for (const [file, partial] of source.entries()) {
      if (!map.has(file)) {
        map.set(file, initializeMetrics());
      }
      Object.assign(map.get(file), partial);
    }
  }

  return map;
}

function calculateHotspotScore(metrics) {
  const cyclomaticScore = clamp((metrics.cyclomatic ?? 0) * 3, 0, 100);
  const cognitiveScore = clamp((metrics.cognitive ?? 0) * 2.5, 0, 100);
  const churnScore = clamp((metrics.churnLines ?? 0) / 8, 0, 100);
  const instabilityScore = clamp((metrics.instability ?? 0) * 100, 0, 100);
  const typeRiskScore = clamp((metrics.anyCount ?? 0) * 10, 0, 100);

  const score =
    cyclomaticScore * 0.3 +
    cognitiveScore * 0.25 +
    churnScore * 0.2 +
    instabilityScore * 0.15 +
    typeRiskScore * 0.1;

  return round(score, 2);
}

function calculateAxes(fileEntries, unavailableMetrics) {
  const axisDetails = {};

  const ccAvg = mean(fileEntries.map((entry) => entry.metrics.cyclomatic));
  const cognitiveAvg = mean(fileEntries.map((entry) => entry.metrics.cognitive));
  const halsteadAvg = mean(fileEntries.map((entry) => entry.metrics.halsteadVolume));
  const miAvg = mean(fileEntries.map((entry) => entry.metrics.maintainabilityIndex));

  const ccRisk = ccAvg == null ? null : clamp((ccAvg / 20) * 100, 0, 100);
  const cognitiveRisk = cognitiveAvg == null ? null : clamp((cognitiveAvg / 25) * 100, 0, 100);
  const halsteadRisk = halsteadAvg == null ? null : clamp((halsteadAvg / 800) * 100, 0, 100);
  const miRisk = miAvg == null ? null : 100 - clamp(miAvg, 0, 100);

  const complexityRisk = mean([ccRisk, cognitiveRisk, halsteadRisk, miRisk]);
  axisDetails.complexity = {
    weight: AXIS_WEIGHTS.complexity,
    score: complexityRisk == null ? null : round(100 - complexityRisk, 2),
  };

  const totalLoc = fileEntries.reduce((acc, entry) => acc + (entry.metrics.locLogical ?? 0), 0);
  const totalAny = fileEntries.reduce((acc, entry) => acc + (entry.metrics.anyCount ?? 0), 0);
  const totalIgnore = fileEntries.reduce((acc, entry) => acc + (entry.metrics.tsIgnoreCount ?? 0), 0);
  const totalAssertion = fileEntries.reduce((acc, entry) => acc + (entry.metrics.assertionCount ?? 0), 0);
  const diagnosticAvg = mean(fileEntries.map((entry) => entry.metrics.typeDiagnosticCount));

  const anyDensity = totalLoc > 0 ? (totalAny / totalLoc) * 1000 : null;
  const ignoreDensity = totalLoc > 0 ? (totalIgnore / totalLoc) * 1000 : null;
  const assertionDensity = totalLoc > 0 ? (totalAssertion / totalLoc) * 1000 : null;

  const typeRisk = mean([
    diagnosticAvg == null ? null : clamp(diagnosticAvg * 5, 0, 100),
    anyDensity == null ? null : clamp(anyDensity * 8, 0, 100),
    ignoreDensity == null ? null : clamp(ignoreDensity * 20, 0, 100),
    assertionDensity == null ? null : clamp(assertionDensity * 5, 0, 100),
  ]);

  axisDetails.typeSafety = {
    weight: AXIS_WEIGHTS.typeSafety,
    score: typeRisk == null ? null : round(100 - typeRisk, 2),
  };

  const lineCoverageAvg = mean(fileEntries.map((entry) => entry.metrics.lineCoverage));
  const branchCoverageAvg = mean(fileEntries.map((entry) => entry.metrics.branchCoverage));
  const mutationScoreAvg = mean(fileEntries.map((entry) => entry.metrics.mutationScore));
  const coverageMutationGap =
    lineCoverageAvg != null && mutationScoreAvg != null
      ? Math.max(0, lineCoverageAvg - mutationScoreAvg)
      : null;

  const weightedCoverageScore = (() => {
    const weightedParts = [
      lineCoverageAvg == null ? null : { value: lineCoverageAvg, weight: 0.35 },
      branchCoverageAvg == null ? null : { value: branchCoverageAvg, weight: 0.35 },
      mutationScoreAvg == null ? null : { value: mutationScoreAvg, weight: 0.3 },
    ].filter(Boolean);

    if (weightedParts.length === 0) {
      return null;
    }

    const totalWeight = weightedParts.reduce((acc, item) => acc + item.weight, 0);
    const score = weightedParts.reduce((acc, item) => acc + item.value * item.weight, 0) / totalWeight;
    const gapPenalty = coverageMutationGap == null ? 0 : clamp(coverageMutationGap / 2, 0, 30);
    return clamp(score - gapPenalty, 0, 100);
  })();

  axisDetails.testReliability = {
    weight: AXIS_WEIGHTS.testReliability,
    score: weightedCoverageScore == null ? null : round(weightedCoverageScore, 2),
  };

  const churnAvg = mean(fileEntries.map((entry) => entry.metrics.churnLines));
  const instabilityAvg = mean(fileEntries.map((entry) => entry.metrics.instability));
  const circularRate = mean(
    fileEntries.map((entry) =>
      typeof entry.metrics.circular === 'boolean' ? (entry.metrics.circular ? 1 : 0) : null,
    ),
  );
  const hotspotAvg = mean(fileEntries.map((entry) => entry.hotspotScore));

  const changeRisk = mean([
    churnAvg == null ? null : clamp((churnAvg / 600) * 100, 0, 100),
    instabilityAvg == null ? null : clamp(instabilityAvg * 100, 0, 100),
    circularRate == null ? null : clamp(circularRate * 100, 0, 100),
    hotspotAvg == null ? null : clamp(hotspotAvg, 0, 100),
  ]);

  axisDetails.changeRisk = {
    weight: AXIS_WEIGHTS.changeRisk,
    score: changeRisk == null ? null : round(100 - changeRisk, 2),
  };

  for (const [axisName, axisInfo] of Object.entries(axisDetails)) {
    if (axisInfo.score == null) {
      unavailableMetrics.push(`axis.${axisName}.not-enough-data`);
    }
  }

  const quantitativeScore = round(
    Object.entries(axisDetails).reduce((acc, [axisName, axisInfo]) => {
      const value = axisInfo.score == null ? 0 : axisInfo.score;
      return acc + (value * AXIS_WEIGHTS[axisName]) / 100;
    }, 0),
    2,
  );

  return {
    axes: axisDetails,
    summary: {
      quantitativeScore,
      quantitativeGrade: gradeFromScore(quantitativeScore),
    },
  };
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const unavailableMetrics = [];

  const toolchain = ensureToolchain({
    skillDir: options.skillRoot,
    autoInstall: options.autoInstall,
  });

  if (!toolchain.ready) {
    unavailableMetrics.push(
      `toolchain.missing:${toolchain.missingPackages.join(',') || 'unknown-packages'}`,
    );
  }
  unavailableMetrics.push(...toolchain.logs);

  let targets;
  if (toolchain.ready) {
    const resolverModule = await loadModule(
      './utils/file-target-resolver.mjs',
      unavailableMetrics,
      'resolver',
    );
    if (resolverModule?.resolveAnalysisTargets) {
      targets = resolverModule.resolveAnalysisTargets({
        projectRoot: options.projectRoot,
        mode: options.mode,
        target: options.target,
        closureLimit: options.closureLimit,
      });
    } else {
      targets = resolveAnalysisTargetsFallback({
        projectRoot: options.projectRoot,
        mode: options.mode,
        target: options.target,
      });
    }
  } else {
    targets = resolveAnalysisTargetsFallback({
      projectRoot: options.projectRoot,
      mode: options.mode,
      target: options.target,
    });
  }

  unavailableMetrics.push(...targets.warnings);
  if (targets.truncated) {
    unavailableMetrics.push(
      `import-closure.truncated: limit=${options.closureLimit}, seeds=${targets.seedFiles.length}`,
    );
  }

  const targetFiles = targets.targetFiles;

  const astResult = { byFile: new Map(), unavailableMetrics: ['ast.skipped:toolchain-not-ready'] };
  const eslintResult = { byFile: new Map(), unavailableMetrics: ['eslint.skipped:toolchain-not-ready'] };
  const typeResult = { byFile: new Map(), unavailableMetrics: ['typescript.skipped:toolchain-not-ready'] };
  const dependencyResult = {
    byFile: new Map(),
    unavailableMetrics: ['dependency-cruiser.skipped:toolchain-not-ready'],
  };
  let churnResult = { byFile: new Map(), unavailableMetrics: [] };
  const testResult = { byFile: new Map(), unavailableMetrics: ['test-reliability.skipped:toolchain-not-ready'] };

  if (toolchain.ready) {
    const astModule = await loadModule(
      './analyzers/ast-structural-metrics.mjs',
      unavailableMetrics,
      'ast-structural-metrics',
    );
    if (astModule?.collectAstStructuralMetrics) {
      Object.assign(astResult, astModule.collectAstStructuralMetrics({
        projectRoot: options.projectRoot,
        files: targetFiles,
      }));
    }

    const eslintModule = await loadModule(
      './analyzers/eslint-complexity-metrics.mjs',
      unavailableMetrics,
      'eslint-complexity-metrics',
    );
    if (eslintModule?.collectEslintComplexityMetrics) {
      Object.assign(eslintResult, await eslintModule.collectEslintComplexityMetrics({
        projectRoot: options.projectRoot,
        files: targetFiles,
      }));
    }

    const typeModule = await loadModule(
      './analyzers/type-safety-metrics.mjs',
      unavailableMetrics,
      'type-safety-metrics',
    );
    if (typeModule?.collectTypeSafetyMetrics) {
      Object.assign(typeResult, await typeModule.collectTypeSafetyMetrics({
        projectRoot: options.projectRoot,
        files: targetFiles,
      }));
    }

    const dependencyModule = await loadModule(
      './analyzers/dependency-metrics.mjs',
      unavailableMetrics,
      'dependency-metrics',
    );
    if (dependencyModule?.collectDependencyMetrics) {
      Object.assign(dependencyResult, dependencyModule.collectDependencyMetrics({
        projectRoot: options.projectRoot,
        skillRoot: options.skillRoot,
        files: targetFiles,
      }));
    }

    const testModule = await loadModule(
      './analyzers/test-reliability-metrics.mjs',
      unavailableMetrics,
      'test-reliability-metrics',
    );
    if (testModule?.collectTestReliabilityMetrics) {
      Object.assign(testResult, await testModule.collectTestReliabilityMetrics({
        projectRoot: options.projectRoot,
        files: targetFiles,
      }));
    }
  }

  const churnModule = await loadModule(
    './analyzers/churn-metrics.mjs',
    unavailableMetrics,
    'churn-metrics',
  );
  if (churnModule?.collectChurnMetrics) {
    churnResult = churnModule.collectChurnMetrics({
      projectRoot: options.projectRoot,
      files: targetFiles,
      windowDays: options.windowDays,
    });
  }
  
  unavailableMetrics.push(...astResult.unavailableMetrics);
  unavailableMetrics.push(...eslintResult.unavailableMetrics);
  unavailableMetrics.push(...typeResult.unavailableMetrics);
  unavailableMetrics.push(...dependencyResult.unavailableMetrics);
  unavailableMetrics.push(...churnResult.unavailableMetrics);
  unavailableMetrics.push(...testResult.unavailableMetrics);

  const mergedMetrics = mergeFileMetrics(
    targetFiles,
    astResult.byFile,
    eslintResult.byFile,
    typeResult.byFile,
    dependencyResult.byFile,
    churnResult.byFile,
    testResult.byFile,
  );

  for (const [filePath, metrics] of mergedMetrics) {
    if (metrics.cyclomatic == null && metrics.cyclomaticApprox != null) {
      metrics.cyclomatic = metrics.cyclomaticApprox;
    }
    delete metrics.cyclomaticApprox;
  }

  const fileEntries = [...mergedMetrics.entries()].map(([filePath, metrics]) => ({
    path: normalizePath(filePath),
    metrics,
    hotspotScore: calculateHotspotScore(metrics),
  }));

  const { axes, summary } = calculateAxes(fileEntries, unavailableMetrics);

  const payload = {
    schemaVersion: '2.1.0',
    generatedAt: new Date().toISOString(),
    profile: options.profile,
    analysisMode: toolchain.ready ? 'full' : 'degraded',
    analysisScope: {
      mode: options.mode,
      target: options.target,
      windowDays: options.windowDays,
      closureLimit: options.closureLimit,
      seedFileCount: targets.seedFiles.length,
      analyzedFileCount: fileEntries.length,
    },
    files: fileEntries,
    axes,
    summary,
    unavailableMetrics: [...new Set(unavailableMetrics)].filter(Boolean),
  };

  writeJson(options.out, payload);
  writeJson(options.outUnavailable, { unavailableMetrics: payload.unavailableMetrics });

  console.log(`Generated: ${options.out}`);
  console.log(`Generated: ${options.outUnavailable}`);
}

main().catch((error) => {
  console.error('Failed to collect quantitative metrics.');
  console.error(error instanceof Error ? error.stack ?? error.message : String(error));
  process.exit(1);
});
