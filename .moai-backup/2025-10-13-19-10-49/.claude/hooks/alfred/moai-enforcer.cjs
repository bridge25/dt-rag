#!/usr/bin/env node
'use strict';

/**
 * @CODE:HOOK-005 | @CODE:HOOKS-001
 * Related: @CODE:HOOK-005:API, @CODE:ENFORCER-001, @CODE:TDD-001
 * SPEC: .moai/specs/SPEC-HOOKS-001/spec.md
 *
 * @file moai-enforcer.js
 * @description MoAI-ADK 핵심 강제 훅
 *
 * SPEC-First + TDD-First 철학을 단일 훅으로 강제합니다.
 *
 * @hook PreToolUse
 * @tools Write, Edit
 * @version 2.0.0
 * @author MoAI-ADK
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * @typedef {Object} HookInput
 * @property {string} [tool_name] - 호출된 도구 이름
 * @property {Object} [tool_input] - 도구 입력 객체
 */

/**
 * @typedef {Object} HookResult
 * @property {boolean} success - 훅 실행 성공 여부
 * @property {boolean} [blocked] - 작업 차단 여부
 * @property {string} [message] - 사용자 메시지
 * @property {string[]} [suggestions] - 권장 조치 목록
 * @property {number} [exitCode] - 종료 코드 (0: 성공, 2: 차단)
 */

/**
 * @typedef {Object} ValidationContext
 * @property {string} filePath - 파일 경로
 * @property {string} content - 파일 내용
 * @property {string} toolName - 도구 이름
 */

// ============================================================================
// 공통 유틸리티 함수
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
      shell: false, // 명시적으로 쉘 비활성화 (보안 강화)
    }).trim();

    // 경로 검증: 절대 경로여야 함
    if (!path.isAbsolute(gitRoot)) {
      return null;
    }

    return gitRoot;
  } catch {
    return null;
  }
}

/**
 * 경로 검증 - path traversal 방지
 * @param {string} filePath - 검증할 파일 경로
 * @param {string} basePath - 기준 경로 (gitRoot)
 * @returns {boolean}
 */
function isPathSafe(filePath, basePath) {
  if (!filePath || !basePath) {
    return false;
  }

  // 절대 경로로 해석
  const resolvedPath = path.resolve(basePath, filePath);
  const normalizedBase = path.normalize(basePath);

  // 경로가 기준 경로 내부에 있는지 확인
  return resolvedPath.startsWith(normalizedBase + path.sep) || resolvedPath === normalizedBase;
}

/**
 * 파일 경로 추출
 * @param {Object} toolInput
 * @returns {string}
 */
function extractFilePath(toolInput) {
  if (!toolInput) return '';
  return toolInput.file_path || toolInput.path || '';
}

/**
 * 파일 내용 추출 (Write/Edit 구분)
 * @param {string} toolName
 * @param {Object} toolInput
 * @returns {string}
 */
function extractFileContent(toolName, toolInput) {
  if (!toolInput) return '';

  // Write 도구는 content 필드 사용
  if (toolName === 'Write') {
    return toolInput.content || '';
  }

  // Edit 도구는 new_string 필드 사용
  if (toolName === 'Edit') {
    return toolInput.new_string || '';
  }

  return '';
}

/**
 * 코드 파일 확장자 Set (O(1) 조회)
 * @type {Set<string>}
 */
const CODE_EXTENSIONS = new Set([
  // JavaScript/TypeScript
  '.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs',
  // Python
  '.py',
  // Java/Kotlin
  '.java', '.kt',
  // Go
  '.go',
  // Rust
  '.rs',
  // Swift
  '.swift',
  // Dart
  '.dart',
  // C/C++
  '.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hh', '.hxx',
  // C#
  '.cs',
  // Ruby
  '.rb', '.rake',
  // PHP
  '.php', '.phtml',
  // Web (HTML/CSS)
  '.html', '.htm', '.css', '.scss', '.sass', '.less',
  // Web Frameworks
  '.vue', '.svelte',
  // Shell
  '.sh', '.bash', '.zsh',
  // Other
  '.scala', '.clj', '.cljs', '.ex', '.exs', '.erl', '.hrl',
]);

