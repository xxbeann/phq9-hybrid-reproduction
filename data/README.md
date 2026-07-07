# 데이터 출처 및 라이선스

`processed/` 에는 재현 편의를 위해 **NHANES·Zenodo** 정제 CSV만 포함한다(둘 다 재배포 허용).
**KNHANES 마이크로데이터는 이용약관상 재배포할 수 없어 포함하지 않는다**(아래 참고).

## NHANES DPQ (주 데이터셋)

- **제공**: 미국 CDC / National Center for Health Statistics (NCHS)
- **내용**: Depression Screener = PHQ-9 문항별 응답. 변수 `DPQ010`~`DPQ090` = 9개 증상 문항.
- **코딩**: `0=전혀 아님, 1=며칠, 2=절반 이상, 3=거의 매일` / `7=거부, 9=모름`(→ 결측)
- **라이선스**: 미 연방 **퍼블릭 도메인** — 자유 사용(재식별 시도 금지)
- **다운로드**: `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/<year>/DataFiles/<file>.xpt`
  (사이클 J·P·L·H 병합 → 2013–2023). `src/download_nhanes.py` 참조.
- **인용**: CDC/NCHS. *National Health and Nutrition Examination Survey Data.* Hyattsville, MD: US DHHS/CDC.

## Zenodo 10423537 (교차검증)

- **URL/DOI**: https://zenodo.org/records/10423537 · 10.5281/zenodo.10423537
- **내용**: 중국 대학생 N=24,292, `question1..question9`(각 0~3) + 총점 + 문항별 응답시간
- **라이선스**: **CC-BY-4.0** (출처 표기 시 재배포 허용)
- **인용**: Su Z., et al. "Temporal dynamics in psychological assessments: a novel dataset with
  scales and response times." *Scientific Data* 11 (2024). DOI: 10.1038/s41597-024-03888-8.

## KNHANES (한국 성인) — 이 저장소에 미포함

- **제공**: 질병관리청(KDCA), 국민건강영양조사
- **URL**: https://knhanes.kdca.go.kr (원시자료)
- **PHQ-9 포함 연도**: 2014·2016·2018·2020 (성인 ≥19)
- **접근**: 회원가입 + **이용서약 필요**. 서약상 원시자료의 제3자 제공·공개가 제한되므로,
  본 저장소는 KNHANES에서 파생한 개인 단위 CSV(`knhanes_phq9.csv`)를 **배포하지 않는다.**
- **재현 방법**: KDCA에서 해당 연도 원시자료(SAS `.sas7bdat`)를 직접 내려받아 `data/raw/` 에 두고
  `rye run python src/prep_knhanes.py` 를 실행하면 동일한 `processed/knhanes_phq9.csv` 가 생성된다.
- 논문 및 `results/` 의 KNHANES **집계 통계**(3집단 평균·κ 등)는 마이크로데이터가 아니므로 포함한다.

---
※ `raw/`(대용량 원본)와 `processed/knhanes_phq9.csv`(KNHANES 마이크로데이터)는 `.gitignore` 로 추적 제외한다.
