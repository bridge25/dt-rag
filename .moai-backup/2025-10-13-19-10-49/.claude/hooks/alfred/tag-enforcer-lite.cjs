#!/usr/bin/env node
'use strict';

/**
 * @CODE:HOOK-004 | @CODE:HOOKS-001
 * Related: @CODE:HOOK-004:API, @CODE:TAG-001
 * SPEC: .moai/specs/SPEC-HOOKS-001/spec.md
 *
 * @file tag-enforcer-lite.js
 * @description TAG 시스템 경량 검증 훅 (경고 모드)
 *
 * @TAG 형식을 검증하지만 차단하지 않고 경고만 표시합니다.
 * @IMMUTABLE 검증은 경고 모드로 전환하여 사용자 경험을 개선합니다.
 *
 * @hook PreToolUse
 * @tools Write, Edit
 * @version 2.0.0
 * @author MoAI-ADK
 */

const fs = require('fs');

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
 * @property {number} [exitCode] - 종료 코드
 */

// ============================================================================
// 유틸리티 함수
// ============================================================================

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
 * 파일 내용 추출
 * @param {string} toolName
 * @param {Object} toolInput
 * @returns {string}
 */
function extractFileContent(toolName, toolInput) {
  if (!toolInput) return '';

  // Write 도구
  if (toolName === 'Write') {
    return toolInput.content || '';
  }

  // Edit 도구
  if (toolName === 'Edit') {
    return toolInput.new_string || '';
  }

  return '';
}

/**
 * 기존 파일 내용 읽기
 * @param {string} filePath
 * @returns {string}
 */
function readExistingFile(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return fs.readFileSync(filePath, 'utf8');
    }
  } catch {
    // 읽기 실패 시 빈 문자열
  }
  return '';
}

// ============================================================================
// TAG 검증 함수
// ============================================================================

/**
 * @TAG 형식 검증
 * @param {string} tag
 * @returns {boolean}
 */
function isValidTagFormat(tag) {
  // 허용되는 TAG 패턴:
  // @SPEC:ID, @TEST:ID, @CODE:ID, @DOC:ID
  // @IMMUTABLE, @DEPRECATED 등
  const validPatterns = [
    /^@(SPEC|TEST|CODE|DOC):[A-Z0-9-]+$/,
    /^@IMMUTABLE$/,
    /^@DEPRECATED$/,
    /^@TODO$/,
    /^@FIXME$/,
  ];

  return validPatterns.some(pattern => pattern.test(tag));
}

/**
 * 모든 @TAG 추출
 * @param {string} content
 * @returns {string[]}
 */
function extractAllTags(content) {
  const tagPattern = /@[A-Z][A-Z0-9-]*(?::[A-Z0-9-]+)?/g;
  const matches = content.match(tagPattern);
  return matches || [];
}

/**
 * @IMMUTABLE 블록 추출
 * @param {string} content
 * @returns {Array<{start: number, end: number, content: string}>}
 */
function extractImmutableBlocks(content) {
  const blocks = [];
  const lines = content.split('\n');
  let inBlock = false;
  let blockStart = -1;
  let blockLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    if (line.includes('@IMMUTABLE')) {
      inBlock = true;
      blockStart = i;
      blockLines = [line];
    } else if (inBlock) {
      if (line.trim() === '' || !line.trim().startsWith('//') && !line.trim().startsWith('*')) {
        // 블록 종료
        blocks.push({
          start: blockStart,
          end: i - 1,
          content: blockLines.join('\n'),
        });
        inBlock = false;
        blockStart = -1;
        blockLines = [];
      } else {
        blockLines.push(line);
      }
    }
  }

  // 마지막 블록 처리
  if (inBlock) {
    blocks.push({
      start: blockStart,
      end: lines.length - 1,
      content: blockLines.join('\n'),
    });
  }

  return blocks;
}

/**
 * @IMMUTABLE 블록 수정 감지
 * @param {string} oldContent
 * @param {string} newContent
 * @returns {boolean}
 */
function hasImmutableViolation(oldContent, newContent) {
  const oldBlocks = extractImmutableBlocks(oldContent);
  const newBlocks = extractImmutableBlocks(newContent);

  // 블록 개수가 다르면 위반
  if (oldBlocks.length !== newBlocks.length) {
    return true;
  }

  // 각 블록 내용 비교
  for (let i = 0; i < oldBlocks.length; i++) {
    if (oldBlocks[i].content !== newBlocks[i].content) {
      return true;
    }
  }

  return false;
}

// ============================================================================
// TagEnforcer 클래스
// ============================================================================

/**
 * TAG 경량 검증 훅 (경고 모드)
 */
class TagEnforcer {
  constructor() {
    this.name = 'tag-enforcer-lite';
  }

  /**
   * 훅 실행
   * @param {HookInput} input
   * @returns {HookResult}
   */
  async execute(input) {
    // 입력 검증
    if (!input || !input.tool_name) {
      return { success: true };
    }

    const toolName = input.tool_name;

    // Write, Edit 도구만 검사
    if (!['Write', 'Edit'].includes(toolName)) {
      return { success: true };
    }

    const toolInput = input.tool_input || {};
    const filePath = extractFilePath(toolInput);

    // 파일 경로 없으면 통과
    if (!filePath) {
      return { success: true };
    }

    const newContent = extractFileContent(toolName, toolInput);

    // 1. TAG 형식 검증 (경고만)
    const tags = extractAllTags(newContent);
    const invalidTags = tags.filter(tag => !isValidTagFormat(tag));

    if (invalidTags.length > 0) {
      console.warn('');
      console.warn('⚠️ TAG 형식 경고:');
      for (const tag of invalidTags) {
        console.warn(`   - ${tag} (올바른 형식: @SPEC:ID, @CODE:ID, @TEST:ID, @DOC:ID)`);
      }
      console.warn('');
      console.warn('💡 TAG 형식을 확인하세요. 작업은 계속 진행됩니다.');
      console.warn('');
    }

    // 2. @IMMUTABLE 블록 검증 (경고만)
    if (toolName === 'Edit') {
      const oldContent = readExistingFile(filePath);

      if (oldContent && hasImmutableViolation(oldContent, newContent)) {
        console.warn('');
        console.warn('⚠️ @IMMUTABLE 블록 수정 감지:');
        console.warn(`   파일: ${filePath}`);
        console.warn('   @IMMUTABLE로 표시된 블록이 수정되었습니다.');
        console.warn('');
        console.warn('💡 의도한 변경이 맞는지 확인하세요. 작업은 계속 진행됩니다.');
        console.warn('');
      }
    }

    // 항상 통과 (경고만, 차단하지 않음)
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
    const enforcer = new TagEnforcer();
    const result = await enforcer.execute(input);

    // 결과 출력
    console.log(JSON.stringify(result, null, 2));

    // 종료 코드 설정
    process.exit(result.exitCode || 0);
  } catch (error) {
    console.error(
      JSON.stringify({
        success: false,
        message: `TAG-Enforcer-Lite 내부 오류: ${error.message}`,
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

module.exports = { TagEnforcer };
