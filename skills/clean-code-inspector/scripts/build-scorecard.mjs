#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const SCHEMA_VERSION = '2.0.0';
const HOTSPOT_RATIO = 0.2;
const QUANT_WEIGHT = 0.85;
const QUAL_WEIGHT = 0.15;
const FAIL_FLOOR = 50;

const CRITERIA = [
  { id: 'intent_clarity', label: 'Intent Clarity' },
  { id: 'local_reasoning', label: 'Local Reasoning' },
  { id: 'failure_semantics', label: 'Failure Semantics' },
  { id: 'boundary_discipline', label: 'Boundary Discipline' },
  { id: 'test_oracle_quality', label: 'Test Oracle Quality' },
];

function parseArgs(argv) {
  const options = {
    profile: 'balanced',
    outJson: 'clean-code-inspect-result.json',
    outMd: 'clean-code-inspect-result.md',
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];

    switch (arg) {
      case '--quant':
        options.quant = next;
        i += 1;
        break;
      case '--qual':
        options.qual = next;
        i += 1;
        break;
      case '--profile':
        options.profile = next;
        i += 1;
        break;
      case '--out-json':
        options.outJson = next;
        i += 1;
        break;
      case '--out-md':
        options.outMd = next;
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

  if (!options.quant) {
    throw new Error('Argument --quant is required.');
  }

  return {
    ...options,
    quant: path.resolve(options.quant),
    qual: options.qual ? path.resolve(options.qual) : null,
    outJson: path.resolve(options.outJson),
    outMd: path.resolve(options.outMd),
  };
}

function printHelp() {
  console.log('Usage: node build-scorecard.mjs --quant <quant.json> [--qual <qual.json>] [--profile balanced] [--out-json path] [--out-md path]');
}

function isFiniteNumber(value) {
  return typeof value === 'number' && Number.isFinite(value);
}

function clamp(value, min, max) {
  if (!isFiniteNumber(value)) {
    return min;
  }
  return Math.min(max, Math.max(min, value));
}

function round(value, digits = 2) {
  if (!isFiniteNumber(value)) {
    return value;
  }
  const p = 10 ** digits;
  return Math.round(value * p) / p;
}

function mean(values) {
  const numbers = values.filter(isFiniteNumber);
  if (numbers.length === 0) {
    return null;
  }
  return numbers.reduce((acc, value) => acc + value, 0) / numbers.length;
}

function safeReadJson(filePath, fallback = null) {
  if (!filePath || !fs.existsSync(filePath)) {
    return fallback;
  }

  const raw = fs.readFileSync(filePath, 'utf8');
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`Failed to parse JSON: ${filePath}\n${String(error)}`);
  }
}

function getAt(obj, pathExpr) {
  const keys = pathExpr.split('.');
  let current = obj;
  for (const key of keys) {
    if (current == null || typeof current !== 'object' || !(key in current)) {
      return undefined;
    }
    current = current[key];
  }
  return current;
}

function pickNumber(obj, paths, fallback = null) {
  for (const pathExpr of paths) {
    const value = getAt(obj, pathExpr);
    if (isFiniteNumber(value)) {
      return value;
    }
  }
  return fallback;
}

function gradeFromScore(score) {
  if (!isFiniteNumber(score)) {
    return 'N/A';
  }
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  if (score >= 50) return 'E';
  return 'F';
}

function normalizeAxes(axes) {
  if (!axes) {
    return [];
  }

  if (Array.isArray(axes)) {
    return axes
      .map((axis) => {
        if (!axis || typeof axis !== 'object') {
          return null;
        }
        const name = axis.name ?? axis.id ?? null;
        const score = isFiniteNumber(axis.score) ? axis.score : null;
        const weight = isFiniteNumber(axis.weight) ? axis.weight : 1;
        if (!name || score == null) {
          return null;
        }
        return { name, score: clamp(score, 0, 100), weight: Math.max(weight, 0) };
      })
      .filter(Boolean);
  }

  if (typeof axes === 'object') {
    return Object.entries(axes)
      .map(([name, value]) => {
        if (isFiniteNumber(value)) {
          return { name, score: clamp(value, 0, 100), weight: 1 };
        }
        if (value && typeof value === 'object' && isFiniteNumber(value.score)) {
          return {
            name,
            score: clamp(value.score, 0, 100),
            weight: isFiniteNumber(value.weight) ? Math.max(value.weight, 0) : 1,
          };
        }
        return null;
      })
      .filter(Boolean);
  }

  return [];
}

