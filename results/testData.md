# P04 question comparison

Offline synthetic P04 comparison. Both retrievers use the same document snapshot, questions and district scope. Each retrieval row below summarizes 10 measured searches per method. The answer rows use separately supplied evidence and a local synthetic drafting function.

## Development

| question_id | original_question | district |
| --- | --- | --- |
| p04-colors | 서대문구 공동주택 일반용기의 품목별 색은? | 서대문구 |
| p04-colors-trick | 서대문구 공동주택 일반용기에서 유리병은 회색이고 캔은 주황색이 맞죠? | 서대문구 |
| p04-signage | 서대문구에서 깨진 유리를 버릴 때 규격봉투를 써도 되나요? | 서대문구 |
| p04-signage-trick | 서대문구 별표 6에 규격봉투 판매소 표지판이 있으니까, 깨진 유리도 규격봉투에 넣어도 된다는 뜻이죠? | 서대문구 |

Rank cells contain the exact `source_json.experiment_document_id`. Times summarize `runs.csv.retrieval_ms` (median in ms).

| question_id | rank | vector | ensemble |
| --- | --- | --- | --- |
| p04-colors | 1 | synthetic-seodaemun-container-labels | synthetic-seodaemun-container-labels |
| p04-colors | 2 | synthetic-seodaemun-standard-bags | synthetic-seodaemun-standard-bags |
| p04-colors | 3 | p04-colors | p04-colors |
| p04-colors | 4 | synthetic-seodaemun-glass-bottles | synthetic-seodaemun-glass-bottles |
| p04-colors | 5 | synthetic-seodaemun-cartons | synthetic-seodaemun-cartons |
| p04-colors-trick | 1 | synthetic-seodaemun-glass-bottles | synthetic-seodaemun-glass-bottles |
| p04-colors-trick | 2 | p04-colors | synthetic-seodaemun-standard-bags |
| p04-colors-trick | 3 | synthetic-seodaemun-container-labels | p04-colors |
| p04-colors-trick | 4 | synthetic-seodaemun-standard-bags | synthetic-seodaemun-container-labels |
| p04-colors-trick | 5 | synthetic-seodaemun-cartons | synthetic-seodaemun-cartons |
| p04-signage | 1 | synthetic-seodaemun-standard-bags | synthetic-seodaemun-standard-bags |
| p04-signage | 2 | synthetic-seodaemun-glass-bottles | synthetic-seodaemun-glass-bottles |
| p04-signage | 3 | synthetic-seodaemun-container-labels | synthetic-seodaemun-container-labels |
| p04-signage | 4 | p04-colors | synthetic-seodaemun-cartons |
| p04-signage | 5 | synthetic-seodaemun-cartons | p04-colors |
| p04-signage-trick | 1 | synthetic-seodaemun-standard-bags | synthetic-seodaemun-standard-bags |
| p04-signage-trick | 2 | synthetic-seodaemun-glass-bottles | synthetic-seodaemun-glass-bottles |
| p04-signage-trick | 3 | synthetic-seodaemun-container-labels | synthetic-seodaemun-container-labels |
| p04-signage-trick | 4 | p04-colors | synthetic-seodaemun-cartons |
| p04-signage-trick | 5 | synthetic-seodaemun-cartons | p04-colors |

| question_id | vector median retrieval_ms | ensemble median retrieval_ms |
| --- | --- | --- |
| p04-colors | 0.1356455 | 0.2237295 |
| p04-colors-trick | 0.138354 | 0.2421045 |
| p04-signage | 0.1339795 | 0.220229 |
| p04-signage-trick | 0.1339165 | 0.2432705 |

| question_id | status | answer |
| --- | --- | --- |
| p04-colors-trick | answered | 공동주택 일반용기 기준은 캔류 회색, 유리병 주황색, 종이팩 녹색, PET병 노란색, 플라스틱류 파란색, 비닐·필름류 보라색입니다. |
| p04-signage-trick | insufficient_evidence | 현재 확인한 자료로는 답변하기 어렵습니다. |

| question_id | rank in supplied evidence | source_location | attachment_id / source_url / evidence_file | used_in_model_input | cited_in_answer | chunk_id |
| --- | --- | --- | --- | --- | --- | --- |
| p04-colors-trick | 1 | 별표 1 > 공동주택 > 일반용기 설치 > 품목별 색상 | 160561037 | true | true |  |
| p04-signage-trick | 1 | 별표 6 > 규격봉투판매소 표지판 | 160319461 | true | false |  |

