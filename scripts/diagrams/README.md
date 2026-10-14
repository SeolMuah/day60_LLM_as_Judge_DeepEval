# 도식 원본(HTML → PNG)

`images/`의 도식 6장(04·05·06·12·17·18)은 이 폴더의 HTML로 그려 3200x1800 PNG로 렌더링했습니다. 13·14·15·16·02·00_lesson01_scope와 같은 톤(흰 배경, 가운데 제목·부제, 옅은 색 카드)입니다.

다시 렌더링하는 방법:

1. 한글 폰트 Pretendard를 `fonts/`에 둡니다: `npm pack pretendard@1.3.9` 후 `package/dist/public/static/Pretendard-{Regular,Medium,SemiBold,Bold,ExtraBold}.otf`를 복사합니다.
2. Playwright(Chromium)가 있는 파이썬 환경에서 실행합니다.

```bash
python render.py src/12_testcase_fields.html ../../images/12_testcase_fields.png
```

`render.py`는 글자 넘침과 빈 공간(아래·옆 여백 6% 초과, 내용 사이 10% 이상 빈 띠)을 검사해 경고를 출력합니다.