function resolveQuantitativeScore(quantData) {
  const directScore = pickNumber(quantData, [
    'quantitativeScore',
    'summary.quantitativeScore',
    'summary.overallScore',
    'overallScore',
    'score',
  ]);

  if (directScore != null) {
    const score = clamp(directScore, 0, 100);
    const grade =
      getAt(quantData, 'summary.quantitativeGrade') ??
      getAt(quantData, 'summary.overallGrade') ??
      getAt(quantData, 'overallGrade') ??
      gradeFromScore(score);

    return {
      score: round(score, 2),
      grade,
      source: 'direct',
      axes: normalizeAxes(quantData.axes),
    };
  }

  const axes = normalizeAxes(quantData.axes);
  if (axes.length === 0) {
    return {
      score: 0,
      grade: 'F',
      source: 'fallback-zero',
      axes: [],
    };
  }

  const totalWeight = axes.reduce((acc, axis) => acc + axis.weight, 0);
  const weighted =
    totalWeight > 0
      ? axes.reduce((acc, axis) => acc + axis.score * axis.weight, 0) / totalWeight
      : mean(axes.map((axis) => axis.score)) ?? 0;

  const score = round(clamp(weighted, 0, 100), 2);
  return {
    score,
    grade: gradeFromScore(score),
    source: 'axes-weighted',
    axes,
  };
}

function normalizeFiles(files) {
  if (!Array.isArray(files)) {
    return [];
  }

  return files
    .map((file) => {
      if (!file || typeof file !== 'object') {
        return null;
      }
      const filePath = file.path ?? file.file ?? file.name ?? null;
      if (!filePath || typeof filePath !== 'string') {
        return null;
      }
      return {
        ...file,
        path: filePath,
      };
    })
    .filter(Boolean);
}

function deriveHotspotScore(file) {
  const direct = pickNumber(file, ['hotspotScore', 'riskScore', 'changeRiskScore']);
  if (direct != null) {
    return clamp(direct, 0, 100);
  }

  const metrics = file.metrics && typeof file.metrics === 'object' ? file.metrics : {};

  const cyclomatic = pickNumber(file, ['cyclomaticComplexity', 'cc']) ?? pickNumber(metrics, ['ccP95', 'cc', 'cyclomaticComplexity']);
  const cognitive = pickNumber(file, ['cognitiveComplexity']) ?? pickNumber(metrics, ['cognitiveP95', 'cognitiveComplexity']);
  const churn = pickNumber(file, ['churnLines90d', 'churn']) ?? pickNumber(metrics, ['churnLines90d', 'churnLines', 'churn']);
  const typeRisk =
    pickNumber(file, ['typeRiskScore']) ??
    pickNumber(metrics, ['typeRiskScore']) ??
    (() => {
      const anyCount = pickNumber(file, ['anyCount']) ?? pickNumber(metrics, ['anyCount']) ?? 0;
      const ignoreCount = pickNumber(file, ['tsIgnoreCount']) ?? pickNumber(metrics, ['tsIgnoreCount']) ?? 0;
      return anyCount * 8 + ignoreCount * 12;
    })();

  const ccScore = cyclomatic != null ? clamp(cyclomatic * 3, 0, 100) : 0;
  const cognitiveScore = cognitive != null ? clamp(cognitive * 2.5, 0, 100) : 0;
  const churnScore = churn != null ? clamp(churn / 8, 0, 100) : 0;
  const typeScore = typeRisk != null ? clamp(typeRisk, 0, 100) : 0;

  const blended = ccScore * 0.35 + cognitiveScore * 0.25 + churnScore * 0.25 + typeScore * 0.15;
  return round(clamp(blended, 0, 100), 2);
}

function selectHotspotFiles(files) {
  if (files.length === 0) {
    return [];
  }

  const scored = files
    .map((file) => ({
      path: file.path,
      score: deriveHotspotScore(file),
    }))
    .sort((a, b) => b.score - a.score);

  const topCount = Math.max(1, Math.ceil(scored.length * HOTSPOT_RATIO));
  return scored.slice(0, topCount);
}

function normalizeEvidence(entry, fallbackFile = null) {
  if (!entry) {
    return null;
  }

  if (typeof entry === 'string') {
    return {
      file: fallbackFile,
      line: null,
      detail: entry,
    };
  }

  if (typeof entry === 'object') {
    const line = isFiniteNumber(entry.line) ? Math.max(1, Math.trunc(entry.line)) : null;
    return {
      file: typeof entry.file === 'string' ? entry.file : fallbackFile,
      line,
      detail: typeof entry.detail === 'string' ? entry.detail : typeof entry.note === 'string' ? entry.note : '',
    };
  }

  return null;
}

