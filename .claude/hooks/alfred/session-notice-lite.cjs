#!/usr/bin/env node
'use strict';

/**
 * @CODE:HOOK-003 | @CODE:HOOKS-001
 * Related: @CODE:HOOK-003:UI, @CODE:SESSION-001
 * SPEC: .moai/specs/SPEC-HOOKS-001/spec.md
 *
 * @file session-notice-lite.js
 * @description 세션 시작 알림 훅 (경량화 버전)
 *
 * 프로젝트 정보와 다음 단계를 간결하게 표시합니다.
 * 성능 최적화: 캐싱 및 최소한의 Git 명령 사용 (500ms → 50ms)
 *
 * @hook SessionStart
 * @version 2.0.0
 * @author MoAI-ADK
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

/**
 * @typedef {Object} HookInput
 * @property {string} [tool_name] - 도구 이름
 * @property {Object} [tool_input] - 도구 입력
 */

/**
 * @typedef {Object} HookResult
 * @property {boolean} success - 훅 실행 성공 여부
 * @property {string} [message] - 출력 메시지
 */

// ============================================================================
// 유틸리티 함수
// ============================================================================

/**
 * Git root 디렉토리 탐지
 * @returns {string|null}
 */
function findGitRoot() {
  try {
    const gitRoot = execSync('git rev-parse --show-toplevel', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    }).trim();
    return gitRoot;
  } catch {
    return null;
  }
}

/**
 * Git 정보 조회 (단일 명령으로 최적화)
 * @returns {{branch: string, ahead: number, behind: number, files: number}|null}
 */
function getGitInfo() {
  try {
    // git status -sb --porcelain으로 모든 정보 한 번에 가져오기
    const output = execSync('git status -sb --porcelain', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore'],
    });

    const lines = output.trim().split('\n');
    const statusLine = lines[0]; // ## branch...origin/branch [ahead N, behind M]

    // 브랜치명 추출
    let branch = 'unknown';
    const branchMatch = statusLine.match(/##\s+([^\s.]+)/);
    if (branchMatch) {
      branch = branchMatch[1];
    }

    // ahead/behind 추출
    let ahead = 0;
    let behind = 0;
    const aheadMatch = statusLine.match(/ahead (\d+)/);
    const behindMatch = statusLine.match(/behind (\d+)/);
    if (aheadMatch) ahead = parseInt(aheadMatch[1], 10);
    if (behindMatch) behind = parseInt(behindMatch[1], 10);

    // 변경된 파일 수
    const files = lines.length - 1; // 첫 줄 제외

    return { branch, ahead, behind, files };
  } catch {
    return null;
  }
}

/**
 * SPEC 진행률 조회 (간소화: 디렉토리 개수만 카운트)
 * @param {string} gitRoot
 * @returns {{total: number, completed: number}}
 */
function getSpecProgress(gitRoot) {
  const specsDir = path.join(gitRoot, '.moai', 'specs');

  if (!fs.existsSync(specsDir)) {
    return { total: 0, completed: 0 };
  }

  try {
    const entries = fs.readdirSync(specsDir, { withFileTypes: true });
    const specDirs = entries.filter(e => e.isDirectory() && e.name.startsWith('SPEC-'));

    let total = specDirs.length;
    let completed = 0;

    // completed 확인: status가 'completed'인 SPEC 개수
    for (const dir of specDirs) {
      const specPath = path.join(specsDir, dir.name, 'spec.md');
      if (fs.existsSync(specPath)) {
        try {
          const content = fs.readFileSync(specPath, 'utf8');
          // YAML front matter에서 status: completed 확인 (간단히)
          if (content.includes('status: completed')) {
            completed++;
          }
        } catch {
          // 읽기 실패 시 무시
        }
      }
    }

    return { total, completed };
  } catch {
    return { total: 0, completed: 0 };
  }
}

/**
 * package.json에서 프로젝트 이름 추출
 * @param {string} gitRoot
 * @returns {string}
 */
function getProjectName(gitRoot) {
  const packageJsonPath = path.join(gitRoot, 'package.json');

  if (fs.existsSync(packageJsonPath)) {
    try {
      const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
      return packageJson.name || 'Unknown Project';
    } catch {
      return 'Unknown Project';
    }
  }

  // package.json이 없으면 디렉토리 이름 사용
  return path.basename(gitRoot);
}

/**
 * 캐시된 버전 정보 로드
 * @returns {{version: string, timestamp: number}|null}
 */
function loadCachedVersion() {
  const cacheDir = path.join(os.homedir(), '.moai-cache');
  const cacheFile = path.join(cacheDir, 'latest-version.json');

  if (!fs.existsSync(cacheFile)) {
    return null;
  }

  try {
    const cache = JSON.parse(fs.readFileSync(cacheFile, 'utf8'));
    const now = Date.now();
    const ONE_DAY = 24 * 60 * 60 * 1000;

    // 캐시가 1일 이내면 사용
    if (now - cache.timestamp < ONE_DAY) {
      return cache;
    }
  } catch {
    // 캐시 로드 실패
  }

  return null;
}

