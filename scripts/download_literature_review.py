#!/usr/bin/env python3
"""Download all papers cited in the EVRYN Phase 1 Literature Review into /home/tk/Downloads/literature review/"""
import os
import shutil
import urllib.request
import time

TARGET_DIR = "/home/tk/Downloads/literature review"
BENCHMARK_DIR = os.path.join(TARGET_DIR, "benchmark_papers")
BENCHMARK_SRC = "/home/tk/projects/evryn/data/real_papers/pdf"

os.makedirs(TARGET_DIR, exist_ok=True)
os.makedirs(BENCHMARK_DIR, exist_ok=True)

PAPERS = [
    {
        "filename": "Beltagy_2019_SciBERT.pdf",
        "title": "SciBERT: A Pretrained Language Model for Scientific Text (Beltagy et al., 2019)",
        "url": "https://arxiv.org/pdf/1903.10676.pdf",
    },
    {
        "filename": "Luan_2018_SciERC.pdf",
        "title": "Multi-Task Identification of Entities, Relations, and Coreference on Scientific Articles (Luan et al., 2018)",
        "url": "https://aclanthology.org/D18-1360.pdf",
    },
    {
        "filename": "Yao_2019_DocRED.pdf",
        "title": "DocRED: A Large-Scale Document-Level Relation Extraction Dataset (Yao et al., 2019)",
        "url": "https://aclanthology.org/P19-1074.pdf",
    },
    {
        "filename": "Xiao_2024_DualChannel_DocRE.pdf",
        "title": "Dual-Channel Reasoning Network for Document-Level Relation Extraction (Xiao et al., 2024)",
        "url": "https://aclanthology.org/2024.findings-acl.245.pdf",
    },
    {
        "filename": "Hope_2022_Mechanism_Causal_Relations.pdf",
        "title": "Extracting Mechanism-Based Causal Relations from Scientific Literature (Hope et al., 2022)",
        "url": "https://aclanthology.org/2022.acl-long.470.pdf",
    },
    {
        "filename": "Mihaila_2013_BioCause.pdf",
        "title": "BioCause: Annotating and extracting causal relations from biomedical scientific text (Mihaila et al., 2013)",
        "url": "https://link.springer.com/content/pdf/10.1186/1471-2105-14-2.pdf",
    },
    {
        "filename": "Seng_2025_Causality_in_Flux.pdf",
        "title": "Causality in Flux: Continual Adaptation of Causal Knowledge via Evidence Matching (Seng et5 al., 2025)",
        "url": "https://arxiv.org/pdf/2306.14774.pdf",
    },
    {
        "filename": "Peters_2017_Elements_of_Causal_Inference.pdf",
        "title": "Elements of Causal Inference: Foundations and Learning Algorithms (Peters, Janzing, Scholkopf, 2017)",
        "url": "https://raw.githubusercontent.com/binny1446/Causality/main/Elements%20of%20Causal%20Inference.pdf",
    },
    {
        "filename": "Pearl_2009_Causal_Inference_Overview.pdf",
        "title": "Causal Inference in Statistics: An Overview (Pearl, 2009)",
        "url": "https://ftp.cs.ucla.edu/pub/stat_ser/r350.pdf",
    },
    {
        "filename": "Pearl_2010_Foundations_of_Causal_Inference.pdf",
        "title": "The Foundations of Causal Inference (Pearl, 2010)",
        "url": "https://ftp.cs.ucla.edu/pub/stat_ser/r355.pdf",
    },
    {
        "filename": "Zheng_2018_NOTEARS.pdf",
        "title": "DAGs with NO TEARS: Continuous Optimization for Structure Learning (Zheng et al., 2018)",
        "url": "https://arxiv.org/pdf/1803.01422.pdf",
    },
    {
        "filename": "Gretton_2005_HSIC.pdf",
        "title": "Kernel methods for measuring independence and their applications with HSIC (Gretton et al., 2005)",
        "url": "https://www.jmlr.org/papers/volume6/gretton05a/gretton05a.pdf",
    },
    {
        "filename": "Tank_2021_Neural_Granger_Causality.pdf",
        "title": "Neural Granger Causality (Tank et al., 2021)",
        "url": "https://arxiv.org/pdf/1802.05842.pdf",
    },
    {
        "filename": "Zenke_2017_Synaptic_Intelligence.pdf",
        "title": "Continual Learning Through Synaptic Intelligence (Zenke et al., 2017)",
        "url": "https://arxiv.org/pdf/1703.04200.pdf",
    },
    {
        "filename": "Guo_2017_Calibration.pdf",
        "title": "On Calibration of Modern Neural Networks (Guo et al., 2017)",
        "url": "https://arxiv.org/pdf/1706.04599.pdf",
    },
    {
        "filename": "Williams_2010_PID.pdf",
        "title": "Nonnegative Decomposition of Multivariate Information (Williams & Beer, 2010)",
        "url": "https://arxiv.org/pdf/1004.2515.pdf",
    },
]

print("=== Starting Literature Review Paper Downloads ===")
results = []
for paper in PAPERS:
    dest = os.path.join(TARGET_DIR, paper["filename"])
    print(f"Downloading: {paper['filename']} ...")
    req = urllib.request.Request(paper["url"], headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/pdf,text/html,*/*"
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
            data = resp.read()
            f.write(data)
        size_kb = len(data) / 1024
        is_pdf = data.startswith(b"%PDF")
        print(f"  ✓ Saved {paper['filename']} ({size_kb:.1f} KB, valid PDF: {is_pdf})")
        results.append((paper["filename"], True, f"{size_kb:.1f} KB", is_pdf))
    except Exception as e:
        print(f"  ✗ Failed to download {paper['filename']}: {e}")
        results.append((paper["filename"], False, str(e), False))
    time.sleep(1)

print("\n=== Copying 20 Benchmark Literature Review Papers ===")
bench_files = [f for f in os.listdir(BENCHMARK_SRC) if f.endswith(".pdf")]
for bf in sorted(bench_files):
    src_file = os.path.join(BENCHMARK_SRC, bf)
    dest_file = os.path.join(BENCHMARK_DIR, bf)
    shutil.copy2(src_file, dest_file)
    with open(dest_file, "rb") as f:
        head = f.read(10)
    print(f"  ✓ Copied {bf} ({os.path.getsize(dest_file)/1024:.1f} KB, magic: {head[:5]})")

print("\n=== Summary ===")
for name, ok, info, is_pdf in results:
    status = "OK" if ok and is_pdf else "WARN/FAIL"
    print(f"[{status}] {name}: {info}")
print(f"Total benchmark papers copied: {len(bench_files)}")
