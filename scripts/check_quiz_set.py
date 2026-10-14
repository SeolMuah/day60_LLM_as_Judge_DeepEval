"""과제 데이터(data/과제/python_quiz_set.json)를 API 없이 검사합니다.

사용법: python scripts/check_quiz_set.py
- 문항 유형별 답안 수와 교사 판정 수(문항마다 pass 3·fail 3)
- 답안 ID 형식, 답안 유형 이름이 answer_types에 있는지
- 서술형 교사 판정이 채점 항목 A·B 규칙(둘 다 충족해야 pass)과 맞는지
- 쌍의 교사 승자가 pair_rule(충족 항목 수 비교)과 맞는지
- 평가 범위 목표(coverage_targets)에 실제 답안 유형이 모두 들어 있는지
"""
import json
from collections import Counter
from pathlib import Path

data = json.loads((Path(__file__).resolve().parent.parent / "data" / "과제" / "python_quiz_set.json").read_text(encoding="utf-8"))
problems = []
answers = {}
for item in data["items"]:
    kind = item["item_type"]
    types = data["answer_types"][kind]
    verdicts = Counter(answer["teacher"] for answer in item["answers"])
    if verdicts != Counter({"pass": 3, "fail": 3}):
        problems.append(f"{item['item_id']}: 교사 판정이 pass 3·fail 3이 아님 {dict(verdicts)}")
    if [answer["answer_type"] for answer in item["answers"]] != list(types):
        problems.append(f"{item['item_id']}: 답안 유형 순서가 answer_types[{kind}]와 다름")
    if kind == "서술" and set(item.get("rubric", {})) != {"A", "B"}:
        problems.append(f"{item['item_id']}: 서술형에는 채점 항목 A·B가 필요함")
    for answer in item["answers"]:
        answers[answer["answer_id"]] = (item, answer)
        if answer["answer_id"] != f"{item['item_id']}-{answer['answer_type']}":
            problems.append(f"{answer['answer_id']}: 답안 ID는 '문항 ID-답안 유형' 형식")
        if answer["answer"].strip() == item["reference"].strip() and answer["answer_type"] not in ("정답",):
            problems.append(f"{answer['answer_id']}: 기준 답변과 같은 답안")
        if not answer["teacher_reason"]:
            problems.append(f"{answer['answer_id']}: 교사 이유가 비어 있음")
        if kind == "서술":
            expected = "pass" if all(answer["criteria"].values()) else "fail"
            if answer["teacher"] != expected:
                problems.append(f"{answer['answer_id']}: A·B 충족({answer['criteria']})과 교사 판정({answer['teacher']})이 맞지 않음")

total = Counter(answer["teacher"] for _, answer in answers.values())
if total != Counter({"pass": 18, "fail": 18}):
    problems.append(f"전체 교사 판정이 pass 18·fail 18이 아님 {dict(total)}")

for pair in data["pairs"]:
    met = {}
    for side in ("a", "b"):
        item, answer = answers[pair[side]]
        if item["item_id"] != pair["item_id"]:
            problems.append(f"{pair['pair_id']}: {side} 답안이 다른 문항")
        met[pair[side]] = sum(answer["criteria"].values())
    a_met, b_met = met[pair["a"]], met[pair["b"]]
    expected = "무승부" if a_met == b_met else (pair["a"] if a_met > b_met else pair["b"])
    if pair["teacher_winner"] != expected:
        problems.append(f"{pair['pair_id']}: 교사 승자 {pair['teacher_winner']}가 충족 항목 수 규칙({expected})과 다름")

for kind, targets in data["coverage_targets"].items():
    missing = set(data["answer_types"][kind]) - set(targets)
    if missing:
        problems.append(f"coverage_targets[{kind}]에 실제 답안 유형 {missing}이 없음")

print(f"문항 {len(data['items'])}개, 답안 {len(answers)}개, 쌍 {len(data['pairs'])}개")
print("통과: 문제 0건" if not problems else "문제 발견:\n- " + "\n- ".join(problems))
