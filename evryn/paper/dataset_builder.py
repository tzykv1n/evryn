# evryn benchmark --suite multi-page
# pytest tests/test_paper_pipeline.py

import os
import json
from typing import Dict, Any, List
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib import colors


PAPERS_SPEC: List[Dict[str, Any]] = [
    {
        "id": "paper_01_egfr_mapk",
        "title": "Epidermal Growth Factor Receptor Activation of the MAPK Pathway in Carcinoma Progression",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "The epidermal growth factor receptor (EGFR) plays a central regulatory role in cellular proliferation and oncogenic transformation. Binding of extracellular epidermal growth factor activates EGFR through receptor dimerization. We investigate the sequential downstream signal transduction across cellular compartments.",
            },
            {
                "section": "Methods & Early Signaling",
                "text": "Phosphorylated EGFR recruits the adaptor protein GRB2 via its SH2 domain. Subsequently, GRB2 binds the guanine nucleotide exchange factor SOS1 to form a stable binary signaling complex at the cell membrane.",
            },
            {
                "section": "Intermediate Cascade",
                "text": "Membrane-anchored SOS1 stimulates RAS by catalyzing GDP-GTP exchange. Active GTP-bound RAS directly binds and activates RAF serine/threonine kinase, initiating the cytoplasmic kinase cascade.",
            },
            {
                "section": "Results & Kinase Phosphorylation",
                "text": "In our experimental assays, active RAF phosphorylates MEK at dual serine residues Ser217 and Ser221. Activated MEK directly phosphorylates ERK to elicit full enzymatic activation of MAPK.",
            },
            {
                "section": "Discussion & Conclusions",
                "text": "Our findings demonstrate that active ERK translocates into the nucleus to stimulate transcription factors. Consequently, EGFR signaling drives cellular proliferation through sequential MAPK activation. Inhibition of MEK failed to alter EGFR phosphorylation but completely blocked ERK activation.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["EGFR", "GRB2", "SOS1", "RAS", "RAF", "MEK", "ERK", "MAPK"],
            "direct_edges": [
                ["EGFR", "GRB2"],
                ["GRB2", "SOS1"],
                ["SOS1", "RAS"],
                ["RAS", "RAF"],
                ["RAF", "MEK"],
                ["MEK", "ERK"],
            ],
            "cross_page_edges": [
                ["EGFR", "SOS1"],
                ["GRB2", "RAS"],
                ["SOS1", "RAF"],
                ["RAS", "MEK"],
                ["RAF", "ERK"],
                ["EGFR", "ERK"],
            ],
        },
    },
    {
        "id": "paper_02_il6_stat3_socs3",
        "title": "Interleukin-6 Triggers STAT3 Phosphorylation and Negative Feedback Regulation by SOCS3",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract",
                "text": "Interleukin-6 (IL-6) is a pleiotropic cytokine regulating inflammatory responses and hematopoiesis. Excessive IL-6 signaling contributes to autoimmune pathology.",
            },
            {
                "section": "Introduction",
                "text": "Binding of IL-6 to its receptor complex induces gp130 dimerization. This receptor engagement rapidly activates JAK2 tyrosine kinase at the inner membrane leaflet.",
            },
            {
                "section": "Methods",
                "text": "Activated JAK2 directly phosphorylates STAT3 at Tyr705. Phosphorylated STAT3 undergoes homodimerization and translocates into the nucleus.",
            },
            {
                "section": "Results",
                "text": "Quantitative RT-PCR and immunoblotting revealed that activated STAT3 strongly upregulates SOCS3 gene expression within 60 minutes of stimulation.",
            },
            {
                "section": "Discussion",
                "text": "Elevated SOCS3 protein binds JAK2 to downregulate kinase activity, establishing a negative feedback loop. Thus, IL-6 triggers SOCS3 expression through STAT3 phosphorylation.",
            },
            {
                "section": "Conclusion",
                "text": "Our study confirms that SOCS3 prevents excessive inflammation by attenuating continuous STAT3 signaling. Unstimulated controls did not induce SOCS3 expression.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["IL-6", "JAK2", "STAT3", "SOCS3"],
            "direct_edges": [
                ["IL-6", "JAK2"],
                ["JAK2", "STAT3"],
                ["STAT3", "SOCS3"],
                ["SOCS3", "JAK2"],
            ],
            "cross_page_edges": [
                ["IL-6", "STAT3"],
                ["JAK2", "SOCS3"],
                ["IL-6", "SOCS3"],
            ],
        },
    },
    {
        "id": "paper_03_hypoxia_hif1a_vegf",
        "title": "Hypoxia-Inducible Factor 1-Alpha Orchestrates VEGF-Mediated Angiogenesis in Ischemic Tissue",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "Tissue ischemia induces oxygen deprivation, triggering compensatory vascular remodeling. Hypoxia inhibits prolyl hydroxylase domain enzymes, preventing the degradation of key transcription factors.",
            },
            {
                "section": "Mechanisms",
                "text": "Inhibition of prolyl hydroxylases by low oxygen stabilizes HIF-1alpha by blocking its binding to von Hippel-Lindau protein.",
            },
            {
                "section": "Results: Gene Expression",
                "text": "Stabilized HIF-1alpha translocates to the nucleus and upregulates VEGF expression by binding the hypoxia response element.",
            },
            {
                "section": "Results: Endothelial Response",
                "text": "Secreted VEGF binds VEGF receptor 2 on endothelial cells, activating downstream signaling to stimulate angiogenesis and tube formation.",
            },
            {
                "section": "Discussion",
                "text": "Consequently, hypoxia promotes angiogenesis via sequential stabilization of HIF-1alpha and upregulation of VEGF. Normoxic conditions failed to stimulate VEGF expression.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["Hypoxia", "HIF-1alpha", "VEGF", "Angiogenesis"],
            "direct_edges": [
                ["Hypoxia", "HIF-1alpha"],
                ["HIF-1alpha", "VEGF"],
                ["VEGF", "Angiogenesis"],
            ],
            "cross_page_edges": [
                ["Hypoxia", "VEGF"],
                ["HIF-1alpha", "Angiogenesis"],
                ["Hypoxia", "Angiogenesis"],
            ],
        },
    },
    {
        "id": "paper_04_p53_dna_damage",
        "title": "ATM Kinase Activation by DNA Double-Strand Breaks Induces p53 Phosphorylation and p21-Mediated Arrest",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract",
                "text": "Genomic integrity is maintained by complex DNA damage response surveillance networks. Double-strand breaks rapidly activate the apical sensor kinase ATM.",
            },
            {
                "section": "Introduction",
                "text": "Activated ATM kinase directly phosphorylates p53 at Ser15, preventing MDM2-mediated ubiquitination and degradation.",
            },
            {
                "section": "Methods & Assays",
                "text": "Stabilized nuclear p53 binds canonical promoter response elements to induce p21 transcription in irradiated fibroblasts.",
            },
            {
                "section": "Results",
                "text": "Elevated p21 protein binds and inhibits cyclin-dependent kinase 2 (CDK2) complexes, preventing retinoblastoma phosphorylation.",
            },
            {
                "section": "Discussion",
                "text": "Through this axis, ATM kinase activation induces p21 expression via p53 to enforce cell cycle arrest at the G1/S checkpoint.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["ATM", "p53", "p21", "CDK2"],
            "direct_edges": [
                ["ATM", "p53"],
                ["p53", "p21"],
                ["p21", "CDK2"],
            ],
            "cross_page_edges": [
                ["ATM", "p21"],
                ["p53", "CDK2"],
                ["ATM", "CDK2"],
            ],
        },
    },
    {
        "id": "paper_05_ampk_mtor_autophagy",
        "title": "Nutrient Depletion Stimulates AMPK to Inhibit mTORC1 and Trigger Protective Autophagy",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract",
                "text": "Metabolic homeostasis requires precise coordination of energy-sensing kinases during nutritional starvation.",
            },
            {
                "section": "Introduction",
                "text": "Depletion of cellular ATP increases the AMP/ATP ratio, directly activating AMPK by liver kinase B1 phosphorylation.",
            },
            {
                "section": "Methods",
                "text": "Active AMPK phosphorylates the tuberous sclerosis complex subunit TSC2, enhancing its GTPase-activating activity toward Rheb.",
            },
            {
                "section": "Results: Kinase Inhibition",
                "text": "Inactivation of Rheb downregulates mTORC1 kinase activity, suppressing ribosomal protein S6 kinase phosphorylation.",
            },
            {
                "section": "Results: Autophagy Induction",
                "text": "Relief of mTORC1 suppression activates ULK1 kinase, which phosphorylates Beclin-1 to stimulate autophagosome formation.",
            },
            {
                "section": "Discussion",
                "text": "Together, these data establish that AMPK suppresses mTORC1 to stimulate autophagy under energy stress. Inactive mutants did not stimulate autophagosome formation.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["AMPK", "TSC2", "mTORC1", "ULK1"],
            "direct_edges": [
                ["AMPK", "TSC2"],
                ["TSC2", "mTORC1"],
                ["mTORC1", "ULK1"],
            ],
            "cross_page_edges": [
                ["AMPK", "mTORC1"],
                ["TSC2", "ULK1"],
                ["AMPK", "ULK1"],
            ],
        },
    },
    {
        "id": "paper_06_nfkb_tnf_inflammation",
        "title": "Tumor Necrosis Factor-Alpha Stimulates IKK to Drive NF-kB Nuclear Translocation",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "Tumor necrosis factor-alpha (TNF-alpha) is a master regulator of acute and chronic inflammatory responses. TNF-alpha stimulates the IKK complex through receptor adaptor proteins.",
            },
            {
                "section": "Signaling Mechanisms",
                "text": "Activated IKK phosphorylates IkB-alpha, triggering its polyubiquitination and proteasomal degradation.",
            },
            {
                "section": "Results: Transcription",
                "text": "Degradation of IkB-alpha liberates NF-kB dimers, promoting NF-kB nuclear translocation and binding to target gene promoters.",
            },
            {
                "section": "Results: Cytokines",
                "text": "Nuclear NF-kB strongly upregulates IL-6 and IL-8 expression in vascular endothelial cells.",
            },
            {
                "section": "Discussion",
                "text": "We conclude that TNF-alpha drives IL-6 production via sequential IKK activation and NF-kB translocation. Pretreatment with vehicle did not alter cytokine levels.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["TNF-alpha", "IKK", "NF-kB", "IL-6"],
            "direct_edges": [
                ["TNF-alpha", "IKK"],
                ["IKK", "NF-kB"],
                ["NF-kB", "IL-6"],
            ],
            "cross_page_edges": [
                ["TNF-alpha", "NF-kB"],
                ["IKK", "IL-6"],
                ["TNF-alpha", "IL-6"],
            ],
        },
    },
    {
        "id": "paper_07_tgfb_smad_fibrosis",
        "title": "Transforming Growth Factor-Beta Receptor Signaling Drives SMAD2/3 Phosphorylation in Tissue Fibrosis",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Background",
                "text": "Transforming growth factor beta (TGF-beta) is an essential cytokine promoting extracellular matrix accumulation and organ fibrosis.",
            },
            {
                "section": "Receptor Activation",
                "text": "TGF-beta binds the TGFBR2 kinase, which recruits and activates TGFBR1 through serine phosphorylation.",
            },
            {
                "section": "SMAD Phosphorylation",
                "text": "Activated TGFBR1 directly phosphorylates SMAD3 at its C-terminal SXS motif, promoting heterotrimer formation with SMAD4.",
            },
            {
                "section": "Results: ECM Synthesis",
                "text": "Nuclear SMAD3 complexes upregulate collagen synthesis and drive alpha-SMA gene expression in myofibroblasts.",
            },
            {
                "section": "Discussion & Conclusions",
                "text": "These findings demonstrate that TGF-beta stimulates collagen production through SMAD3 phosphorylation during progressive fibrosis.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["TGF-beta", "TGFBR1", "SMAD3", "Collagen"],
            "direct_edges": [
                ["TGF-beta", "TGFBR1"],
                ["TGFBR1", "SMAD3"],
                ["SMAD3", "Collagen"],
            ],
            "cross_page_edges": [
                ["TGF-beta", "SMAD3"],
                ["TGFBR1", "Collagen"],
                ["TGF-beta", "Collagen"],
            ],
        },
    },
    {
        "id": "paper_08_wnt_betacatenin",
        "title": "Canonical Wnt Ligand Binding Inhibits GSK3-Beta to Stabilize Beta-Catenin in Osteogenesis",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract",
                "text": "Bone morphogenetic pathways depend critically on canonical Wnt ligand stimulation for mesenchymal stem cell lineage allocation.",
            },
            {
                "section": "Introduction",
                "text": "Binding of Wnt3a to Frizzled receptors activates Dishevelled through cytoplasmic domain recruitment.",
            },
            {
                "section": "Methods & Assays",
                "text": "Dishevelled inhibits GSK3-beta by disrupting the axin destruction complex scaffolding.",
            },
            {
                "section": "Results",
                "text": "Inhibition of GSK3-beta prevents phosphorylation and degradation of beta-catenin, leading to cytoplasmic accumulation.",
            },
            {
                "section": "Discussion",
                "text": "Stabilized beta-catenin enters the nucleus and stimulates Runx2 transcription to promote osteoblast differentiation.",
            },
            {
                "section": "Conclusion",
                "text": "Thus, Wnt signaling suppresses GSK3-beta to stabilize beta-catenin during bone formation.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["Wnt3a", "Dishevelled", "GSK3-beta", "beta-catenin"],
            "direct_edges": [
                ["Wnt3a", "Dishevelled"],
                ["Dishevelled", "GSK3-beta"],
                ["GSK3-beta", "beta-catenin"],
            ],
            "cross_page_edges": [
                ["Wnt3a", "GSK3-beta"],
                ["Dishevelled", "beta-catenin"],
                ["Wnt3a", "beta-catenin"],
            ],
        },
    },
    {
        "id": "paper_09_caspase_apoptosis",
        "title": "Mitochondrial Outer Membrane Permeabilization Releases Cytochrome C to Trigger Caspase Cleavage",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "Intrinsic apoptotic signaling is triggered by irremediable cell damage. Pro-apoptotic BAX oligomerizes in the mitochondrial outer membrane to induce permeabilization.",
            },
            {
                "section": "Mitochondrial Release",
                "text": "Permeabilization by BAX triggers cytochrome c release from the intermembrane space into the cytosol.",
            },
            {
                "section": "Apoptosome Formation",
                "text": "Cytosolic cytochrome c binds APAF-1, forming the apoptosome to stimulate Caspase-9 proteolytic cleavage and activation.",
            },
            {
                "section": "Executioner Cleavage",
                "text": "Active Caspase-9 directly cleaves and activates Caspase-3, driving substrate cleavage and nuclear condensation.",
            },
            {
                "section": "Discussion",
                "text": "We show that BAX permeabilization triggers Caspase-3 activation via intermediate Caspase-9 cleavage. Non-apoptotic controls did not cleave Caspase-3.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["BAX", "Cytochrome c", "Caspase-9", "Caspase-3"],
            "direct_edges": [
                ["BAX", "Cytochrome c"],
                ["Cytochrome c", "Caspase-9"],
                ["Caspase-9", "Caspase-3"],
            ],
            "cross_page_edges": [
                ["BAX", "Caspase-9"],
                ["Cytochrome c", "Caspase-3"],
                ["BAX", "Caspase-3"],
            ],
        },
    },
    {
        "id": "paper_10_jak_stat_ifng",
        "title": "Interferon-Gamma Receptor Ligation Triggers JAK1 Activation and STAT1 Expression in Macrophages",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "Interferon-gamma (IFN-gamma) orchestrates host antimicrobial defense and macrophage polarization toward the M1 phenotype.",
            },
            {
                "section": "Receptor Signaling",
                "text": "Ligation of IFN-gamma to its receptor induces trans-phosphorylation and activates JAK1 kinase at the cell surface.",
            },
            {
                "section": "STAT1 Phosphorylation",
                "text": "Active JAK1 phosphorylates STAT1 at Tyr701, driving STAT1 homodimerization and nuclear entry.",
            },
            {
                "section": "Gene Expression",
                "text": "Nuclear STAT1 binds GAS promoter elements to upregulate IRF1 expression in activated macrophages.",
            },
            {
                "section": "Discussion",
                "text": "In conclusion, IFN-gamma drives IRF1 expression via sequential JAK1 and STAT1 activation.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["IFN-gamma", "JAK1", "STAT1", "IRF1"],
            "direct_edges": [
                ["IFN-gamma", "JAK1"],
                ["JAK1", "STAT1"],
                ["STAT1", "IRF1"],
            ],
            "cross_page_edges": [
                ["IFN-gamma", "STAT1"],
                ["JAK1", "IRF1"],
                ["IFN-gamma", "IRF1"],
            ],
        },
    },
    {
        "id": "paper_11_notch_signaling",
        "title": "Delta-Like Ligand 4 Binding Promotes Presenilin Cleavage and HES1 Expression in Arteries",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "Vascular morphogenesis requires strictly regulated cell fate decisions between tip and stalk endothelial cells.",
            },
            {
                "section": "Receptor Cleavage",
                "text": "Binding of DLL4 to Notch1 induces gamma-secretase cleavage, releasing the active Notch intracellular domain (NICD).",
            },
            {
                "section": "Nuclear Translocation",
                "text": "Liberated NICD associates with RBP-Jkappa in the nucleus to stimulate transcription of downstream repressor genes.",
            },
            {
                "section": "Results: Target Activation",
                "text": "The NICD-RBP-Jkappa complex directly upregulates HES1 expression to inhibit VEGFR2 and suppress endothelial sprouting.",
            },
            {
                "section": "Discussion",
                "text": "Our findings show that DLL4 promotes HES1 expression through NICD release to regulate arterial caliber. Vehicle control did not stimulate HES1.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["DLL4", "Notch1", "NICD", "HES1"],
            "direct_edges": [
                ["DLL4", "Notch1"],
                ["Notch1", "NICD"],
                ["NICD", "HES1"],
            ],
            "cross_page_edges": [
                ["DLL4", "NICD"],
                ["Notch1", "HES1"],
                ["DLL4", "HES1"],
            ],
        },
    },
    {
        "id": "paper_12_pi3k_akt_survival",
        "title": "Insulin-Like Growth Factor 1 Activates PI3K to Induce AKT Phosphorylation and Suppress Apoptosis",
        "authors": ["Synthetic Benchmark Generator"],
        "doi": None,
        "is_synthetic": True,
        "provenance": "Synthetic pipeline sanity test. Not real scientific literature.",
        "pmid": None,
        "pmcid": None,
        "pages": [
            {
                "section": "Abstract & Introduction",
                "text": "Survival factors protect neuronal and epithelial cells against stress-induced programmed cell death.",
            },
            {
                "section": "Early Transduction",
                "text": "Binding of IGF-1 to its receptor activates PI3K lipid kinase, generating PIP3 at the plasma membrane.",
            },
            {
                "section": "Kinase Activation",
                "text": "Membrane PIP3 recruits and activates AKT via phosphorylation at Thr308 by PDK1 and Ser473 by mTORC2.",
            },
            {
                "section": "Substrate Phosphorylation",
                "text": "Activated AKT directly phosphorylates BAD at Ser136, promoting BAD sequestration by 14-3-3 proteins.",
            },
            {
                "section": "Discussion & Conclusions",
                "text": "Sequestration of phosphorylated BAD inhibits apoptosis and promotes sustained cell survival. Thus, IGF-1 suppresses apoptosis through PI3K and AKT signaling.",
            },
        ],
        "ground_truth": {
            "canonical_entities": ["IGF-1", "PI3K", "AKT", "BAD"],
            "direct_edges": [
                ["IGF-1", "PI3K"],
                ["PI3K", "AKT"],
                ["AKT", "BAD"],
            ],
            "cross_page_edges": [
                ["IGF-1", "AKT"],
                ["PI3K", "BAD"],
                ["IGF-1", "BAD"],
            ],
        },
    },
]


