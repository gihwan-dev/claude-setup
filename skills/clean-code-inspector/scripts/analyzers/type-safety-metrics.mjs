import path from 'node:path';
import fg from 'fast-glob';
import ts from 'typescript';

function normalizePath(value) {
  return value.replace(/\\/g, '/');
}

async function findTsConfig(projectRoot) {
  const direct = path.resolve(projectRoot, 'tsconfig.json');
  if (ts.sys.fileExists(direct)) {
    return direct;
  }

  const candidates = await fg(['**/tsconfig.json'], {
    cwd: projectRoot,
    dot: false,
    absolute: true,
    ignore: ['**/node_modules/**', '**/dist/**', '**/build/**', '**/.next/**'],
  });

  if (candidates.length === 0) {
    return null;
  }

  candidates.sort((a, b) => a.length - b.length);
  return candidates[0];
}

export async function collectTypeSafetyMetrics({ projectRoot, files }) {
  const byFile = new Map();
  const unavailableMetrics = [];

  if (files.length === 0) {
    return { byFile, unavailableMetrics };
  }

  const tsConfigPath = await findTsConfig(projectRoot);
  if (!tsConfigPath) {
    unavailableMetrics.push('typescript.tsconfig-not-found');
    return { byFile, unavailableMetrics };
  }

  let parsed;
  try {
    const configFile = ts.readConfigFile(tsConfigPath, ts.sys.readFile);
    if (configFile.error) {
      throw new Error(ts.flattenDiagnosticMessageText(configFile.error.messageText, '\n'));
    }

    parsed = ts.parseJsonConfigFileContent(
      configFile.config,
      ts.sys,
      path.dirname(tsConfigPath),
      undefined,
      tsConfigPath,
    );
  } catch (error) {
    unavailableMetrics.push(`typescript.tsconfig-parse-failed:${String(error)}`);
    return { byFile, unavailableMetrics };
  }

  let program;
  try {
    program = ts.createProgram({
      rootNames: parsed.fileNames,
      options: parsed.options,
      projectReferences: parsed.projectReferences,
    });
  } catch (error) {
    unavailableMetrics.push(`typescript.program-create-failed:${String(error)}`);
    return { byFile, unavailableMetrics };
  }

  const diagnostics = ts.getPreEmitDiagnostics(program);
  const diagnosticCountByFile = new Map();

  for (const diagnostic of diagnostics) {
    const fileName = diagnostic.file?.fileName;
    if (!fileName) {
      continue;
    }

    const relative = normalizePath(path.relative(projectRoot, fileName));
    diagnosticCountByFile.set(relative, (diagnosticCountByFile.get(relative) ?? 0) + 1);
  }

  for (const relative of files) {
    byFile.set(relative, {
      typeDiagnosticCount: diagnosticCountByFile.get(relative) ?? 0,
    });
  }

  return {
    byFile,
    unavailableMetrics,
  };
}
