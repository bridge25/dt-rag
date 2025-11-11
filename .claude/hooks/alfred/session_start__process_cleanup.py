#!/usr/bin/env python3
# @CODE:HOOK-PROCESS-CLEANUP-001 | SPEC: BACKGROUND-TASK-MANAGEMENT-001

"""SessionStart Hook: 백그라운드 프로세스 정리

세션 시작 시 고아(orphaned) 프로세스를 감지하고 정리합니다.

기능:
- ripgrep (rg) 좀비 프로세스 감지 및 종료
- 장시간 실행 중인 bash 프로세스 정리
- 프로세스 레지스트리 관리
- 세션 간 잔존 프로세스 정리
"""

import json
import logging
import os
import psutil
import signal
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


def load_hook_timeout() -> int:
    """Load hook timeout from config.json (default: 3000ms)"""
    try:
        config_file = Path(".moai/config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("hooks", {}).get("timeout_ms", 3000)
    except Exception:
        pass
    return 3000


def get_graceful_degradation() -> bool:
    """Load graceful_degradation setting from config.json (default: true)"""
    try:
        config_file = Path(".moai/config.json")
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get("hooks", {}).get("graceful_degradation", True)
    except Exception:
        pass
    return True


def find_orphaned_ripgrep_processes() -> List[Dict]:
    """고아 ripgrep 프로세스 찾기

    Returns:
        고아 프로세스 목록
    """
    orphaned = []

    try:
        current_time = time.time()

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                # ripgrep 프로세스 확인
                if proc.info['name'] in ('rg', 'ripgrep'):
                    cmdline = proc.info['cmdline']
                    create_time = proc.info['create_time']

                    # 실행 시간 계산
                    running_time = current_time - create_time

                    # 5분 이상 실행 중이면 좀비로 간주
                    if running_time > 300:  # 5 minutes
                        orphaned.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(cmdline) if cmdline else '',
                            'running_time': running_time,
                            'reason': 'long_running'
                        })

                    # TAG 관련 작업이면서 3분 이상 실행 중
                    elif running_time > 180 and cmdline:  # 3 minutes
                        cmd_str = ' '.join(cmdline)
                        if any(tag in cmd_str for tag in ['@CODE:', '@SPEC:', '@TEST:', '@DOC:', '@TAG']):
                            orphaned.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmd_str,
                                'running_time': running_time,
                                'reason': 'tag_analysis_stuck'
                            })

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    except Exception as e:
        logger.error(f"Failed to find orphaned ripgrep processes: {e}")

    return orphaned


def find_orphaned_bash_processes() -> List[Dict]:
    """고아 bash 프로세스 찾기

    Returns:
        고아 프로세스 목록
    """
    orphaned = []

    try:
        current_time = time.time()

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'status']):
            try:
                # bash 프로세스 확인
                if proc.info['name'] in ('bash', 'sh'):
                    cmdline = proc.info['cmdline']
                    create_time = proc.info['create_time']
                    status = proc.info['status']

                    # 실행 시간 계산
                    running_time = current_time - create_time

                    # 좀비 상태
                    if status == psutil.STATUS_ZOMBIE:
                        orphaned.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': ' '.join(cmdline) if cmdline else '',
                            'running_time': running_time,
                            'reason': 'zombie_status'
                        })

                    # 10분 이상 실행 중이고 Claude Code 관련
                    elif running_time > 600 and cmdline:  # 10 minutes
                        cmd_str = ' '.join(cmdline)
                        if '.claude' in cmd_str or 'rg' in cmd_str:
                            orphaned.append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': cmd_str,
                                'running_time': running_time,
                                'reason': 'long_running_claude_related'
                            })

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    except Exception as e:
        logger.error(f"Failed to find orphaned bash processes: {e}")

    return orphaned


def kill_process_safely(pid: int, name: str) -> bool:
    """프로세스를 안전하게 종료

    Args:
        pid: 프로세스 ID
        name: 프로세스 이름

    Returns:
        성공 여부
    """
    try:
        proc = psutil.Process(pid)

        # SIGTERM으로 우아하게 종료 시도
        proc.terminate()

        # 3초 대기
        try:
            proc.wait(timeout=3)
            return True
        except psutil.TimeoutExpired:
            # SIGKILL로 강제 종료
            proc.kill()
            try:
                proc.wait(timeout=1)
                return True
            except psutil.TimeoutExpired:
                return False

    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.warning(f"Failed to kill process {pid} ({name}): {e}")
        return False


