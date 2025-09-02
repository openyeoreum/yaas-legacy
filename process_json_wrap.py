#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import shutil
import argparse
from pathlib import Path
from typing import Tuple
from collections import OrderedDict
import copy

KO_SUFFIX_RE = re.compile(r"\(ko\)\.json$", re.IGNORECASE)

def rename_if_ko_suffix(p: Path) -> Path:
    """파일명이 '(ko).json'으로 끝나면 '(ko)'를 제거한 새 경로로 rename 후 그 경로를 반환."""
    name = p.name
    if KO_SUFFIX_RE.search(name):
        new_name = KO_SUFFIX_RE.sub(".json", name)
        new_path = p.with_name(new_name)
        # 동일 파일이 이미 있으면 덮어씀 (요구사항 충족을 위해 명시적 교체)
        p.replace(new_path)
        return new_path
    return p

def is_already_wrapped(data) -> bool:
    """이미 {'ko': dict, 'global': dict} 형태인지 판별."""
    if isinstance(data, dict) and set(data.keys()) == {"ko", "global"}:
        return isinstance(data.get("ko"), dict) and isinstance(data.get("global"), dict)
    return False

def load_json_preserve_order(p: Path) -> OrderedDict:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f, object_pairs_hook=OrderedDict)

def dump_json_atomic(p: Path, data: OrderedDict):
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        f.write("\n")
    tmp.replace(p)

def process_json_file(p: Path) -> Tuple[bool, str]:
    """
    파일 하나 처리.
    반환: (변경여부, 메시지)
    """
    try:
        # 1) 파일명 정리
        p = rename_if_ko_suffix(p)

        # 2) 로드 (순서 유지)
        data = load_json_preserve_order(p)
        if not isinstance(data, dict):
            return False, f"[SKIP] 최상위가 dict가 아님: {p}"

        # 이미 래핑된 경우는 그대로 둠
        if is_already_wrapped(data):
            return False, f"[OK] 이미 {'ko','global'} 구조: {p}"

        # 3) {'ko': 원본, 'global': 원본복사}로 감싸기 (내부 순서 보존)
        original = data  # OrderedDict
        wrapped = OrderedDict()
        wrapped["ko"] = original
        wrapped["global"] = copy.deepcopy(original)

        # 4) 저장 (atomic, indent=4, UTF-8, 순서 유지)
        dump_json_atomic(p, wrapped)
        return True, f"[UPDATED] 구조 래핑 완료: {p}"

    except json.JSONDecodeError as e:
        return False, f"[ERROR] JSON 파싱 실패: {p} ({e})"
    except Exception as e:
        return False, f"[ERROR] 처리 중 예외: {p} ({e})"

def main():
    parser = argparse.ArgumentParser(description="폴더 트리의 JSON을 (ko) 접미사 제거 및 {'ko','global'} 구조로 래핑")
    parser.add_argument("root", nargs="?", default="/yaas/agent/a5_Database/a54_PromptData",
                        help="루트 폴더 경로 (기본값: /yaas/agent/a5_Database/a54_PromptData)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"[ERROR] 경로가 존재하지 않습니다: {root}")
        return

    # 안전을 위해 읽기 전 전체를 백업하려면 아래 주석 해제 (선택사항)
    # backup_dir = root.with_name(root.name + "_backup")
    # if not backup_dir.exists():
    #     shutil.copytree(root, backup_dir)
    #     print(f"[INFO] 백업 완료: {backup_dir}")

    updated = 0
    checked = 0
    for p in root.rglob("*.json"):
        if not p.is_file():
            continue
        checked += 1
        changed, msg = process_json_file(p)
        if changed:
            updated += 1
        print(msg)

    print(f"\n[SUMMARY] 확인 {checked}개, 갱신 {updated}개")

if __name__ == "__main__":
    main()