/**
 * 파일 확장자가 코드 파일인지 확인
 * @param {string} filePath
 * @returns {boolean}
 */
function isCodeFile(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return CODE_EXTENSIONS.has(ext);
}

/**
 * 제외할 디렉토리 패턴 (정규식)
 * 경로가 패턴으로 시작하거나 /패턴을 포함하면 제외
 * @type {RegExp}
 */
const EXCLUDE_PATTERNS = /(?:^|\/)(tests|test|__tests__|docs|documentation|examples|node_modules|dist|build|out|\.moai|\.git|\.github|\.vscode|\.idea|target|bin|obj|vendor)\//;

/**
 * 테스트 파일 패턴 (정규식)
 * @type {RegExp}
 */
const TEST_FILE_PATTERN = /\.(test|spec)\.|_test\./;

/**
 * 파일이 검증 대상인지 확인 (제외 패턴 체크)
 * @param {string} filePath
 * @returns {boolean}
 */
function shouldValidate(filePath) {
  const normalizedPath = filePath.replace(/\\/g, '/').toLowerCase();

  // 제외 디렉토리 패턴 검사 (O(1))
  if (EXCLUDE_PATTERNS.test(normalizedPath)) {
    return false;
  }

  // 테스트 파일 패턴 검사 (O(1))
  if (TEST_FILE_PATTERN.test(normalizedPath)) {
    return false;
  }

  return true;
}

// ============================================================================
// SPEC 검증 함수
// ============================================================================

/**
 * @CODE TAG 패턴 (통합 정규식)
 * 모든 주석 스타일 지원: //, #, block comments, HTML comments, JSX comments
 * @type {RegExp}
 */
