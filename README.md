# LLM-as-Judge와 DeepEval: 판사 모델 설계·편향·평가 지표·테스트 케이스

이 교안은 LLM을 평가자(판사 모델)로 활용해 여러 종류의 LLM 응답을 채점·비교하고, 그 판정을 사람 판정과 대조해 점검하는 방법을 다룹니다. LLM-as-Judge는 평가 방법이고 DeepEval은 테스트 케이스와 지표를 실행하는 프레임워크입니다. RAGAS도 RAG 지표 외에 일반 목적 평가 지표를 제공합니다. 이번 실습은 검색기 없이 준비된 입력·근거·답변을 평가합니다.

실습 대상은 수업용 가상 버추얼 아이돌 챗봇 **루나**와 **루나 굿즈 스토어 상담 챗봇**입니다. 등장하는 인물·설정·일정·정책은 모두 수업용 가상 자료입니다.

| 교안 | 배울 내용 | 본 실습 | 함께 따라하기 |
|---|---|---|---|
| [01 · LLM-as-Judge: 판사와 편향](교안_01_LLM_as_Judge_판사와_편향.ipynb) | 판사 프롬프트 설계, Direct Scoring(pass·fail, 1~5점 점수별 기준, 기준 답변), Pairwise와 무승부, 위치·장황함·권위 효과 확인, 순서를 바꿔 두 번 묻기, 사람 판정과 대조(일치율·실패 탐지율·정상 통과율·kappa) | 루나 답변 22개를 5개 평가 축으로 채점 | 굿즈 스토어 상담 v1·v2를 정책 기준으로 비교하고 배포 여부 판단 |
| [02 · DeepEval: 지표와 테스트 케이스](교안_02_DeepEval_지표와_테스트_케이스.ipynb) | `LLMTestCase`, G-Eval(판단 단계·기준 답변·rubric), ArenaGEval, Hallucination, Toxicity·Bias, 형식 코드 검사, 평가 축별 판사 점검, 평가 범위표, `evaluate()` 결과 읽기 | 루나 사례를 지표로 평가하고 사람 판정과 대조 | 굿즈 스토어 상담 답변을 정책 준수 G-Eval로 평가 |

두 교안은 같은 순서로 구성됩니다. 첫 부분에는 오늘 배울 내용과 학습 목표만 두고, **2절 실습 준비**에서 실습 대상(루나)과 모델·자료를 소개합니다.

교안마다 맨 아래 **함께 따라하기**가 있습니다. 학생본에서 `✏️ 직접 설계`·`✏️ 부분 작성` 표시가 있는 셀의 `...` 자리를 채운 뒤 실행합니다. 완성 코드는 `정답/`에 있습니다.

## 폴더 구조

```
day60_LLM_as_Judge_DeepEval/
├── 교안_01_LLM_as_Judge_판사와_편향.ipynb
├── 교안_02_DeepEval_지표와_테스트_케이스.ipynb
├── 정답/                교안 정답 노트북(함께 따라하기 완성본)
├── .env.example         API 키·모델 설정 예시(비밀 키 없음)
├── data/                실습 자료(아래 표)
├── images/              개념 그림
└── scripts/             이미지 생성 기록
```

### 교안에서 쓰는 자료

| 자료 | 내용 | 쓰는 곳 |
|---|---|---|
| `data/luna_guide.json` | 루나 설정과 가상 팬미팅 공지 문장 8개(L1~L8), 판정에 쓸 정보의 범위 | 01·02 |
| `data/luna_answers.json` | 질문 4개(Q1~Q4)에 대한 답변 22개. 평가 축(`dimension`), 사람 판정(pass 12·fail 10), 이유, 기준 답변 | 01 |
| `data/luna_pairwise_cases.json` | 두 답 비교 사례 6건(LP01~LP06). 사람 선호와 각 답의 사람 판정 | 01, 02(LP04) |
| `data/luna_metric_cases.json` | 주된 결함을 하나씩 심은 지표 연습 사례 8건 | 02 |
| `data/luna_eval_cases.json` | 페르소나 3·질문 충족 3·형식 2·근거성 3·존중 표현 2·편향 2 = 15건과 사람 판정(pass 7·fail 8) | 02 |
| `data/luna_coverage_cases.json` | 평가 축과 근거 상태(준비된 기준·정확한 형식·공식 정보 있음·정보 없음·틀린 전제)를 조합한 새 질문 6건 | 02 |
| `data/store_policies.json` | 굿즈 스토어 가상 정책 5개(P1~P5: 단순 변심, 파손·오배송, 랜덤 포토카드, 주문 제작, 주문 확인·환불 시점) | 01·02 |
| `data/store_chatbot_log.json` | 상담 질문 8건(S01~S08)의 v1·v2 답변 16개, 사람 판정, 검토 이유, 상대 선호(`human_better`), 필수 안내(`required_points`) | 01·02 |
| `data/store_coverage_cases.json` | 답을 새로 만들어 평가할 상담 질문 6건(T1~T6)과 기준 답변 | 02 |

