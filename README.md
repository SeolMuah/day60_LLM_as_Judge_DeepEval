# LLM-as-Judge와 DeepEval: 판사 모델 설계·편향·평가 지표·테스트 케이스

이 교안은 LLM을 평가자(판사 모델)로 활용해 여러 종류의 LLM 응답을 채점·비교하고, 그 판정을 사람 판정과 대조해 점검하는 방법을 다룹니다. LLM-as-Judge는 평가 방법이고 DeepEval은 테스트 케이스와 지표를 실행하는 프레임워크입니다. RAGAS도 RAG 지표 외에 일반 목적 평가 지표를 제공합니다. 이번 실습은 검색기 없이 준비된 입력·근거·답변을 평가합니다.

실습 대상은 수업용 가상 버추얼 아이돌 챗봇 **루나**와 **루나 굿즈 스토어 상담 챗봇**입니다. 등장하는 인물·설정·일정·정책은 모두 수업용 가상 자료입니다.

| 교안 | 배울 내용 | 본 실습 | 함께 따라하기 |
|---|---|---|---|
| [01 · LLM-as-Judge: 판사와 편향](교안_01_LLM_as_Judge_판사와_편향.ipynb) | 판사 프롬프트 설계, Direct Scoring(pass·fail), Pairwise와 무승부, 위치·장황함·권위 효과 확인, 양방향 판정, 사람 판정과 대조한 판사 성적표(일치율·실패 탐지율·정상 통과율·kappa), 놓친 실패·헛경보 읽기 | 루나 답변 40개를 평가 축 3개(페르소나·정확성·안전)로 채점(판사 호출 120번)하고 10쌍을 두 순서로 비교 | 굿즈 스토어 상담 v1·v2를 정책 기준으로 채점·비교하고 배포 여부 판단 |
| [02 · DeepEval: 지표와 테스트 케이스](교안_02_DeepEval_지표와_테스트_케이스.ipynb) | `LLMTestCase`, G-Eval(판단 단계·기준 답변·rubric), ArenaGEval, Hallucination, Toxicity·Bias, `evaluate()` 결과 읽기, 결함과 걸리는 방법 짝짓기, 평가 범위표 | 같은 평가셋 40개를 축별 지표로 평가하고 사람 판정·교안 01 판사와 성적표로 대조 | 정책 기준을 G-Eval로 옮겨 기록 16답으로 검증하고, 새 질문 6개의 답을 평가해 배포 여부 판단 |

두 교안은 같은 순서로 구성됩니다. 첫 부분에는 오늘 배울 내용과 학습 목표만 두고, **2절 실습 준비**에서 실습 대상(루나)과 모델·자료를 소개합니다. 두 교안은 같은 평가셋, 같은 `answer_id`, 같은 기준 문장(`axes`)을 씁니다.

| 과제 | 적용하는 교안 | 할 일 |
|---|---|---|
| [01 · 퀴즈 자동 채점: 판사 점검](과제_01_퀴즈_자동_채점_판사_점검.ipynb) | 교안 01 | 파이썬 퀴즈 답안 36개(단답 18·서술 18)를 LangChain 판사로 채점해 교사 판정과 대조하고, 기준 문장·장황함 효과를 점검해 문항 유형별로 판사에게 1차 채점을 맡길지 정합니다 |
| [02 · 퀴즈 자동 채점: DeepEval 테스트](과제_02_퀴즈_자동_채점_DeepEval_테스트.ipynb) | 교안 02 | 같은 답안을 DeepEval 테스트 케이스로 바꿔 단답(코드 규칙·G-Eval)과 서술(rubric G-Eval, 기준 답변 있이·없이)을 채점하고, 성적표와 평가 범위표로 채점 방법과 다음 답안 유형을 고릅니다 |

과제는 `[작성]` 셀의 `...`를 채우고 바로 아래 `[자가채점]` 셀로 확인한 뒤, 마지막에 결정 기록을 씁니다. 완성 코드는 `정답/`에 있습니다. 과제 02는 과제 01 결과에 의존하지 않습니다.

