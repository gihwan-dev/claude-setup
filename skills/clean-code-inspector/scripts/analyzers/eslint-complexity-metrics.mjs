import path from 'node:path';
import { ESLint } from 'eslint';
import tsParser from '@typescript-eslint/parser';
import sonarjs from 'eslint-plugin-sonarjs';

function parseComplexityValue(ruleId, message) {
  if (!message || typeof message !== 'string') {
    return null;
  }

  if (ruleId === 'complexity') {
    const match = message.match(/complexity of\s+(\d+)/i);
    return match ? Number(match[1]) : null;
  }

  if (ruleId === 'sonarjs/cognitive-complexity') {
    const match = message.match(/from\s+(\d+)\s+to/i);
    return match ? Number(match[1]) : null;
  }

  return null;
}

export async function collectEslintComplexityMetrics({ projectRoot, files }) {
  const byFile = new Map();
  const unavailableMetrics = [];

  if (files.length === 0) {
    return { byFile, unavailableMetrics };
  }

  let eslint;
  try {
    eslint = new ESLint({
      cwd: projectRoot,
      ignore: false,
      overrideConfigFile: true,
      overrideConfig: [
        {
          files: ['**/*.{ts,tsx,js,jsx,mts,cts,mjs,cjs}'],
          languageOptions: {
            parser: tsParser,
            parserOptions: {
              ecmaVersion: 'latest',
              sourceType: 'module',
              ecmaFeatures: { jsx: true },
            },
          },
          plugins: {
            sonarjs,
          },
          rules: {
            complexity: ['error', { max: 0 }],
            'sonarjs/cognitive-complexity': ['error', 0],
          },
        },
      ],
    });
  } catch (error) {
    unavailableMetrics.push(`eslint.init-failed:${String(error)}`);
    return { byFile, unavailableMetrics };
  }

  const absoluteFiles = files.map((relativePath) => path.resolve(projectRoot, relativePath));

  let lintResults;
  try {
    lintResults = await eslint.lintFiles(absoluteFiles);
  } catch (error) {
    unavailableMetrics.push(`eslint.run-failed:${String(error)}`);
    return { byFile, unavailableMetrics };
  }

  for (const result of lintResults) {
    const relativePath = path.relative(projectRoot, result.filePath).replace(/\\/g, '/');

    let cyclomatic = null;
    let cognitive = null;

    for (const message of result.messages) {
      const value = parseComplexityValue(message.ruleId, message.message);
      if (value == null) {
        continue;
      }

      if (message.ruleId === 'complexity') {
        cyclomatic = cyclomatic == null ? value : Math.max(cyclomatic, value);
      }

      if (message.ruleId === 'sonarjs/cognitive-complexity') {
        cognitive = cognitive == null ? value : Math.max(cognitive, value);
      }
    }

    byFile.set(relativePath, {
      cyclomatic,
      cognitive,
    });
  }

  return {
    byFile,
    unavailableMetrics,
  };
}
