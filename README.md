# LLM-as-Judge와 DeepEval: 판사 모델 설계·편향·평가 지표·테스트 케이스

이 교안은 LLM을 평가자로 활용해 여러 종류의 LLM 응답을 채점·비교하고 그 판정을 점검하는 일반적인 방법을 다룹니다. LLM-as-Judge는 평가 방법이고 DeepEval은 테스트 케이스와 지표를 실행하는 프레임워크입니다. RAGAS도 RAG 지표 외에 일반 목적 평가 지표를 제공합니다. 이번 실습은 검색기 없이 준비된 입력·근거·답변을 평가합니다. 루나 사례에서는 페르소나·말투·도움성·형식·편향·공식 정보 근거성을 다룹니다.

| 교안 | 배울 내용 | 본 실습 | 함께 따라하기 |
|---|---|---|---|
| [01 · LLM-as-Judge: 판사와 편향](교안_01_LLM_as_Judge_판사와_편향.ipynb) | 판사 모델, Direct Scoring(통과·실패, 1~5점, 정답 답변), Pairwise와 무승부, 위치·장황함·가짜 출처 편향 재기, 순서를 바꿔 두 번 묻기, 사람 라벨과 맞춰 보기(일치율·실패 탐지율·kappa), 판사 프롬프트 고치기 | 한빛바이크(수업용 가상 공공자전거) 이용 안내 챗봇 답변 | 복약 안내 챗봇 v1·v2 중 무엇을 배포할지 판사로 결정 |
| [02 · DeepEval: 지표와 테스트 케이스](교안_02_DeepEval_지표와_테스트_케이스.ipynb) | `LLMTestCase`, G-Eval과 도메인 평가 기준(정답 답변·rubric), ArenaGEval, Hallucination, Toxicity·Bias, 루나 사례, 커버리지 표 설계, `evaluate` 결과 읽기 | 같은 한빛바이크 안내 | 복약 안내 챗봇 출시 전 평가 |

교안마다 맨 아래 **함께 따라하기**가 있습니다. 본 실습과 다른 도메인(복약 안내)이며, `직접 설계`·`부분 작성` 칸을 채운 뒤 아래 실행 셀로 확인합니다. 완성 코드는 `정답/`에 있습니다. 과제는 따로 준비 중입니다.

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

| 자료 | 내용 |
|---|---|
| `data/bike_guide.json` | 한빛바이크 이용 안내 문장 6개(요금·대여 시간·대여·반납·나이 제한) |
| `data/bike_answers.json` | 질문 4개 x 답변 5종(정답·사실 오류·근거 없는 내용 추가·장황한 정답·무례한 정답)과 사람 라벨 |
| `data/bike_cases.json` | 결함을 하나씩 심은 테스트 케이스 6개 |
| `data/luna_eval_cases.json` | 버추얼 아이돌 챗봇 루나의 페르소나·도움성·형식·공식 사실 근거성·편향을 보여 주는 수업용 사례 12개와 사람 라벨 |
| `data/drug_docs.json` | 일반의약품 6종 문서(효능·용법·경고·주의·함께 먹으면 안 되는 것). 출처: 식품의약품안전처 의약품개요정보(e약은요), 공공데이터포털 |
| `data/drug_chatbot_log.json` | 복약 안내 챗봇 v1·v2의 실제 응답 10건, 문서만으로 쓴 정답 답변, 약사 검수를 가정한 수업용 라벨 |

## 준비

1. `실습자료` 폴더에서 `uv sync`로 공용 환경을 맞춥니다. 이 환경의 DeepEval은 **4.1.1**입니다.
2. 이 레포의 .env.example을 .env로 복사하고 OPENAI_API_KEY를 설정합니다. 답변·판사 모델 이름은 필요하면 조정합니다. 상위 실습자료의 .env를 사용할 수도 있습니다.
   - `OPENAI_CHAT_MODEL`: 챗봇 답변 모델(기본 `gpt-5.6-luna`)
   - `OPENAI_EVAL_MODEL`: 판사 모델(기본 `gpt-4.1`). G-Eval에 토큰 로그확률이 필요하므로, 상위 `.env`를 재사용하면 선택 모델의 지원 여부를 확인합니다.
3. 교안 02의 준비 셀은 `DEEPEVAL_TELEMETRY_OPT_OUT=1`로 DeepEval이 사용 기록을 외부로 보내지 않게 합니다. deepeval을 불러오기 전에 정해야 해서 `.env`가 아니라 코드에서 정합니다.
4. DeepEval은 실행한 폴더에 `.deepeval/` 폴더를 만들고, `evaluate` 끝에 Confident AI 안내 문구를 출력합니다. 둘 다 이 실습에는 필요 없으며 `.gitignore`에 넣어 두었습니다.

**점수 방향 주의:** DeepEval 4.1.1에서 Hallucination·Toxicity·Bias는 **낮을수록 좋은** 점수입니다. 이 설명은 uv.lock에 고정된 버전과 [4.1.1 Hallucination 구현](https://github.com/confident-ai/deepeval/blob/v4.1.1/deepeval/metrics/hallucination/hallucination.py)에 맞췄습니다. 다른 버전의 온라인 문서·코드에서는 점수 방향과 세부 동작이 달라질 수 있으므로 설치 버전을 먼저 확인합니다.

판사 모델의 판정과 점수는 실행마다 달라질 수 있습니다. 교안의 "확인할 점"은 숫자 대신 어떤 출력 줄을 무엇과 비교하는지로 적었습니다.

한빛바이크와 챗봇 응답은 수업용 가상 자료입니다. 약 정보는 공공데이터 원문이지만, 복약 판단은 평가를 연습하기 위한 예시이며 의료 조언이 아닙니다.


## RAGAS와 LLM-as-Judge·DeepEval의 관계와 실무 적용

- 공통점: RAGAS와 DeepEval은 모두 평가 지표를 실행할 수 있으며, LLM 기반 판정도 활용합니다.
- 차이와 초점: RAGAS는 RAG를 포함한 다양한 평가 지표 모음입니다. LLM-as-Judge는 판정 방법이고 DeepEval은 그 방법을 테스트 케이스와 지표에 적용하는 프레임워크입니다. 따라서 RAGAS를 RAG 전용, DeepEval을 일반 평가 전용으로 나누지 않습니다.
- 오늘의 실습: 검색기를 실행하지 않고 준비된 답변을 대상으로 일반 응답의 기준을 설계합니다. 후보 답변 비교는 Pairwise/ArenaGEval로 다룹니다.
- 실무 예: 사람 확인 사례를 기준 세트로 유지하고, 모델·프롬프트 변경 전후에 재평가합니다. 먼저 작은 묶음으로 판정 결과와 비용을 확인하고, 실패 탐지와 헛경보를 사람 라벨과 함께 살펴 기준을 보완합니다.

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
- [DeepEval 환경 변수와 telemetry opt-out](https://deepeval.com/docs/environment-variables)
