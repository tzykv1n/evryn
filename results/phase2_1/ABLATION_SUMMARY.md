# EVRYN Phase 2.1 Controlled Ablation Results

| Condition | Description | Train Direct F1 | Train Cross F1 | Dev Direct F1 | Dev Cross F1 | Locked Test Direct F1 | Locked Test Cross F1 | External Direct F1 | External Cross F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | Original pipeline with whole-sentence matching and unconstrained noise spans | 0.4640 | 0.2734 | 0.6317 | 0.5016 | 0.5640 | 0.1839 | 0.4919 | 0.2857 |
| **Ablation_A** | Clause-aware direct extraction & scoped negation | 0.4640 | 0.2019 | 0.6317 | 0.5016 | 0.5640 | 0.1625 | 0.4919 | 0.2262 |
| **Ablation_B** | Coordinated causes & effects (requires both X and Y) | 0.4585 | 0.2019 | 0.6657 | 0.5064 | 0.5695 | 0.2394 | 0.4808 | 0.3262 |
| **Ablation_C** | Entity-span canonicalization & mutant directionality | 0.4640 | 0.2019 | 0.6458 | 0.5068 | 0.5640 | 0.1625 | 0.4919 | 0.2262 |
| **Ablation_D** | False-positive suppression (verb clause & citation rejection) | 0.4585 | 0.2019 | 0.6657 | 0.5064 | 0.5695 | 0.2394 | 0.4808 | 0.3262 |
| **Ablation_E** | Cross-sentence bridge validation (discourse & anaphora) | 0.4585 | 0.2019 | 0.6657 | 0.5064 | 0.5695 | 0.2394 | 0.4808 | 0.3262 |
| **Ablation_F** | Cross-page path validation & direct edge isolation | 0.4585 | 0.2120 | 0.6657 | 0.5350 | 0.5695 | 0.2625 | 0.4808 | 0.3262 |
| **Ablation_G_Combined** | Combined Phase 2.1 Production implementation | 0.4585 | 0.2120 | 0.6657 | 0.5350 | 0.5695 | 0.2625 | 0.4808 | 0.3262 |