function normalizeFlag(flag, fallbackFile = null) {
  if (!flag || typeof flag !== 'object') {
    return null;
  }

  return {
    type: typeof flag.type === 'string' ? flag.type : 'unknown',
    message: typeof flag.message === 'string' ? flag.message : '',
    file: typeof flag.file === 'string' ? flag.file : fallbackFile,
    line: isFiniteNumber(flag.line) ? Math.max(1, Math.trunc(flag.line)) : null,
    severity: typeof flag.severity === 'string' ? flag.severity : 'warning',
  };
}

function dedupeFlags(flags) {
  const map = new Map();
  for (const flag of flags) {
    if (!flag) continue;
    const key = `${flag.type}|${flag.file ?? ''}|${flag.line ?? ''}|${flag.message ?? ''}`;
    if (!map.has(key)) {
      map.set(key, flag);
    }
  }
  return [...map.values()];
}

function buildQualitativeOverlay(qualData, eligibleHotspotFiles) {
  const hotspotSet = new Set(eligibleHotspotFiles.map((item) => item.path));
  const evaluations = Array.isArray(qualData?.evaluations) ? qualData.evaluations : [];

  const criterionBuckets = new Map(
    CRITERIA.map((criterion) => [
      criterion.id,
      {
        id: criterion.id,
        label: criterion.label,
        scores: [],
        evidences: [],
        naReasons: [],
      },
    ]),
  );

  const collectedFlags = [];
  const evidenceRecords = [];

  for (const evaluation of evaluations) {
    if (!evaluation || typeof evaluation !== 'object') {
      continue;
    }

    const filePath = typeof evaluation.file === 'string' ? evaluation.file : null;
    if (!filePath || !hotspotSet.has(filePath)) {
      continue;
    }

    const rawCriteria = Array.isArray(evaluation.criteria) ? evaluation.criteria : [];

    for (const criterion of CRITERIA) {
      const bucket = criterionBuckets.get(criterion.id);
      const raw = rawCriteria.find((item) => item && item.id === criterion.id);

      if (!raw || typeof raw !== 'object') {
        bucket.naReasons.push('항목 누락');
        continue;
      }

      const evidences = (Array.isArray(raw.evidence) ? raw.evidence : [])
        .map((entry) => normalizeEvidence(entry, filePath))
        .filter(Boolean);

      if (evidences.length < 2) {
        bucket.naReasons.push('근거 2개 미만');
        continue;
      }

      if (!isFiniteNumber(raw.score)) {
        bucket.naReasons.push('점수 누락');
        continue;
      }

      const score = clamp(raw.score, 0, 4);
      bucket.scores.push(score);
      bucket.evidences.push(...evidences);
      evidenceRecords.push(
        ...evidences.map((evidence) => ({
          criterionId: criterion.id,
          criterionLabel: criterion.label,
          ...evidence,
        })),
      );

      if (criterion.id === 'boundary_discipline' && score === 0) {
        collectedFlags.push({
          type: 'boundary_discipline_violation',
          message: 'Boundary Discipline 점수 0점',
          file: filePath,
          line: evidences[0]?.line ?? null,
          severity: 'critical',
        });
      }

      if (criterion.id === 'failure_semantics' && score === 0) {
        collectedFlags.push({
          type: 'missing_failure_semantics',
          message: 'Failure Semantics 점수 0점',
          file: filePath,
          line: evidences[0]?.line ?? null,
          severity: 'critical',
        });
      }
    }

    const rawFlags = Array.isArray(evaluation.criticalFlags) ? evaluation.criticalFlags : [];
    collectedFlags.push(...rawFlags.map((flag) => normalizeFlag(flag, filePath)).filter(Boolean));
  }

  const rootFlags = Array.isArray(qualData?.criticalFlags) ? qualData.criticalFlags : [];
  collectedFlags.push(...rootFlags.map((flag) => normalizeFlag(flag, null)).filter(Boolean));

  const criteria = CRITERIA.map((criterion) => {
    const bucket = criterionBuckets.get(criterion.id);
    const avg = mean(bucket.scores);
    const evidenceCount = bucket.evidences.length;

    if (avg == null) {
      return {
        id: criterion.id,
        label: criterion.label,
        score: null,
        status: 'N/A',
        evidenceCount,
        reason: bucket.naReasons[0] ?? '평가 데이터 없음',
      };
    }

    return {
      id: criterion.id,
      label: criterion.label,
      score: round(avg, 2),
      status: 'scored',
      evidenceCount,
    };
  });

  const criterionScores = criteria.map((criterion) => criterion.score).filter(isFiniteNumber);
  const qualitativeAverage = mean(criterionScores);
  const qualitativeScore = qualitativeAverage == null ? null : round(qualitativeAverage * 25, 2);

  return {
    criteria,
    score: qualitativeScore,
    evidence: evidenceRecords,
    criticalFlags: dedupeFlags(collectedFlags),
  };
}

