# 冻结输入登记表 v1（FROZEN_INPUT_MAP_v1）

问题：这份文档的字节一改，哪条已记录的背书就再也验不过？（GOVERNANCE_ARTIFACT，不跑实验、不改判定）
推导器源码 SHA-256：`4a8ba7213e2e9e43`；扫描仓库文件 363 份、仓库外守门件 125 份；配对 300 行，出处文档 74 份，被钉对象 118 个。
配对口径：**按键名配对且要求唯一候选**（先量过：按「第一个同级的路径」配对会把 27 行判成陈旧，全是把文档哈希配到门控路径上——伪造的硬伤）。

| 可见性状态 | 条数 |
|---|---|
| `json_key_reproduced` | 25 |
| `source_call_visible` | 40 |

冻结行的可见性按读法分开记录，三态以上各自一条通路；不可见与未读都属于披露，不是硬伤（R2）。

| 判定 | 条数 |
|---|---|
| `stale_attestation` | 0 |
| `named_object_absent` | 1 |
| `pin_of_this_layer_output` | 0 |
| `frozen_by_round_instrument` | 65 |
| `renewable_governance_pin` | 107 |
| `hash_without_named_object` | 113 |
| `ambiguous_pairing` | 14 |
| **硬伤合计** | **1** |

被轮次仪器或其预注册钉住的对象（追加不可用，R6）：

- `_m2a_ft/L03_R13-N15.raw.txt`
- `experiments/PHASE23_PREREGISTRATION.md`
- `experiments/PHASE24_PREREGISTRATION.md`
- `experiments/PHASE25_PREREGISTRATION.md`
- `experiments/PHASE26_PREREGISTRATION.md`
- `experiments/PHASE27_PREREGISTRATION.md`
- `experiments/PHASE28_PREREGISTRATION.md`
- `experiments/PHASE29_PREREGISTRATION.md`
- `experiments/PHASE30_PREREGISTRATION.md`
- `experiments/PHASE31_PREREGISTRATION.md`
- `experiments/p14_gate.py`
- `experiments/p15_gate.py`
- `experiments/p16_gate.py`
- `experiments/p17_gate.py`
- `experiments/p18_gate.py`
- `experiments/p19_gate.py`
- `experiments/p20_gate.py`
- `experiments/p21_gate.py`
- `experiments/p22_gate.py`
- `experiments/p23_gate.py`
- `experiments/p23_mechanisms.py`
- `experiments/p24_gate.py`
- `experiments/p24_mechanisms.py`
- `experiments/phase28_results.json`
- `experiments/phase29_results.json`
- `experiments/phase6_results.json`
- `experiments/run_phase23.py`
- `experiments/run_phase24.py`
- `literature/L01_CODING_PROTOCOL.md`
- `literature/L01_candidates.json`
- `literature/L01_channels.json`
- `literature/L01_coding.json`
- `literature/L01_fulltexts.json`
- `literature/L01_verification.json`
- `literature/L02_PREREGISTRATION.md`
- `literature/L02_REPRESENTATION_ADDENDUM.md`
- `literature/L02_coding.json`
- `literature/L03_PREREGISTRATION.md`
- `literature/L04_PREREGISTRATION.md`
- `literature/L05_PREREGISTRATION.md`
- `literature/ROUND_L01_RESULTS.md`
- `literature/l03_coding.py`
- `literature/registry.json`
- `literature/synthesis_v2.json`

档位可达性探针（合成行送入真正的 `classify()`，读它返回的判定；在内存的行副本上做，不落盘）：可达硬档 `named_object_absent,pin_of_this_layer_output,stale_attestation`；披露档 `ambiguous_pairing,hash_without_named_object`；对照行保持非硬 `True`；活硬伤计数 `{"stale_attestation": 0, "named_object_absent": 1, "pin_of_this_layer_output": 0}`。

硬伤逐条：

- `literature/L05_SECOND_CODER.json` ｜ 键 `sha256` ｜ 对象 `-` ｜ named_object_absent

看不见什么：只认单行的 `sha256((X / "路径").read_bytes())` 形态——从变量或 glob 取到文件再哈希的仪器，本表看不见，因此「谁钉了这份字节」的答案只会**偏少**，不会凭空多出（与 §49 的轮次级不对称同向：
宽松只能删发现，绝不铸造发现）。仓库外的对象（草稿、页面缓存、守门件）按字节所在侧判定命名空间，不靠字段名猜。本表两个输出不参与任何一侧的配对（X-85(a)）。