def cleanup_processes() -> Dict[str, any]:
    """프로세스 정리 실행

    Returns:
        정리 통계
    """
    stats = {
        'ripgrep_cleaned': 0,
        'bash_cleaned': 0,
        'total_cleaned': 0,
        'failed': 0,
        'details': []
    }

    try:
        # ripgrep 프로세스 정리
        orphaned_rg = find_orphaned_ripgrep_processes()
        for proc_info in orphaned_rg:
            success = kill_process_safely(proc_info['pid'], proc_info['name'])
            if success:
                stats['ripgrep_cleaned'] += 1
                stats['details'].append({
                    'pid': proc_info['pid'],
                    'type': 'ripgrep',
                    'reason': proc_info['reason'],
                    'running_time': round(proc_info['running_time'], 2)
                })
            else:
                stats['failed'] += 1

        # bash 프로세스 정리
        orphaned_bash = find_orphaned_bash_processes()
        for proc_info in orphaned_bash:
            success = kill_process_safely(proc_info['pid'], proc_info['name'])
            if success:
                stats['bash_cleaned'] += 1
                stats['details'].append({
                    'pid': proc_info['pid'],
                    'type': 'bash',
                    'reason': proc_info['reason'],
                    'running_time': round(proc_info['running_time'], 2)
                })
            else:
                stats['failed'] += 1

        stats['total_cleaned'] = stats['ripgrep_cleaned'] + stats['bash_cleaned']

    except Exception as e:
        logger.error(f"Process cleanup failed: {e}")

    return stats


def update_cleanup_log(stats: Dict):
    """정리 로그 업데이트

    Args:
        stats: 정리 통계
    """
    try:
        log_file = Path(".moai/cache/process_cleanup_log.json")
        log_file.parent.mkdir(exist_ok=True)

        # 기존 로그 로드
        existing_log = []
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                existing_log = json.load(f)

        # 새 로그 추가
        existing_log.append({
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        })

        # 최근 30개만 유지
        if len(existing_log) > 30:
            existing_log = existing_log[-30:]

        # 로그 저장
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(existing_log, f, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to update cleanup log: {e}")


def main():
    """메인 함수"""
    try:
        # Hook timeout 설정 로드
        timeout_seconds = load_hook_timeout() / 1000
        graceful_degradation = get_graceful_degradation()

        # 타임아웃 체크
        def timeout_handler(signum, frame):
            raise TimeoutError("Hook execution timeout")

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout_seconds))

        try:
            start_time = time.time()

            # 프로세스 정리 실행
            cleanup_stats = cleanup_processes()

            # 로그 업데이트
            if cleanup_stats['total_cleaned'] > 0:
                update_cleanup_log(cleanup_stats)

            # 실행 시간 기록
            execution_time = time.time() - start_time

            # 결과 출력
            result = {
                'hook': 'session_start__process_cleanup',
                'success': True,
                'execution_time_seconds': round(execution_time, 2),
                'cleanup_stats': cleanup_stats,
                'timestamp': datetime.now().isoformat()
            }

            print(json.dumps(result, ensure_ascii=False, indent=2))

        finally:
            signal.alarm(0)  # 타임아웃 해제

    except TimeoutError as e:
        # 타임아웃 처리
        result = {
            'hook': 'session_start__process_cleanup',
            'success': False,
            'error': f"Hook execution timeout: {str(e)}",
            'graceful_degradation': graceful_degradation,
            'timestamp': datetime.now().isoformat()
        }

        if graceful_degradation:
            result['message'] = "Hook timeout but continuing due to graceful degradation"

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        # 예외 처리
        result = {
            'hook': 'session_start__process_cleanup',
            'success': False,
            'error': f"Hook execution failed: {str(e)}",
            'graceful_degradation': graceful_degradation,
            'timestamp': datetime.now().isoformat()
        }

        if graceful_degradation:
            result['message'] = "Hook failed but continuing due to graceful degradation"

        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