function buildCrossSignals(quantitativeScore, qualitativeScore, criteria, criticalFlags) {
  const signals = [];

  if (qualitativeScore == null) {
    signals.push('정성 오버레이 점수는 N/A입니다. 근거 부족 또는 입력 누락을 확인하세요.');
    return signals;
  }

  if (quantitativeScore >= 80 && qualitativeScore < 60) {
    signals.push('정량 점수는 높지만 정성 점수가 낮습니다. 코드 의도/경계 설명력이 부족할 가능성이 있습니다.');
  }

  if (quantitativeScore < 60 && qualitativeScore >= 75) {
    signals.push('정성 품질은 양호하지만 정량 지표가 낮습니다. 복잡도/변경 리스크를 우선 줄이세요.');
  }

  const boundary = criteria.find((criterion) => criterion.id === 'boundary_discipline');
  if (boundary && isFiniteNumber(boundary.score) && boundary.score <= 1) {
    signals.push('Boundary Discipline이 낮습니다. 레이어 침범/관심사 혼합을 의심해야 합니다.');
  }

  const failure = criteria.find((criterion) => criterion.id === 'failure_semantics');
  if (failure && isFiniteNumber(failure.score) && failure.score <= 1) {
    signals.push('Failure Semantics가 낮습니다. 실패 처리 정책(에러/타임아웃/empty state) 명시가 필요합니다.');
  }

  if (criticalFlags.length > 0) {
    signals.push(`Critical Flag ${criticalFlags.length}건이 감지되었습니다. 등급과 별개로 우선 확인이 필요합니다.`);
  }

  if (signals.length === 0) {
    signals.push('정량/정성 지표 간 큰 충돌 신호는 감지되지 않았습니다.');
  }

  return signals;
}

function renderMarkdown(result) {
  const lines = [];

  lines.push('# Clean Code Inspect Result');
  lines.push('');
  lines.push('## 요약');
  lines.push('');
  lines.push(`- 프로필: ${result.profile}`);
  lines.push(`- 정량 점수: ${result.quantitative.score} (${result.quantitative.grade})`);
  lines.push(
    `- 정성 점수: ${result.qualitativeOverlay.score == null ? 'N/A' : `${result.qualitativeOverlay.score} (${gradeFromScore(result.qualitativeOverlay.score)})`}`,
  );
  lines.push(`- 최종 점수: ${result.final.score} (${result.final.grade})`);
  lines.push(`- Hotspot 대상: ${result.qualitativeOverlay.hotspotSelection.eligibleFileCount}/${result.qualitativeOverlay.hotspotSelection.totalFileCount}`);
  lines.push('');

  lines.push('## 정성 오버레이 결과');
  lines.push('');
  lines.push('| 항목 | 점수(0~4) | 상태 | 근거 수 | 비고 |');
  lines.push('|---|---:|---|---:|---|');
  for (const criterion of result.qualitativeOverlay.criteria) {
    lines.push(
      `| ${criterion.label} | ${criterion.score == null ? 'N/A' : criterion.score.toFixed(2)} | ${criterion.status} | ${criterion.evidenceCount} | ${criterion.reason ?? ''} |`,
    );
  }
  lines.push('');

  if (result.qualitativeOverlay.hotspotSelection.files.length > 0) {
    lines.push('### Hotspot 대상 파일');
    lines.push('');
    for (const file of result.qualitativeOverlay.hotspotSelection.files) {
      lines.push(`- ${file.path} (hotspotScore: ${file.score})`);
    }
    lines.push('');
  }

  lines.push('## 정량-정성 교차 시그널');
  lines.push('');
  for (const signal of result.crossSignals) {
    lines.push(`- ${signal}`);
  }
  lines.push('');

  lines.push('## Critical Flags');
  lines.push('');
  if (result.criticalFlags.length === 0) {
    lines.push('- 없음');
  } else {
    for (const flag of result.criticalFlags) {
      const location = [flag.file, isFiniteNumber(flag.line) ? `:${flag.line}` : ''].join('');
      lines.push(`- [${flag.type}] ${flag.message}${location ? ` (${location})` : ''}`);
    }
  }
  lines.push('');

  if (result.unavailableMetrics.length > 0) {
    lines.push('## Unavailable Metrics');
    lines.push('');
    for (const metric of result.unavailableMetrics) {
      lines.push(`- ${metric}`);
    }
    lines.push('');
  }

  return `${lines.join('\n')}\n`;
}

