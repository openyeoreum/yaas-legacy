#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
from typing import Dict, Any

TARGET_SUBKEYS = [
    'BaseModel',
    'ExampleFineTunedModel',
    'MemoryFineTunedModel',
]
TARGET_TOPLEVEL = [
    'ExampleFineTuning',
    'Memory',
    'MemoryFineTuning',
]

def process_json_obj(obj: Any, prune_empty: bool = False) -> (Any, bool):
    """
    obj(dict)를 수정하고 변경 여부를 반환합니다.
    prune_empty=True면 비게 된 'OpenAI', 'ANTHROPIC' 키도 제거합니다.
    """
    if not isinstance(obj, dict):
        return obj, False

    changed = False

    # 1,2) OpenAI / ANTHROPIC 내부 하위 키 삭제
    for provider in ('OpenAI', 'ANTHROPIC'):
        if provider in obj and isinstance(obj[provider], dict):
            before_len = len(obj[provider])
            for k in TARGET_SUBKEYS:
                if k in obj[provider]:
                    obj[provider].pop(k, None)
                    changed = True
            # 비어 있으면 컨테이너 제거 옵션
            if prune_empty and isinstance(obj[provider], dict) and len(obj[provider]) == 0:
                obj.pop(provider, None)
                changed = True
            else:
                # 내용 변화 체크(하위 다른 키가 남아 있을 수 있음)
                changed = changed or (len(obj.get(provider, {})) != before_len)

    # 3) 최상위 키 삭제
    for topk in TARGET_TOPLEVEL:
        if topk in obj:
            obj.pop(topk, None)
            changed = True

    return obj, changed

def process_file(filepath: str, backup: bool = True, prune_empty: bool = False, dry_run: bool = False) -> bool:
    """
    파일 하나를 처리. 변경이 있으면 True 반환.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[SKIP] JSON 읽기 실패: {filepath} ({e})")
        return False

    new_data, changed = process_json_obj(data, prune_empty=prune_empty)

    if not changed:
        return False

    if dry_run:
        print(f"[DRY-RUN] 변경 예정: {filepath}")
        return True

    # 백업
    if backup:
        bak_path = filepath + '.bak'
        try:
            if not os.path.exists(bak_path):
                with open(bak_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[WARN] 백업 실패: {filepath} -> {bak_path} ({e})")

    # 저장
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, ensure_ascii=False, indent=2)
        print(f"[OK] 수정 저장: {filepath}")
        return True
    except Exception as e:
        print(f"[ERROR] 저장 실패: {filepath} ({e})")
        return False

def iter_json_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith('.json'):
                yield os.path.join(dirpath, fn)

def main():
    parser = argparse.ArgumentParser(description="PromptData 트리의 JSON에서 모델 관련 키 일괄 삭제")
    parser.add_argument('--root', default='/yaas/agent/a5_Database/a54_PromptData', help='루트 디렉토리 경로')
    parser.add_argument('--no-backup', action='store_true', help='백업(.bak) 생성하지 않음')
    parser.add_argument('--prune-empty', action='store_true', help='비어버린 OpenAI/ANTHROPIC 컨테이너도 삭제')
    parser.add_argument('--dry-run', action='store_true', help='실제 파일 저장 없이 변경 대상만 출력')
    args = parser.parse_args()

    root = args.root
    backup = not args.no_backup

    total = 0
    changed = 0
    for fp in iter_json_files(root):
        total += 1
        if process_file(fp, backup=backup, prune_empty=args.prune_empty, dry_run=args.dry_run):
            changed += 1

    mode = "DRY-RUN" if args.dry_run else "실행"
    print(f"\n[{mode} 완료] 총 파일: {total}, 변경된 파일: {changed}")

if __name__ == '__main__':
    main()