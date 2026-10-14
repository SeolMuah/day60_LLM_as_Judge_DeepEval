"""평가셋 검사(강사용, 재설계안 3-9).

루나 평가셋(data/본실습)과 스토어 평가셋(data/따라하기)을 표준 라이브러리만으로 검사합니다.
문제를 모두 모아 출력하고, 하나라도 있으면 종료 코드 1로 끝납니다.

실행: python scripts/check_golden_set.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # 스크립트 위치 기준이라 어디서 실행해도 같은 파일을 읽음
LUNA_DIR = ROOT / "data" / "본실습"
STORE_DIR = ROOT / "data" / "따라하기"

VARIANTS = ["정상", "길게_늘임", "말투_깨짐", "정보_오류", "존중_위반"]
LUNA_AXES = ["페르소나", "정확성", "안전"]
TIE = "무승부"

errors = []


def check(ok, message):
    """조건이 거짓이면 문제를 모아 둡니다(바로 멈추지 않음)."""
    if not ok:
        errors.append(message)
    return ok


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def winner_by_rule(a_id, b_id, a_label, b_label):
    """3-7 규칙 3: pass와 fail이면 pass, 둘 다 pass면 무승부, 둘 다 fail이면 None(심각도로 정함)."""
    if a_label != b_label:
        return a_id if a_label == "pass" else b_id
    return TIE if a_label == "pass" else None


def check_reason(where, reason, axis_rule, valid_ids, answer_text, passed):
    """reasons 형식 '태그 · 근거ID · '문제 표현''을 검사합니다."""
    parts = [p.strip() for p in reason.split(" · ")]
    if not check(len(parts) >= 2, f"{where}: reasons 형식이 '태그 · 근거ID · ...'가 아님 → {reason}"):
        return
    tag, evidence_id = parts[0], parts[1]
    if passed:  # pass 축의 근거는 허용 항목만 적음
        check(tag.endswith("(허용)") and tag.removesuffix("(허용)") in axis_rule["allowed"],
              f"{where}: pass 축 태그 '{tag}'가 allowed에 없음")
    else:
        check(tag in axis_rule["fail_tags"], f"{where}: fail 태그 '{tag}'가 fail_tags에 없음")
    check(evidence_id in valid_ids, f"{where}: 근거ID '{evidence_id}'가 허용 범위 밖")
    for quote in re.findall(r"'([^']+)'", reason):  # 인용한 표현이 실제 답에 있는지
        for piece in quote.split("..."):
            check(piece.strip() in answer_text, f"{where}: 인용 '{piece.strip()}'가 답변에 없음")


def check_luna():
    guide = load(LUNA_DIR / "luna_guide.json")
    data = load(LUNA_DIR / "luna_golden_set.json")
    guide_ids = [s["id"] for s in guide["sentences"]]
    check(guide_ids == [f"L{i}" for i in range(1, 9)], f"루나 설정 문장 ID가 L1–L8이 아님: {guide_ids}")
    evidence_ids = set(guide_ids) | {"evidence_scope"}  # Q7 지어낸 신곡은 목록 밖 정보라 evidence_scope를 근거로 씀

    check(list(data["variants"]) == VARIANTS, f"variants 이름·순서가 다름: {list(data['variants'])}")
    check(list(data["axes"]) == LUNA_AXES, f"axes가 {LUNA_AXES}가 아님: {list(data['axes'])}")
    questions = data["questions"]
    check([q["question_id"] for q in questions] == [f"Q{i}" for i in range(1, 9)], "질문 ID가 Q1–Q8이 아님")

    answers = {}
    fail_count = Counter()
    boundary = 0
    for q in questions:
        qid = q["question_id"]
        for cid in q["context_ids"]:
            check(cid in guide_ids, f"{qid}: context_ids '{cid}'가 L1–L8 밖")
        variants = [a["variant"] for a in q["answers"]]
        check(sorted(variants) == sorted(VARIANTS), f"{qid}: 변형 5종이 하나씩 있지 않음 → {variants}")
        for a in q["answers"]:
            aid = a["answer_id"]
            check(aid == f"{qid}-{a['variant']}", f"{aid}: answer_id가 '{qid}-{a['variant']}' 형식이 아님")
            check(aid not in answers, f"{aid}: answer_id 중복")
            answers[aid] = a
            boundary += a["boundary"] is True
            check(a["actual_output"].strip() != q["expected_output"].strip(), f"{aid}: actual_output이 expected_output과 같음")
            check(list(a["labels"]) == LUNA_AXES, f"{aid}: labels 축이 {LUNA_AXES}가 아님")
            for axis in LUNA_AXES:
                label = a["labels"].get(axis)
                if not check(label in ("pass", "fail"), f"{aid}: {axis} 라벨이 pass/fail이 아님 → {label}"):
                    continue
                expected = "fail" if data["variants"][a["variant"]] == axis else "pass"
                check(label == expected, f"{aid}: {axis} 라벨 {label} (변형 {a['variant']}이면 {expected})")
                fail_count[axis] += label == "fail"
                reason = a["reasons"].get(axis)
                if label == "fail":
                    check(bool(reason), f"{aid}: fail 축 '{axis}'에 reasons가 없음")
                if reason:
                    check_reason(f"{aid} {axis}", reason, data["axes"][axis], evidence_ids,
                                 a["actual_output"], passed=label == "pass")
            for axis in a["reasons"]:
                check(axis in LUNA_AXES, f"{aid}: reasons에 없는 축 '{axis}'")

    check(len(answers) == 40, f"답변 수 {len(answers)} (기대 40)")
    check(boundary == 13, f"경계 답 {boundary}개 (기대 13)")
    for axis in LUNA_AXES:
        check(fail_count[axis] == 8, f"{axis} 축 fail {fail_count[axis]}건 (기대 8)")

    pairs = data["pairs"]
    check(len(pairs) == 10, f"루나 쌍 {len(pairs)}개 (기대 10)")
    seat = Counter()
    for p in pairs:
        pid, a_id, b_id, axis = p["pair_id"], p["a"], p["b"], p["axis"]
        if not check(a_id in answers and b_id in answers, f"{pid}: 없는 answer_id ({a_id}, {b_id})"):
            continue
        check(a_id.split("-")[0] == b_id.split("-")[0] == p["question_id"], f"{pid}: a·b가 {p['question_id']}의 답이 아님")
        check(axis in LUNA_AXES, f"{pid}: 축 '{axis}'가 없음")
        check(p["use"] in ("장황함", "위치", "권위"), f"{pid}: use '{p['use']}'가 장황함·위치·권위가 아님")
        rule = winner_by_rule(a_id, b_id, answers[a_id]["labels"][axis], answers[b_id]["labels"][axis])
        check(rule is not None, f"{pid}: 둘 다 fail인 쌍은 루나에 없어야 함(스토어 S07에만)")
        check(p["human_winner"] == rule, f"{pid}: 사람 승자 {p['human_winner']} (라벨 규칙: {rule})")
        if p["human_winner"] == TIE:  # 무승부 쌍은 긴 답이 어느 자리에 있는지 셈
            longer_a = len(answers[a_id]["actual_output"]) > len(answers[b_id]["actual_output"])
            seat["무승부·긴 답 a" if longer_a else "무승부·긴 답 b"] += 1
        else:
            seat["승부·a 승" if p["human_winner"] == a_id else "승부·b 승"] += 1
    for key, n in [("승부·a 승", 3), ("승부·b 승", 3), ("무승부·긴 답 a", 2), ("무승부·긴 답 b", 2)]:
        check(seat[key] == n, f"루나 쌍 자리 균형: {key} {seat[key]} (기대 {n})")

    return {"답변": len(answers), "경계": boundary, "fail": dict(fail_count), "쌍": len(pairs), "자리": dict(seat)}


def check_store():
    policies = load(STORE_DIR / "store_policies.json")
    data = load(STORE_DIR / "store_golden_set.json")
    policy_ids = [p["policy_id"] for p in policies]
    check(policy_ids == [f"P{i}" for i in range(1, 6)], f"정책 ID가 P1–P5가 아님: {policy_ids}")
    rule = data["axes"]["정책"]

    records = {r["question_id"]: r for r in data["records"]}
    check(list(records) == [f"S{i:02d}" for i in range(1, 9)], f"기록 ID가 S01–S08이 아님: {list(records)}")
    passes = Counter()
    for sid, r in records.items():
        for pid in r["policy_ids"]:
            check(pid in policy_ids, f"{sid}: policy_ids '{pid}'가 P1–P5 밖")
        for v in ("v1", "v2"):
            label, answer, reason = r[f"label_{v}"], r[f"answer_{v}"], r[f"reason_{v}"]
            if not check(label in ("pass", "fail"), f"{sid}-{v}: 라벨이 pass/fail이 아님 → {label}"):
                continue
            passes[v] += label == "pass"
            check(answer.strip() != r["reference"].strip(), f"{sid}-{v}: 답이 기준 답변과 같음")
            if label == "fail" and check(bool(reason), f"{sid}-{v}: fail인데 이유가 없음"):
                check_reason(f"{sid}-{v}", reason, rule, set(policy_ids), answer, passed=False)
    check(passes["v1"] == 5, f"스토어 v1 pass {passes['v1']}개 (기대 5)")
    check(passes["v2"] == 3, f"스토어 v2 pass {passes['v2']}개 (기대 3)")
    s07 = records.get("S07", {})
    check(s07.get("label_v1") == s07.get("label_v2") == "fail", "S07: v1·v2가 둘 다 fail이 아님")

    pairs = data["pairs"]
    check(len(pairs) == 8, f"스토어 쌍 {len(pairs)}개 (기대 8)")
    wins = Counter()
    for p in pairs:
        pid, sid = p["pair_id"], p["question_id"]
        r = records.get(sid)
        if not check(r is not None, f"{pid}: 기록 {sid}가 없음"):
            continue
        check((p["a"], p["b"]) == (f"{sid}-v1", f"{sid}-v2"), f"{pid}: a·b가 {sid}-v1·{sid}-v2가 아님")
        by_rule = winner_by_rule(p["a"], p["b"], r["label_v1"], r["label_v2"])
        if by_rule is None:  # 둘 다 fail: 승자는 심각도로 정하므로 무승부일 수 없음
            check(sid == "S07", f"{pid}: 둘 다 fail인 쌍은 S07에만 있어야 함")
            check(p["human_winner"] in (p["a"], p["b"]), f"{pid}: 둘 다 fail이면 심각도로 승자를 정해야 함")
        else:
            check(p["human_winner"] == by_rule, f"{pid}: 사람 승자 {p['human_winner']} (라벨 규칙: {by_rule})")
        better = TIE if p["human_winner"] == TIE else p["human_winner"].split("-")[1]
        check(r["human_better"] == better, f"{sid}: human_better {r['human_better']}와 쌍 승자 {better}가 다름")
        wins[better] += 1
    check(dict(wins) == {"v1": 4, "v2": 3, TIE: 1}, f"스토어 쌍 결과 {dict(wins)} (기대 v1 4·v2 3·무승부 1)")

    new_ids = [t["question_id"] for t in data["new_questions"]]
    check(new_ids == [f"T{i}" for i in range(1, 7)], f"새 질문 ID가 T1–T6이 아님: {new_ids}")
    for t in data["new_questions"]:
        for pid in t["policy_ids"]:
            check(pid in policy_ids, f"{t['question_id']}: policy_ids '{pid}'가 P1–P5 밖")
        check("answer_v1" not in t and "answer_v2" not in t, f"{t['question_id']}: 새 질문에 답이 들어 있음")

    return {"v1 pass": passes["v1"], "v2 pass": passes["v2"], "쌍": len(pairs), "쌍 결과": dict(wins)}


def main():
    summary = {}
    for name, fn in [("루나", check_luna), ("스토어", check_store)]:
        try:
            summary[name] = fn()
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as e:  # 파일·필드가 없으면 그 평가셋 검사만 멈춤
            errors.append(f"{name}: 검사를 끝내지 못함 → {type(e).__name__}: {e}")

    for name, s in summary.items():
        print(f"[{name}] {s}")
    if errors:
        print(f"\n문제 {len(errors)}건")
        for e in errors:
            print(f"- {e}")
        sys.exit(1)
    print("\n통과: 문제 0건")


if __name__ == "__main__":
    main()