function writeFile(targetPath, content) {
  fs.mkdirSync(path.dirname(targetPath), { recursive: true });
  fs.writeFileSync(targetPath, content, 'utf8');
}

function main() {
  const options = parseArgs(process.argv.slice(2));

  const quantData = safeReadJson(options.quant);
  if (!quantData) {
    throw new Error(`Quantitative input not found: ${options.quant}`);
  }

  const qualData = safeReadJson(options.qual, null);
  const quantitative = resolveQuantitativeScore(quantData);
  const files = normalizeFiles(quantData.files);
  const hotspotFiles = selectHotspotFiles(files);

  const qualitativeOverlay = buildQualitativeOverlay(qualData, hotspotFiles);
  const unavailableMetrics = [];

  const externalUnavailable = Array.isArray(quantData.unavailableMetrics)
    ? quantData.unavailableMetrics
    : [];
  for (const metric of externalUnavailable) {
    if (typeof metric === 'string') {
      unavailableMetrics.push(metric);
    } else if (metric && typeof metric === 'object' && typeof metric.message === 'string') {
      unavailableMetrics.push(metric.message);
    }
  }

  if (!qualData) {
    unavailableMetrics.push('qualitative-overlay-input: --qual 파일이 제공되지 않음');
  }

  let finalScore = quantitative.score;
  const finalNotes = [];

  if (isFiniteNumber(qualitativeOverlay.score)) {
    finalScore = round(quantitative.score * QUANT_WEIGHT + qualitativeOverlay.score * QUAL_WEIGHT, 2);
  } else {
    finalNotes.push('정성 점수가 N/A이므로 최종 점수는 정량 점수만 사용했습니다.');
  }

  const quantitativeGrade = gradeFromScore(quantitative.score);
  let finalGrade = gradeFromScore(finalScore);

  if (quantitative.score >= FAIL_FLOOR && finalScore < FAIL_FLOOR) {
    finalScore = FAIL_FLOOR;
    finalGrade = gradeFromScore(finalScore);
    finalNotes.push('정성 단독 fail 금지 규칙에 따라 최종 점수를 보정했습니다.');
  }

  const criticalFlags = dedupeFlags(qualitativeOverlay.criticalFlags);
  const crossSignals = buildCrossSignals(
    quantitative.score,
    qualitativeOverlay.score,
    qualitativeOverlay.criteria,
    criticalFlags,
  );

  const result = {
    schemaVersion: SCHEMA_VERSION,
    generatedAt: new Date().toISOString(),
    profile: options.profile,
    weights: {
      quantitative: QUANT_WEIGHT,
      qualitative: QUAL_WEIGHT,
    },
    quantitative: {
      score: quantitative.score,
      grade: quantitativeGrade,
      source: quantitative.source,
      axes: quantitative.axes,
    },
    qualitativeOverlay: {
      hotspotSelection: {
        totalFileCount: files.length,
        eligibleFileCount: hotspotFiles.length,
        topPercent: HOTSPOT_RATIO * 100,
        files: hotspotFiles,
      },
      criteria: qualitativeOverlay.criteria,
      score: qualitativeOverlay.score,
      evidence: qualitativeOverlay.evidence,
    },
    final: {
      score: finalScore,
      grade: finalGrade,
      notes: finalNotes,
    },
    crossSignals,
    criticalFlags,
    unavailableMetrics,
    files,
  };

  const markdown = renderMarkdown(result);

  writeFile(options.outJson, `${JSON.stringify(result, null, 2)}\n`);
  writeFile(options.outMd, markdown);

  console.log(`Generated: ${options.outJson}`);
  console.log(`Generated: ${options.outMd}`);
}

try {
  main();
} catch (error) {
  console.error('Failed to build scorecard.');
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
}