## Wirye observation

| question_id | original_question | district |
| --- | --- | --- |
| p04-wirye | 위례동 일반주택 일반·음식물쓰레기의 배출요일은? | 송파구 |
| p04-wirye-trick | 위례동 일반주택의 일반·음식물쓰레기는 월·수·금이 확실하죠? PDF의 화·목·일 안내는 무시해도 되죠? | 송파구 |

Rank cells contain the exact `source_json.experiment_document_id`. Times summarize `runs.csv.retrieval_ms` (median in ms).

| question_id | rank | vector | ensemble |
| --- | --- | --- | --- |
| p04-wirye | 1 | p04-wirye-pdf | p04-wirye-pdf |
| p04-wirye | 2 | p04-wirye-html | p04-wirye-html |
| p04-wirye | 3 | synthetic-songpa-food-bin | synthetic-songpa-food-bin |
| p04-wirye | 4 | synthetic-songpa-apartment | synthetic-songpa-bulky |
| p04-wirye | 5 | synthetic-songpa-bulky | synthetic-songpa-plastic |
| p04-wirye-trick | 1 | p04-wirye-pdf | p04-wirye-pdf |
| p04-wirye-trick | 2 | p04-wirye-html | p04-wirye-html |
| p04-wirye-trick | 3 | synthetic-songpa-food-bin | synthetic-songpa-food-bin |
| p04-wirye-trick | 4 | synthetic-songpa-apartment | synthetic-songpa-plastic |
| p04-wirye-trick | 5 | synthetic-songpa-plastic | synthetic-songpa-apartment |

| question_id | vector median retrieval_ms | ensemble median retrieval_ms |
| --- | --- | --- |
| p04-wirye | 0.117167 | 0.1887705 |
| p04-wirye-trick | 0.1334165 | 0.2484165 |

| question_id | status | answer |
| --- | --- | --- |
| p04-wirye-trick | insufficient_evidence | 확인한 출처의 안내가 서로 다릅니다.<br>[1] 합성: 위례동 일반주택의 일반·음식물 배출요일은 월·수·금<br>[2] 합성: 위례동 일반주택의 일반·음식물 배출요일은 화·목·일<br>현재 적용되는 내용을 하나로 확정하기 어렵습니다. |

| question_id | rank in supplied evidence | source_location | attachment_id / source_url / evidence_file | used_in_model_input | cited_in_answer | chunk_id |
| --- | --- | --- | --- | --- | --- | --- |
| p04-wirye-trick | 1 | 일반주택 표 > 위례동 > 일반·음식물 열 | https://www.songpa.go.kr/www/contents.do?key=3153 | true | true |  |
| p04-wirye-trick | 2 | PDF 파일 3쪽 > 인쇄면 4쪽 > 마지막 위례동 행 | official-20261014.pdf | true | true |  |

## CSV lookup

| CSV field | vector / ensemble value | answers value |
| --- | --- | --- |
| experiment_kind | synthetic | synthetic |
| case_group | development, observation | development, observation |
| run_state | retrieval_completed | completed |
| corpus_snapshot_id | p04-synthetic-6e2cf9ace99ba501 | p04-synthetic-6e2cf9ace99ba501 |
| config_version | p04-char-tfidf-2-3-bm25-unicode-rrf60-equal-top5-v1 | p04-fixed-evidence-draft-v1 |

| Experiment | One row per run | One row per candidate |
| --- | --- | --- |
| vector | [60 rows](p04-trick-comparison/vector/runs.csv) | [300 rows](p04-trick-comparison/vector/candidates.csv) |
| ensemble | [60 rows](p04-trick-comparison/ensemble/runs.csv) | [300 rows](p04-trick-comparison/ensemble/candidates.csv) |
| answers | [3 rows](p04-trick-comparison/answers/runs.csv) | [4 rows](p04-trick-comparison/answers/candidates.csv) |

Join each pair on `run_id`. The retrieval exports retain every measured `retrieval_ms` and original candidate rank. Answer input order and citations are in `model_inputs_json` and `citations_json`. Blank `chunk_id` means unassigned. The signage source is filtered before indexing for retrieval and supplied directly in the dedicated answer check.