def generate_benchmark_dataset(target_dir: str = "data/synthetic_sanity") -> List[str]:
    os.makedirs(target_dir, exist_ok=True)
    generated_pdf_paths: List[str] = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PaperTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
    )
    meta_style = ParagraphStyle(
        "PaperMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "PaperSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "PaperBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )

    for spec in PAPERS_SPEC:
        pdf_name = f"{spec['id']}.pdf"
        pdf_path = os.path.join(target_dir, pdf_name)
        gt_path = os.path.join(target_dir, f"{spec['id']}_ground_truth.json")

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
        )
        story = []

        story.append(Paragraph("[SYNTHETIC PIPELINE SANITY TEST — NOT REAL LITERATURE]", ParagraphStyle("SanityNotice", fontName="Helvetica-Bold", fontSize=8, textColor=colors.HexColor("#b91c1c"), spaceAfter=4)))
        story.append(Paragraph(spec["title"], title_style))
        authors_str = ", ".join(spec["authors"])
        meta_str = f"Authors: {authors_str}<br/>Provenance: Synthetic Pipeline Sanity Test (Procedural Fixture)"
        story.append(Paragraph(meta_str, meta_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceAfter=14))

        for idx, page_data in enumerate(spec["pages"]):
            if idx > 0:
                story.append(PageBreak())
            story.append(Paragraph(f"Page {idx + 1} — {page_data['section']}", section_style))
            story.append(Spacer(1, 6))
            story.append(Paragraph(page_data["text"], body_style))
            story.append(Spacer(1, 14))
            story.append(
                Paragraph(
                    f"<i>EVRYN Scientific Benchmark Corpus — Document {spec['id']} — Page {idx + 1} of {len(spec['pages'])}</i>",
                    ParagraphStyle("Footer", fontName="Helvetica", fontSize=8, textColor=colors.HexColor("#94a3b8")),
                )
            )

        doc.build(story)
        generated_pdf_paths.append(pdf_path)

        with open(gt_path, "w", encoding="utf-8") as f:
            gt_data = {**spec["ground_truth"], "is_synthetic": True, "provenance": "Synthetic pipeline sanity test. Not real scientific literature.", "paper_id": spec["id"]}
            json.dump(gt_data, f, indent=2)

    if target_dir == "data/synthetic_sanity":
        import shutil
        legacy_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "multipage_papers")
        os.makedirs(legacy_dir, exist_ok=True)
        for p in generated_pdf_paths:
            base = os.path.basename(p)
            shutil.copyfile(p, os.path.join(legacy_dir, base))
            gt_base = base.replace(".pdf", "_ground_truth.json")
            orig_gt = os.path.join(target_dir, gt_base)
            if os.path.exists(orig_gt):
                shutil.copyfile(orig_gt, os.path.join(legacy_dir, gt_base))
    return generated_pdf_paths
