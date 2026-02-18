#!/usr/bin/env node

import path from 'node:path';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

const REQUIRED_PACKAGES = [
  '@typescript-eslint/parser',
  '@typescript-eslint/typescript-estree',
  'dependency-cruiser',
  'eslint',
  'eslint-plugin-sonarjs',
  'fast-glob',
  'istanbul-lib-coverage',
  'typhonjs-escomplex',
  'typescript',
];

function parseArgs(argv) {
  const scriptDir = path.dirname(fileURLToPath(import.meta.url));
  const options = {
    skillDir: path.resolve(scriptDir, '..'),
    autoInstall: true,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = argv[i + 1];

    if (arg === '--skill-dir') {
      options.skillDir = path.resolve(next);
      i += 1;
      continue;
    }

    if (arg === '--auto-install') {
      options.autoInstall = next !== 'false';
      i += 1;
      continue;
    }

    if (arg === '--help' || arg === '-h') {
      printHelp();
      process.exit(0);
    }

    throw new Error(`Unknown argument: ${arg}`);
  }

  return options;
}

function printHelp() {
  console.log(
    'Usage: node ensure-toolchain.mjs --skill-dir <path> --auto-install <true|false>',
  );
}

function isPnpmAvailable() {
  const result = spawnSync('pnpm', ['--version'], {
    encoding: 'utf8',
  });

  return result.status === 0;
}

function findMissingPackages(skillDir) {
  const requireFromSkill = createRequire(path.resolve(skillDir, 'package.json'));
  const missing = [];

  for (const packageName of REQUIRED_PACKAGES) {
    if (packageName === 'dependency-cruiser') {
      const depCruiseBin = path.resolve(skillDir, 'node_modules', '.bin', 'depcruise');
      if (!fs.existsSync(depCruiseBin)) {
        missing.push(packageName);
      }
      continue;
    }

    try {
      requireFromSkill.resolve(packageName);
    } catch {
      missing.push(packageName);
    }
  }

  return missing;
}

function runInstall(skillDir, frozenLockfile) {
  const args = ['--dir', skillDir, 'install'];
  if (frozenLockfile) {
    args.push('--frozen-lockfile');
  }

  return spawnSync('pnpm', args, {
    encoding: 'utf8',
  });
}

export function ensureToolchain({ skillDir, autoInstall = true }) {
  const pnpmAvailable = isPnpmAvailable();
  let missingPackages = findMissingPackages(skillDir);
  const logs = [];
  let installAttempted = false;
  let installSucceeded = false;

  if (missingPackages.length > 0 && autoInstall && pnpmAvailable) {
    installAttempted = true;

    let installResult = runInstall(skillDir, true);
    if (installResult.status !== 0) {
      logs.push(`pnpm install --frozen-lockfile failed: ${(installResult.stderr || '').trim()}`);
      installResult = runInstall(skillDir, false);
    }

    if (installResult.status === 0) {
      installSucceeded = true;
      logs.push('pnpm install succeeded');
    } else {
      logs.push(`pnpm install failed: ${(installResult.stderr || installResult.stdout || '').trim()}`);
    }

    missingPackages = findMissingPackages(skillDir);
  }

  if (missingPackages.length > 0 && !pnpmAvailable) {
    logs.push('pnpm is not available');
  }

  return {
    ready: missingPackages.length === 0,
    missingPackages,
    installAttempted,
    installSucceeded,
    pnpmAvailable,
    logs,
  };
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  const summary = ensureToolchain(options);
  console.log(`${JSON.stringify(summary, null, 2)}\n`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    main();
  } catch (error) {
    console.error('Failed to ensure toolchain.');
    console.error(error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}