교안마다 맨 아래 **함께 따라하기**가 있습니다. 학생본에서 `✏️ 부분 작성` 표시가 있는 셀의 `...` 자리를 채운 뒤 실행합니다. 완성 코드는 `정답/`에 있습니다.

## 폴더 구조

```
day60_LLM_as_Judge_DeepEval/
├── 교안_01_LLM_as_Judge_판사와_편향.ipynb
├── 교안_02_DeepEval_지표와_테스트_케이스.ipynb
├── 과제_01_퀴즈_자동_채점_판사_점검.ipynb
├── 과제_02_퀴즈_자동_채점_DeepEval_테스트.ipynb
├── 정답/                교안·과제 정답 노트북
├── .env.example         API 키·모델 설정 예시(비밀 키 없음)
├── data/
│   ├── 본실습/          루나 설정·공지와 평가셋
│   ├── 따라하기/        굿즈 스토어 정책과 평가셋
│   └── 과제/            과제 01·02 공용 파이썬 퀴즈 답안과 교사 판정
├── images/              개념 그림
├── results/             실행할 때 생기는 판사 결과 CSV(git에 올리지 않음)
└── scripts/             평가셋 검사 스크립트, 그림 원본과 생성 기록
```

### 교안에서 쓰는 자료

평가셋의 답변은 모두 **사람이 쓴 통제 입력**입니다. 모델이 만든 답이 아니라, 어느 축에 걸려야 하는지 정해 둔 답입니다.

| 자료 | 내용 | 쓰는 곳 |
|---|---|---|
| `data/본실습/luna_guide.json` | 루나 설정과 가상 팬미팅 공지 문장 8개(L1–L8), 판정에 쓸 정보의 범위(`evidence_scope`) | 01·02 |
| `data/본실습/luna_golden_set.json` | 루나 평가셋. 평가 축 3개의 기준 문장(`axes`), 질문 8개 × 답변 변형 5개 = 답변 40개, 축별 사람 판정 120칸과 이유, 질문마다 기준 답변, 두 답 비교 10쌍과 사람 승자 | 01·02 |
| `data/따라하기/store_policies.json` | 굿즈 스토어 가상 정책 5개(P1–P5: 단순 변심, 파손·오배송, 랜덤 포토카드, 주문 제작, 주문 확인·환불 시점) | 01·02 |
| `data/따라하기/store_golden_set.json` | 스토어 평가셋. 정책 축 기준 문장(`axes.정책`), 상담 기록 S01–S08의 v1·v2 답 16개와 사람 판정, 쌍 8개와 사람 승자, 답을 새로 만들어 평가할 질문 T1–T6 | 01·02 |

| `data/과제/python_quiz_set.json` | 과제용 파이썬 퀴즈. 문항 6개(단답 3·서술 3), 학생 답안 36개와 교사 판정(pass 18·fail 18), 채점 규칙(`grading_rules`), 서술형 쌍 6개, 평가 범위 목표(`coverage_targets`). 자세한 설명은 [`data/과제/README.md`](data/과제/README.md) | 과제 01·02 |

강사는 평가셋을 고친 뒤 `python scripts/check_golden_set.py`로 API 없이 검사합니다(축별 fail 수, 쌍 승자와 라벨 규칙, 기준 답변과 같은 답 등). 문제가 없으면 "통과: 문제 0건"이 출력됩니다. 과제 데이터는 `python scripts/check_quiz_set.py`로 같은 방식으로 검사합니다.

### 실행 결과(`results/`)

교안을 실행하면 `results/`에 판사 결과 CSV가 생깁니다. 모든 CSV에 판사 모델 열이 있습니다.

| 파일 | 만드는 곳 | 읽는 곳 |
|---|---|---|
| `lesson01_luna_direct.csv` | 교안 01 Direct Scoring(120행) | 교안 02 성적표 비교 |
| `lesson01_luna_pairwise.csv` | 교안 01 Pairwise·양방향 판정(10행) | 교안 02 ArenaGEval |
| `lesson01_store_direct.csv` | 교안 01 함께 따라하기(16행) | 교안 02 함께 따라하기 기록 검증 |
| `lesson02_luna_deepeval.csv` | 교안 02 세 축 판정(96행) | 없음(기록용) |