### 현재 교안에서 쓰지 않는 자료

이전 판의 실습(한빛바이크 이용 안내·복약 안내 챗봇) 자료입니다. 지금 교안은 이 파일들을 읽지 않으며, 참고용으로 남겨 두었습니다.

| 자료 | 내용 |
|---|---|
| `data/bike_guide.json`, `data/bike_answers.json`, `data/bike_cases.json` | 수업용 가상 공공자전거 안내 문장, 답변과 사람 판정, 결함 사례 |
| `data/drug_docs.json`, `data/drug_chatbot_log.json` | 일반의약품 6종 문서(출처: 식품의약품안전처 의약품개요정보(e약은요), 공공데이터포털)와 복약 안내 챗봇 응답 |
| `images/00_lesson01_scope.png`, `images/15_opinion_metrics.png`, `images/02_direct_pairwise_reference.svg` | 현재 교안에 넣지 않은 그림과 원본 벡터 파일 |

## 준비

1. `실습자료` 폴더에서 `uv sync`로 공용 환경을 맞춥니다. 이 환경의 DeepEval은 **4.1.1**입니다.
2. 이 레포의 `.env.example`을 `.env`로 복사하고 `OPENAI_API_KEY`를 설정합니다. 답변·판사 모델 이름은 필요하면 조정합니다. 상위 실습자료의 `.env`를 사용할 수도 있습니다.
   - `OPENAI_CHAT_MODEL`: 챗봇 답변 모델(기본 `gpt-5.6-luna`). 교안 02에서 새 답변을 만들 때만 씁니다.
   - `OPENAI_EVAL_MODEL`: 판사 모델(기본 `gpt-4.1`). G-Eval에 토큰 로그확률(`logprobs`)이 필요하므로, 상위 `.env`를 재사용하면 선택 모델의 지원 여부를 확인합니다.
3. 교안 02의 준비 셀은 `DEEPEVAL_TELEMETRY_OPT_OUT=1`로 DeepEval이 사용 기록을 외부로 보내지 않게 합니다. deepeval을 불러오기 전에 정해야 해서 `.env`가 아니라 코드에서 정합니다.
4. DeepEval은 실행한 폴더에 `.deepeval/` 폴더를 만들고, `evaluate` 끝에 Confident AI 안내 문구를 출력합니다. 둘 다 이 실습에는 필요 없으며 `.gitignore`에 넣어 두었습니다.

**점수 방향 주의:** DeepEval 4.1.1에서 Hallucination·Toxicity·Bias는 **낮을수록 좋은** 점수입니다. 이 설명은 uv.lock에 고정된 버전과 [4.1.1 Hallucination 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/hallucination/hallucination.py)에 맞췄습니다. 다른 버전의 온라인 문서·코드에서는 점수 방향과 세부 동작이 달라질 수 있으므로 설치 버전을 먼저 확인합니다.

판사 모델의 판정과 점수는 실행마다 달라질 수 있습니다. 교안의 "확인할 점"은 숫자 대신 어떤 출력 줄을 무엇과 비교하는지로 적었습니다.

## 용어

두 교안과 정답본은 아래 용어를 같은 뜻으로 씁니다.

| 용어 | 뜻 | 데이터·코드 이름 |
|---|---|---|
| 평가 축 | 답변을 볼 관점 하나(페르소나, 질문 충족도, 근거성, 형식, 존중 표현, 편향, 정책 준수) | `dimension` |
| 사람 판정 | 사람이 미리 매긴 pass·fail | `human_label`, `label_v1` 등 |
| 판사 판정 | 판사 모델(또는 코드 검사)이 낸 pass·fail | 표의 `판사 판정` 열 |
| 기준 답변 | 사람이 확인한 모범 답 문장 또는 기대 행동 설명 | `reference`, `expected_output` |
| 사람 선호 | 두 답 중 사람이 더 낫다고 본 쪽 | `human_winner`, `human_better` |
| 판사 성적표 | 일치율·실패 탐지율·정상 통과율·kappa | `summarize_judge_results()` |

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