const CODE_TAG_PATTERN = /(\/\/|#|\/\*[\s\S]*?|<!--[\s\S]*?|\{\s*\/\*[\s\S]*?)\s*@CODE:[A-Z0-9-]+/;

/**
 * @CODE TAG 존재 여부 확인
 * 다양한 주석 스타일 지원: //, #, block comments, HTML comments, JSX comments
 * @param {string} content
 * @returns {boolean}
 */
function hasCodeTag(content) {
  return CODE_TAG_PATTERN.test(content);
}

/**
 * @CODE TAG에서 SPEC 참조 추출
 * 다양한 주석 스타일 지원
 * @param {string} content
 * @returns {string|null} - SPEC 파일명 (예: "SPEC-AUTH-001.md")
 */
function extractSpecReference(content) {
  // @CODE:AUTH-001 | SPEC: SPEC-AUTH-001.md 형식 (모든 주석 스타일)
  const specRefPatterns = [
    // // 주석
    /\/\/\s*@CODE:[A-Z0-9-]+\s*\|\s*SPEC:\s*(SPEC-[A-Z0-9-]+\.md)/,
    // # 주석
    /#\s*@CODE:[A-Z0-9-]+\s*\|\s*SPEC:\s*(SPEC-[A-Z0-9-]+\.md)/,
    // /* */ 주석
    /\/\*[\s\S]*?@CODE:[A-Z0-9-]+\s*\|\s*SPEC:\s*(SPEC-[A-Z0-9-]+\.md)[\s\S]*?\*\//,
    // <!-- --> 주석
    /<!--[\s\S]*?@CODE:[A-Z0-9-]+\s*\|\s*SPEC:\s*(SPEC-[A-Z0-9-]+\.md)[\s\S]*?-->/,
    // {/* */} 주석
    /\{\s*\/\*[\s\S]*?@CODE:[A-Z0-9-]+\s*\|\s*SPEC:\s*(SPEC-[A-Z0-9-]+\.md)[\s\S]*?\*\/\s*\}/,
  ];

  for (const pattern of specRefPatterns) {
    const match = content.match(pattern);
    if (match) return match[1];
  }
  return null;
}

/**
 * @CODE TAG에서 SPEC ID 추출
 * 다양한 주석 스타일 지원
 * @param {string} content
 * @returns {string|null} - SPEC ID (예: "AUTH-001")
 */
function extractSpecId(content) {
  const codeTagPatterns = [
    // // 주석
    /\/\/\s*@CODE:([A-Z0-9-]+)/,
    // # 주석
    /#\s*@CODE:([A-Z0-9-]+)/,
    // /* */ 주석
    /\/\*[\s\S]*?@CODE:([A-Z0-9-]+)[\s\S]*?\*\//,
    // <!-- --> 주석
    /<!--[\s\S]*?@CODE:([A-Z0-9-]+)[\s\S]*?-->/,
    // {/* */} 주석
    /\{\s*\/\*[\s\S]*?@CODE:([A-Z0-9-]+)[\s\S]*?\*\/\s*\}/,
  ];

  for (const pattern of codeTagPatterns) {
    const match = content.match(pattern);
    if (match) return match[1];
  }
  return null;
}

/**
 * SPEC 파일 존재 확인
 * @param {string} specFileName - 예: "SPEC-AUTH-001.md"
 * @param {string} gitRoot
 * @returns {boolean}
 */
function specFileExists(specFileName, gitRoot) {
  // SPEC ID 추출 (예: "AUTH-001")
  const specIdMatch = specFileName.match(/SPEC-([A-Z0-9-]+)\.md/);
  if (!specIdMatch) return false;

  const specId = specIdMatch[1];
  const specDir = path.join(gitRoot, '.moai', 'specs', `SPEC-${specId}`);
  const specFilePath = path.join(specDir, 'spec.md');

  // 경로 검증: path traversal 방지 (보안 강화)
  if (!isPathSafe(specFilePath, gitRoot)) {
    return false;
  }

  return fs.existsSync(specFilePath);
}

// ============================================================================
// TDD 검증 함수
// ============================================================================

/**
 * 대응하는 테스트 파일 경로 생성
 * @param {string} srcFilePath - 소스 파일 경로 (절대 또는 상대)
 * @param {string} gitRoot
 * @returns {string[]} - 가능한 테스트 파일 경로 배열
 */
function getCorrespondingTestFiles(srcFilePath, gitRoot) {
  const ext = path.extname(srcFilePath);
  const basename = path.basename(srcFilePath, ext);
  const relativePath = path.relative(gitRoot, srcFilePath);
  const dirPath = path.dirname(relativePath);

  // 언어별 테스트 파일 패턴
  const testPatterns = [];

  // TypeScript/JavaScript
  if (['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'].includes(ext)) {
    testPatterns.push(
      path.join(gitRoot, 'tests', dirPath, `${basename}.test${ext}`),
      path.join(gitRoot, 'test', dirPath, `${basename}.test${ext}`),
      path.join(gitRoot, '__tests__', dirPath, `${basename}.test${ext}`),
      path.join(gitRoot, 'tests', dirPath, `${basename}.spec${ext}`),
    );
  }

  // Python
  if (ext === '.py') {
    testPatterns.push(
      path.join(gitRoot, 'tests', dirPath, `test_${basename}.py`),
      path.join(gitRoot, 'test', dirPath, `test_${basename}.py`),
      path.join(gitRoot, 'tests', dirPath, `${basename}_test.py`),
    );
  }

  // Go
  if (ext === '.go') {
    testPatterns.push(
      path.join(gitRoot, path.dirname(srcFilePath), `${basename}_test.go`),
    );
  }

  // Rust
  if (ext === '.rs') {
    testPatterns.push(
      path.join(gitRoot, 'tests', dirPath, `${basename}_test.rs`),
      path.join(gitRoot, path.dirname(srcFilePath), `${basename}_test.rs`),
    );
  }

  // Java
  if (ext === '.java') {
    testPatterns.push(
      path.join(gitRoot, 'src', 'test', 'java', dirPath, `${basename}Test.java`),
      path.join(gitRoot, 'test', dirPath, `${basename}Test.java`),
    );
  }

  // Kotlin
  if (ext === '.kt') {
    testPatterns.push(
      path.join(gitRoot, 'src', 'test', 'kotlin', dirPath, `${basename}Test.kt`),
      path.join(gitRoot, 'test', dirPath, `${basename}Test.kt`),
    );
  }

  // Swift
  if (ext === '.swift') {
    testPatterns.push(
      path.join(gitRoot, 'Tests', dirPath, `${basename}Tests.swift`),
      path.join(gitRoot, 'tests', dirPath, `${basename}Tests.swift`),
    );
  }

  // Dart
  if (ext === '.dart') {
    testPatterns.push(
      path.join(gitRoot, 'test', dirPath, `${basename}_test.dart`),
    );
  }

  // C#
  if (ext === '.cs') {
    testPatterns.push(
      path.join(gitRoot, 'tests', dirPath, `${basename}Tests.cs`),
      path.join(gitRoot, 'test', dirPath, `${basename}Tests.cs`),
      path.join(gitRoot, 'Tests', dirPath, `${basename}Tests.cs`),
    );
  }

  // Ruby
  if (ext === '.rb') {
    testPatterns.push(
      path.join(gitRoot, 'spec', dirPath, `${basename}_spec.rb`),
      path.join(gitRoot, 'test', dirPath, `test_${basename}.rb`),
      path.join(gitRoot, 'tests', dirPath, `test_${basename}.rb`),
    );
  }

  // PHP
  if (ext === '.php') {
    testPatterns.push(
      path.join(gitRoot, 'tests', dirPath, `${basename}Test.php`),
      path.join(gitRoot, 'test', dirPath, `${basename}Test.php`),
    );
  }

  // C/C++
  if (['.c', '.cpp', '.cc', '.cxx'].includes(ext)) {
    testPatterns.push(
      path.join(gitRoot, 'tests', dirPath, `${basename}_test${ext}`),
      path.join(gitRoot, 'test', dirPath, `${basename}_test${ext}`),
      path.join(gitRoot, 'tests', dirPath, `test_${basename}${ext}`),
    );
  }

  // Scala
  if (ext === '.scala') {
    testPatterns.push(
      path.join(gitRoot, 'src', 'test', 'scala', dirPath, `${basename}Test.scala`),
      path.join(gitRoot, 'test', dirPath, `${basename}Test.scala`),
    );
  }

  // Elixir
  if (['.ex', '.exs'].includes(ext)) {
    testPatterns.push(
      path.join(gitRoot, 'test', dirPath, `${basename}_test.exs`),
    );
  }

  return testPatterns;
}

/**
 * 테스트 파일이 존재하는지 확인
 * @param {string[]} testFilePaths
 * @returns {boolean}
 */
function testFileExists(testFilePaths) {
  return testFilePaths.some(testPath => fs.existsSync(testPath));
}

/**
 * 존재하는 테스트 파일 경로 반환
 * @param {string[]} testFilePaths
 * @returns {string|null}
 */
function findExistingTestFile(testFilePaths) {
  for (const testPath of testFilePaths) {
    if (fs.existsSync(testPath)) {
      return testPath;
    }
  }
  return null;
}

// ============================================================================
// MoAIEnforcer 클래스
// ============================================================================

/**
 * MoAI-ADK 통합 강제 훅
 */
class MoAIEnforcer {
  constructor() {
    this.name = 'moai-enforcer';
    this.gitRoot = findGitRoot();
  }

  /**
   * 검증 컨텍스트 추출
   * @param {HookInput} input
   * @returns {ValidationContext|null}
   */
  extractContext(input) {
    if (!input || !input.tool_name) {
      return null;
    }

    const toolName = input.tool_name;

    // Write, Edit 도구만 검사
    if (!['Write', 'Edit'].includes(toolName)) {
      return null;
    }

    const toolInput = input.tool_input || {};
    const filePath = extractFilePath(toolInput);

    // 파일 경로 없으면 스킵
    if (!filePath) {
      return null;
    }

    // 코드 파일이 아니면 스킵
    if (!isCodeFile(filePath)) {
      return null;
    }

    // 검증 대상이 아니면 스킵
    if (!shouldValidate(filePath)) {
      return null;
    }

    const content = extractFileContent(toolName, toolInput);

    return { filePath, content, toolName };
  }

  /**
   * SPEC 검증
   * @param {ValidationContext} context
   * @returns {HookResult}
   */
  validateSpec(context) {
    const { content } = context;

    // @CODE TAG 존재 확인
    if (!hasCodeTag(content)) {
      return {
        success: false,
        blocked: true,
        message: '❌ SPEC-First 원칙 위반: @CODE TAG가 필요합니다',
        suggestions: [
          '',
          '📋 다음 단계를 따라주세요:',
          '',
          '1️⃣ SPEC 작성:',
          '   /alfred:1-spec "기능명"',
          '',
          '2️⃣ 파일 최상단에 @CODE TAG 추가 (언어별 주석 스타일):',
          '   // @CODE:FEATURE-001 | SPEC: SPEC-FEATURE-001.md | TEST: tests/feature.test.ts',
          '   # @CODE:FEATURE-001 | SPEC: SPEC-FEATURE-001.md | TEST: tests/feature_test.py',
          '   <!-- @CODE:FEATURE-001 | SPEC: SPEC-FEATURE-001.md | TEST: tests/feature.test.js -->',
          '',
          '💡 MoAI-ADK는 "명세 없이는 코드 없음" 철학을 따릅니다.',
          '   모든 구현 코드는 SPEC 문서와 연결되어야 합니다.',
          '   지원 언어: TypeScript, Python, Java, Go, Rust, Ruby, PHP, C#, C/C++, HTML, CSS 등',
        ],
        exitCode: 2,
      };
    }

    // SPEC 참조 추출
    const specRef = extractSpecReference(content);
    const specId = extractSpecId(content);

    // SPEC 참조가 없으면 경고
    if (!specRef && specId) {
      return {
        success: false,
        blocked: true,
        message: `❌ @CODE TAG에 SPEC 참조가 필요합니다`,
        suggestions: [
          '',
          '📋 @CODE TAG 형식이 불완전합니다:',
          '',
          '현재:',
          `   @CODE:${specId}`,
          '',
          '올바른 형식 (언어별 주석 스타일):',
          `   // @CODE:${specId} | SPEC: SPEC-${specId}.md | TEST: tests/...     (JS/TS/Java/C/C++/Go/Rust)`,
          `   # @CODE:${specId} | SPEC: SPEC-${specId}.md | TEST: tests/...      (Python/Ruby/Shell)`,
          `   <!-- @CODE:${specId} | SPEC: SPEC-${specId}.md | TEST: tests/... --> (HTML/XML)`,
          '',
          '💡 @CODE TAG는 SPEC 파일과 TEST 파일을 명시해야 추적성이 보장됩니다.',
        ],
        exitCode: 2,
      };
    }

    // SPEC 파일 존재 확인
    if (specRef && this.gitRoot && !specFileExists(specRef, this.gitRoot)) {
      return {
        success: false,
        blocked: true,
        message: `❌ SPEC 파일이 존재하지 않습니다: ${specRef}`,
        suggestions: [
          '',
          '📋 SPEC 파일을 먼저 생성해야 합니다:',
          '',
          '1️⃣ SPEC 작성:',
          `   /alfred:1-spec "${specId} 기능"`,
          '',
          `2️⃣ 예상 경로: .moai/specs/SPEC-${specId}/spec.md`,
          '',
          '💡 SPEC 파일이 생성된 후 다시 시도하세요.',
        ],
        exitCode: 2,
      };
    }

    // SPEC 검증 통과
    return { success: true };
  }

  /**
   * TDD 검증
   * @param {ValidationContext} context
   * @returns {HookResult}
   */
  validateTDD(context) {
    const { filePath } = context;

    // Git root를 찾을 수 없으면 경고만
    if (!this.gitRoot) {
      console.warn('⚠️ MoAI-Enforcer: Git root를 찾을 수 없습니다. TDD 검증을 건너뜁니다.');
      return { success: true };
    }

    // 대응하는 테스트 파일 경로 생성
    const testFilePaths = getCorrespondingTestFiles(filePath, this.gitRoot);

    if (testFilePaths.length === 0) {
      console.warn('⚠️ MoAI-Enforcer: 테스트 파일 패턴을 결정할 수 없습니다.');
      return { success: true };
    }

    // 테스트 파일 존재 확인
    if (!testFileExists(testFilePaths)) {
      const ext = path.extname(filePath);
      const basename = path.basename(filePath, ext);
      const primaryTestPath = testFilePaths[0];

      return {
        success: false,
        blocked: true,
        message: '❌ TDD-First 원칙 위반: 테스트 파일이 필요합니다',
        suggestions: [
          '',
          '📋 TDD 워크플로우를 따라주세요:',
          '',
          '1️⃣ RED 단계: 실패하는 테스트 작성',
          `   테스트 파일 생성: ${path.relative(this.gitRoot, primaryTestPath)}`,
          '',
          '   예시:',
          '   ```',
          `   // @TEST:FEATURE-001 | SPEC: SPEC-FEATURE-001.md`,
          '   ',
          `   describe('${basename}', () => {`,
          `     it('should ...', () => {`,
          `       // 테스트 작성`,
          '     });',
          '   });',
          '   ```',
          '',
          '2️⃣ 테스트 실행 (실패 확인)',
          '',
          '3️⃣ GREEN 단계: 테스트를 통과하는 최소한의 코드 작성',
          '',
          '💡 MoAI-ADK는 "테스트 없이는 구현 없음" 철학을 따릅니다.',
          '   RED → GREEN → REFACTOR 사이클을 준수해야 합니다.',
        ],
        exitCode: 2,
      };
    }

    // TDD 검증 통과
    return { success: true };
  }

  /**
   * 훅 실행 (메인 로직)
   * @param {HookInput} input
   * @returns {HookResult}
   */
  async execute(input) {
    // 1. 검증 컨텍스트 추출 (공통)
    const context = this.extractContext(input);

    // 검증 대상이 아니면 통과
    if (!context) {
      return { success: true };
    }

    // Git root 경고
    if (!this.gitRoot) {
      console.warn('⚠️ MoAI-Enforcer: Git root를 찾을 수 없습니다. 일부 검증을 건너뜁니다.');
    }

    // 2. SPEC 검증 (우선)
    const specResult = this.validateSpec(context);
    if (!specResult.success) {
      return specResult;
    }

    // 3. TDD 검증 (SPEC 통과 시에만)
    const tddResult = this.validateTDD(context);
    if (!tddResult.success) {
      return tddResult;
    }

    // 모든 검증 통과
    return { success: true };
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
    // stdin에서 JSON 입력 읽기
    let inputData = '';
    for await (const chunk of process.stdin) {
      inputData += chunk;
    }

    if (!inputData.trim()) {
      console.log(JSON.stringify({ success: true }));
      return;
    }

    /** @type {HookInput} */
    const input = JSON.parse(inputData);
    const enforcer = new MoAIEnforcer();
    const result = await enforcer.execute(input);

    // 결과 출력
    console.log(JSON.stringify(result, null, 2));

    // 종료 코드 설정
    process.exit(result.exitCode || 0);
  } catch (error) {
    console.error(
      JSON.stringify({
        success: false,
        message: `MoAI-Enforcer 내부 오류: ${error.message}`,
        exitCode: 1,
      })
    );
    process.exit(1);
  }
}

// 스크립트 직접 실행 시에만 main 실행
if (require.main === module) {
  main();
}

module.exports = { MoAIEnforcer };