교안 01 결과 CSV가 없으면 교안 02는 교안 01을 먼저 실행하라는 안내를 한 줄 출력하고 DeepEval 결과만 보여 줍니다.

### 현재 교안에서 쓰지 않는 자료

이전 판의 실습(한빛바이크 이용 안내·복약 안내 챗봇) 자료입니다. 지금 교안은 이 파일들을 읽지 않으며, 참고용으로 남겨 두었습니다.

| 자료 | 내용 |
|---|---|
| `data/bike_guide.json`, `data/bike_answers.json`, `data/bike_cases.json` | 수업용 가상 공공자전거 안내 문장, 답변과 사람 판정, 결함 사례 |
| `data/drug_docs.json`, `data/drug_chatbot_log.json` | 일반의약품 6종 문서(출처: 식품의약품안전처 의약품개요정보(e약은요), 공공데이터포털)와 복약 안내 챗봇 응답 |
| `images/02_direct_pairwise_reference.svg` | 그림 02의 원본 벡터 파일 |

## 준비

1. `실습자료` 폴더에서 `uv sync`로 공용 환경을 맞춥니다. 이 환경의 DeepEval은 **4.1.1**입니다.
2. 이 레포의 `.env.example`을 `.env`로 복사하고 `OPENAI_API_KEY`를 설정합니다. 답변·판사 모델 이름은 필요하면 조정합니다. 상위 실습자료의 `.env`를 사용할 수도 있습니다.
   - `OPENAI_CHAT_MODEL`: 챗봇 답변 모델(기본 `gpt-5.6-luna`). 교안 02에서 새 답변을 만들 때만 씁니다.
   - `OPENAI_EVAL_MODEL`: 판사 모델(기본 `gpt-4.1`). G-Eval에 토큰 로그확률(`logprobs`)이 필요하므로, 상위 `.env`를 재사용하면 선택 모델의 지원 여부를 확인합니다.
3. 교안 02의 준비 셀은 `DEEPEVAL_TELEMETRY_OPT_OUT=1`로 DeepEval이 사용 기록을 외부로 보내지 않게 합니다. deepeval을 불러오기 전에 정해야 해서 `.env`가 아니라 코드에서 정합니다.
4. DeepEval은 실행한 폴더에 `.deepeval/` 폴더를 만들고, `evaluate` 끝에 Confident AI 안내 문구를 출력합니다. 둘 다 이 실습에는 필요 없으며 `.gitignore`에 넣어 두었습니다.

**점수 방향 주의:** DeepEval 4.1.1에서 Hallucination·Toxicity·Bias는 **낮을수록 좋은** 점수입니다. 이 설명은 uv.lock에 고정된 버전과 [4.1.1 Hallucination 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/hallucination/hallucination.py)에 맞췄습니다. 다른 버전의 온라인 문서·코드에서는 점수 방향과 세부 동작이 달라질 수 있으므로 설치 버전을 먼저 확인합니다.

**빠른 모드:** 두 교안의 준비 셀에 있는 `RUN_QIDS = None`을 `["Q1", "Q3", "Q5", "Q7"]`로 바꾸면 루나 답변 20개만 평가합니다. 교안 01 Direct Scoring은 판사 호출 120번이 60번으로 줄고, 쌍 비교와 함께 따라하기는 그대로입니다. 429 오류가 나면 코드의 동시 실행 수(`max_concurrency`·`max_concurrent`)를 32에서 8로 낮춥니다.

판사 모델의 판정과 점수는 실행마다 달라질 수 있습니다. 그래서 교안은 결과를 미리 단정하지 않고, 결과 뒤에 조건형 읽기('…라면 …입니다')와 접는 질문을 두었습니다.

### 강사 리허설 체크리스트

수업 전에 실제 API 키로 두 교안을 한 번 실행하고 다음 세 가지를 확인합니다.

1. 교안 01 Direct Scoring에서 축별로 사람 판정과 다른 칸 수
2. 교안 01 Pairwise에서 무승부 4쌍(PR01–PR04)의 판정
3. 교안 02 Hallucination 16개 표에서 `Q5-정보_오류`의 점수