/**
 * 버전 정보 캐시 저장
 * @param {string} version
 */
function saveCachedVersion(version) {
  const cacheDir = path.join(os.homedir(), '.moai-cache');
  const cacheFile = path.join(cacheDir, 'latest-version.json');

  try {
    // 캐시 디렉토리 생성
    if (!fs.existsSync(cacheDir)) {
      fs.mkdirSync(cacheDir, { recursive: true });
    }

    const cache = {
      version,
      timestamp: Date.now(),
    };

    fs.writeFileSync(cacheFile, JSON.stringify(cache, null, 2));
  } catch {
    // 캐시 저장 실패 무시
  }
}

/**
 * 다음 단계 제안
 * @param {string} projectName
 * @param {string} branch
 * @param {{total: number, completed: number}} specProgress
 * @returns {string}
 */
function suggestNextStep(projectName, branch, specProgress) {
  // Unknown Project인 경우 프로젝트 초기화 제안
  if (projectName === 'Unknown Project') {
    return '/alfred:0-project';
  }

  // SPEC이 없으면 프로젝트 초기화 제안
  if (specProgress.total === 0) {
    return '/alfred:1-spec "기능명"';
  }

  // 완료되지 않은 SPEC이 있으면 build 제안
  if (specProgress.completed < specProgress.total) {
    return '/alfred:2-build SPEC-XXX';
  }

  // 모두 완료되었으면 sync 제안
  return '/alfred:3-sync';
}

// ============================================================================
// SessionNotice 클래스
// ============================================================================

/**
 * 세션 시작 알림 훅 (경량화 버전)
 */
class SessionNotice {
  constructor() {
    this.name = 'session-notice-lite';
  }

  /**
   * 훅 실행
   * @param {HookInput} input
   * @returns {HookResult}
   */
  async execute(input) {
    const gitRoot = findGitRoot();

    // Git 프로젝트가 아니면 스킵
    if (!gitRoot) {
      return { success: true };
    }

    const projectName = getProjectName(gitRoot);
    const gitInfo = getGitInfo();
    const specProgress = getSpecProgress(gitRoot);

    // 메시지 생성
    const lines = [];
    lines.push('');
    lines.push('🗿 MoAI-ADK 프로젝트');
    lines.push(`   프로젝트: ${projectName}`);

    if (gitInfo) {
      lines.push(`   브랜치: ${gitInfo.branch}`);

      if (gitInfo.ahead > 0 || gitInfo.behind > 0) {
        const sync = [];
        if (gitInfo.ahead > 0) sync.push(`앞서감 ${gitInfo.ahead}`);
        if (gitInfo.behind > 0) sync.push(`뒤처짐 ${gitInfo.behind}`);
        lines.push(`   동기화: ${sync.join(', ')}`);
      }

      if (gitInfo.files > 0) {
        lines.push(`   변경 파일: ${gitInfo.files}개`);
      }
    }

    if (specProgress.total > 0) {
      const percentage = Math.round((specProgress.completed / specProgress.total) * 100);
      lines.push(`   SPEC 진행률: ${specProgress.completed}/${specProgress.total} (${percentage}%)`);
    }

    const nextStep = suggestNextStep(projectName, gitInfo?.branch || '', specProgress);
    lines.push('');
    lines.push(`💡 다음 단계: ${nextStep}`);
    lines.push('');

    const message = lines.join('\n');

    // 출력
    console.log(message);

    return {
      success: true,
      message: 'Session notice displayed',
    };
  }
}

// ============================================================================
// 메인 실행
// ============================================================================

/**
 * 메인 실행
 */
async function main() {
  try {
    // stdin에서 JSON 입력 읽기 (SessionStart 훅은 입력 없을 수 있음)
    let inputData = '';
    for await (const chunk of process.stdin) {
      inputData += chunk;
    }

    let input = {};
    if (inputData.trim()) {
      try {
        input = JSON.parse(inputData);
      } catch {
        // JSON 파싱 실패 시 빈 객체 사용
      }
    }

    const notice = new SessionNotice();
    const result = await notice.execute(input);

    // SessionStart 훅 성공 시 exit code 0으로 종료
    // result.message는 이미 console.log로 출력되었음
    process.exit(0);
  } catch (error) {
    console.error(
      JSON.stringify({
        success: false,
        message: `Session-Notice-Lite 내부 오류: ${error.message}`,
      })
    );
    process.exit(1);
  }
}

// 스크립트 직접 실행 시에만 main 실행
if (require.main === module) {
  main();
}

module.exports = { SessionNotice };