## 용어

두 교안과 정답본은 아래 용어를 같은 뜻으로 씁니다.

| 용어 | 뜻 | 데이터·코드 이름 |
|---|---|---|
| 평가셋 | 사람이 미리 확인한 질문·답변·사람 판정·기준 답변 묶음 | `luna_golden_set.json`, `store_golden_set.json` |
| 평가 축 | 답변을 볼 관점 하나. 루나는 페르소나·정확성·안전 3개, 함께 따라하기는 정책 1개 | `axes`(축마다 `criterion`·`steps`·`fail_tags`·`allowed`) |
| 사람 판정 | 사람이 미리 매긴 pass·fail | `labels`, `label_v1`·`label_v2` |
| 판사 판정 | 판사 모델(또는 DeepEval 지표)이 낸 pass·fail | 표의 `판사` 열 |
| 기준 답변 | 사람이 확인한 모범 답 문장 | `expected_output`(루나), `reference`(스토어) |
| 사람 승자 | 두 답 중 사람이 더 낫다고 본 답의 ID 또는 무승부 | `human_winner`, `human_better` |
| 판사 성적표 | 일치율·실패 탐지율·정상 통과율·kappa | `scorecard()` |
| 놓친 실패·헛경보 | 사람 fail을 판사가 pass로 본 칸 · 사람 pass를 판사가 fail로 본 칸 | 성적표 아래 표의 `구분` 열 |

## RAGAS와 LLM-as-Judge·DeepEval의 관계와 실무 적용

- 공통점: RAGAS와 DeepEval은 모두 평가 지표를 실행할 수 있으며, LLM 기반 판정도 활용합니다.
- 차이와 초점: RAGAS는 RAG를 포함한 다양한 평가 지표 모음입니다. LLM-as-Judge는 판정 방법이고 DeepEval은 그 방법을 테스트 케이스와 지표에 적용하는 프레임워크입니다. 따라서 RAGAS를 RAG 전용, DeepEval을 일반 평가 전용으로 나누지 않습니다.
- 오늘의 실습: 검색기를 실행하지 않고 준비된 답변을 대상으로 일반 응답의 기준을 설계합니다. 후보 답변 비교는 Pairwise/ArenaGEval로 다룹니다.
- 실무 예: 사람 확인 사례를 기준 세트로 유지하고, 모델·프롬프트 변경 전후에 재평가합니다. 먼저 작은 묶음으로 판정 결과와 비용을 확인하고, 실패 탐지와 헛경보를 사람 판정과 함께 살펴 기준을 보완합니다. Pairwise 승자와 배포 가능 여부(절대 기준 통과)는 따로 판단합니다.

## 공식 문서와 구현 확인

- [DeepEval 평가 소개](https://deepeval.com/docs/evaluation-introduction)
- [DeepEval 테스트 케이스](https://deepeval.com/docs/evaluation-test-cases)
- [DeepEval 비동기 실행과 동시성 설정](https://deepeval.com/docs/evaluation-flags-and-configs)
- [LangChain Runnable.batch 공식 문서](https://reference.langchain.com/python/langchain-core/runnables/base/Runnable/batch)
- [DeepEval 메트릭 소개](https://deepeval.com/docs/metrics-introduction)
- [DeepEval G-Eval](https://deepeval.com/docs/metrics-llm-evals)
- [DeepEval의 OpenAI 모델 및 G-Eval logprobs 조건](https://deepeval.com/integrations/models/openai)
- [RAGAS 지표 목록](https://docs.ragas.io/en/latest/concepts/metrics/available_metrics/)
- [DeepEval 4.1.1 Hallucination 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/hallucination/hallucination.py)
- [DeepEval 4.1.1 Toxicity 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/toxicity/toxicity.py)
- [DeepEval 4.1.1 Bias 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/bias/bias.py)
- [DeepEval 4.1.1 ArenaGEval 이름 가리기·순서 섞기 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/arena_g_eval/utils.py)
- [DeepEval 환경 변수와 telemetry opt-out](https://deepeval.com/docs/environment-variables)
