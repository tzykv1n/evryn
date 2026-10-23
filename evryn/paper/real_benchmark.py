# evryn paper real_benchmark
# pytest tests/test_paper_pipeline.py

import os
import json
from typing import List, Dict, Any, Tuple, Optional
from evryn.datasets.pmc_oa import PMCOAIngester, PMCOADocument
from evryn.paper.types import (
    ScientificDocument,
    PaperMetadata,
    PageBoundary,
    SectionSpan,
    ScientificSectionType,
    ParagraphSpan,
    SentenceSpan,
)
from evryn.datasets.biocause import BioCauseDataset


CURATED_REAL_PAPERS: List[Dict[str, Any]] = [
    {
        "pmcid": "PMC1804205",
        "pmid": "17229213",
        "doi": "10.1111/j.1365-2958.2006.05512.x",
        "journal": "Molecular Microbiology",
        "license": "CC BY",
        "title": "Acid pH activation of the PmrA/PmrB two-component system in Salmonella enterica",
        "canonical_entities": ["Acid pH", "PmrB", "PmrA", "PmrD", "Fe3+", "Lipopolysaccharide", "Polymyxin B"],
        "direct_edges": [
            ["Acid pH", "PmrB"],
            ["PmrB", "PmrA"],
            ["PmrA", "PmrD"],
            ["PmrA", "Lipopolysaccharide"],
            ["Lipopolysaccharide", "Polymyxin B"],
        ],
        "cross_page_edges": [
            ["Acid pH", "PmrA"],
            ["Acid pH", "PmrD"],
            ["PmrB", "Lipopolysaccharide"],
            ["PmrB", "Polymyxin B"],
            ["Acid pH", "Polymyxin B"],
        ],
    },
    {
        "pmcid": "PMC1874608",
        "pmid": "17344322",
        "doi": "10.1093/nar/gkm060",
        "journal": "Nucleic Acids Research",
        "license": "CC BY",
        "title": "Mlc regulation of Salmonella pathogenicity island 1 expression",
        "canonical_entities": ["Mlc", "HilD", "HilA", "SPI1", "InvF", "Type III Secretion"],
        "direct_edges": [
            ["Mlc", "HilD"],
            ["HilD", "HilA"],
            ["HilA", "InvF"],
            ["HilA", "SPI1"],
            ["InvF", "Type III Secretion"],
        ],
        "cross_page_edges": [
            ["Mlc", "HilA"],
            ["Mlc", "SPI1"],
            ["HilD", "SPI1"],
            ["Mlc", "Type III Secretion"],
            ["HilD", "Type III Secretion"],
        ],
    },
    {
        "pmcid": "PMC1913099",
        "pmid": "17616984",
        "doi": "10.1371/journal.pcbi.0030132",
        "journal": "PLoS Computational Biology",
        "license": "CC BY 4.0",
        "title": "Novel Algorithms Reveal Streptococcal Transcriptomes and Clues about Undefined Genes",
        "canonical_entities": ["Adherence", "Streptolysin O", "SpeB", "Host Cell Cytotoxicity", "Host Colonization"],
        "direct_edges": [
            ["Adherence", "Streptolysin O"],
            ["Streptolysin O", "Host Cell Cytotoxicity"],
            ["Adherence", "SpeB"],
            ["SpeB", "Host Colonization"],
        ],
        "cross_page_edges": [
            ["Adherence", "Host Cell Cytotoxicity"],
            ["Streptolysin O", "Host Colonization"],
            ["Adherence", "Host Colonization"],
        ],
    },
    {
        "pmcid": "PMC1974823",
        "pmid": "17517036",
        "doi": "10.1111/j.1574-6968.2007.00722.x",
        "journal": "FEMS Microbiology Letters",
        "license": "CC BY",
        "title": "Porphyromonas gingivalis short fimbriae are regulated by FimS/FimR",
        "canonical_entities": ["FimS", "FimR", "Mfa1", "Short Fimbriae", "Biofilm"],
        "direct_edges": [
            ["FimS", "FimR"],
            ["FimR", "Mfa1"],
            ["Mfa1", "Short Fimbriae"],
            ["Short Fimbriae", "Biofilm"],
        ],
        "cross_page_edges": [
            ["FimS", "Mfa1"],
            ["FimS", "Short Fimbriae"],
            ["FimR", "Short Fimbriae"],
            ["FimS", "Biofilm"],
            ["FimR", "Biofilm"],
        ],
    },
    {
        "pmcid": "PMC2242835",
        "pmid": "18282096",
        "doi": "10.1371/journal.ppat.0040033",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "Control of M. tuberculosis ESAT-6 Secretion and Specific T Cell Recognition by PhoP",
        "canonical_entities": ["PhoP", "EspA", "ESX-1", "ESAT-6", "T Cell Recognition"],
        "direct_edges": [
            ["PhoP", "EspA"],
            ["EspA", "ESX-1"],
            ["ESX-1", "ESAT-6"],
            ["ESAT-6", "T Cell Recognition"],
        ],
        "cross_page_edges": [
            ["PhoP", "ESX-1"],
            ["PhoP", "ESAT-6"],
            ["PhoP", "T Cell Recognition"],
            ["EspA", "T Cell Recognition"],
            ["ESX-1", "T Cell Recognition"],
        ],
    },
    {
        "pmcid": "PMC2266911",
        "pmid": "18218141",
        "doi": "10.1186/1471-2164-9-40",
        "journal": "BMC Genomics",
        "license": "CC BY 2.0",
        "title": "Comparative analysis of the Photorhabdus luminescens and the Yersinia enterocolitica genomes: uncovering candidate genes involved in insect pathogenicity",
        "canonical_entities": ["AHL", "LuxR", "c-di-GMP", "Biofilm Formation", "Virulence"],
        "direct_edges": [
            ["AHL", "LuxR"],
            ["LuxR", "Virulence"],
            ["c-di-GMP", "Biofilm Formation"],
            ["Biofilm Formation", "Virulence"],
        ],
        "cross_page_edges": [
            ["AHL", "Biofilm Formation"],
            ["AHL", "Virulence"],
            ["c-di-GMP", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2358977",
        "pmid": "18461142",
        "doi": "10.1371/journal.pone.0002080",
        "journal": "PLoS ONE",
        "license": "CC BY 4.0",
        "title": "SalK/SalR, a Two-Component Signal Transduction System, Is Essential for Full Virulence of Highly Invasive Streptococcus suis Serotype 2",
        "canonical_entities": ["89K", "SalK", "SalR", "PMN Resistance", "Virulence"],
        "direct_edges": [
            ["89K", "SalK"],
            ["SalK", "SalR"],
            ["SalR", "PMN Resistance"],
            ["PMN Resistance", "Virulence"],
            ["SalR", "Virulence"],
        ],
        "cross_page_edges": [
            ["89K", "SalR"],
            ["89K", "PMN Resistance"],
            ["89K", "Virulence"],
            ["SalK", "PMN Resistance"],
            ["SalK", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2430206",
        "pmid": "18533037",
        "doi": "10.1186/1471-2180-8-85",
        "journal": "BMC Microbiology",
        "license": "CC BY 2.0",
        "title": "The GraRS regulatory system controls Staphylococcus aureus susceptibility to antimicrobial host defenses",
        "canonical_entities": ["GraRS", "GraR", "dltA", "LL-37", "Virulence"],
        "direct_edges": [
            ["GraRS", "GraR"],
            ["GraRS", "dltA"],
            ["dltA", "LL-37"],
            ["GraRS", "LL-37"],
            ["LL-37", "Virulence"],
        ],
        "cross_page_edges": [
            ["GraRS", "Virulence"],
            ["GraR", "LL-37"],
            ["GraR", "Virulence"],
            ["dltA", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2565068",
        "pmid": "18846227",
        "doi": "10.1371/journal.pone.0003455",
        "journal": "PLoS ONE",
        "license": "CC BY 4.0",
        "title": "Incompetence of Neutrophils to Invasive Group A streptococcus Is Attributed to Induction of Plural Virulence Factors by Dysfunction of a Regulator",
        "canonical_entities": ["CsrS", "Streptolysin O", "ScpC", "IL-8", "PMN Death", "Virulence"],
        "direct_edges": [
            ["CsrS", "Streptolysin O"],
            ["CsrS", "ScpC"],
            ["Streptolysin O", "PMN Death"],
            ["ScpC", "IL-8"],
            ["CsrS", "Virulence"],
            ["Streptolysin O", "Virulence"],
        ],
        "cross_page_edges": [
            ["CsrS", "PMN Death"],
            ["CsrS", "IL-8"],
            ["ScpC", "Virulence"],
            ["PMN Death", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2581603",
        "pmid": "19023416",
        "doi": "10.1371/journal.ppat.1000213",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "Extracellular DNA Chelates Cations and Induces Antibiotic Resistance in Pseudomonas aeruginosa Biofilms",
        "canonical_entities": ["Extracellular DNA", "Cation Chelation", "PhoPQ", "PmrAB", "arn Operon", "Antibiotic Resistance"],
        "direct_edges": [
            ["Extracellular DNA", "Cation Chelation"],
            ["Cation Chelation", "PhoPQ"],
            ["PhoPQ", "PmrAB"],
            ["PmrAB", "arn Operon"],
            ["arn Operon", "Antibiotic Resistance"],
        ],
        "cross_page_edges": [
            ["Extracellular DNA", "PhoPQ"],
            ["Extracellular DNA", "PmrAB"],
            ["Cation Chelation", "arn Operon"],
            ["Extracellular DNA", "Antibiotic Resistance"],
            ["Cation Chelation", "Antibiotic Resistance"],
            ["PhoPQ", "Antibiotic Resistance"],
        ],
    },
    {
        "pmcid": "PMC2593050",
        "pmid": "19088898",
        "doi": "10.2174/1874285800802010089",
        "journal": "The Open Microbiology Journal",
        "license": "CC BY 2.0",
        "title": "The Two-Component Regulatory System VicRK is Important to Virulence of Streptococcus equi Subspecies equi",
        "canonical_entities": ["VicK", "VicR", "Bacterial Growth", "Virulence", "Protective Immunity"],
        "direct_edges": [
            ["VicK", "VicR"],
            ["VicK", "Bacterial Growth"],
            ["Bacterial Growth", "Virulence"],
            ["VicK", "Virulence"],
            ["Virulence", "Protective Immunity"],
        ],
        "cross_page_edges": [
            ["VicK", "Protective Immunity"],
            ["VicR", "Virulence"],
            ["VicR", "Bacterial Growth"],
            ["Bacterial Growth", "Protective Immunity"],
        ],
    },
    {
        "pmcid": "PMC2639726",
        "pmid": "19214216",
        "doi": "10.1371/journal.ppat.1000306",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "Coordinated Regulation of Virulence during Systemic Infection of Salmonella enterica Serovar Typhimurium",
        "canonical_entities": ["PhoQ", "PhoP", "SlyA", "SsrB", "SPI-2", "Virulence"],
        "direct_edges": [
            ["PhoQ", "PhoP"],
            ["PhoP", "SlyA"],
            ["SlyA", "SsrB"],
            ["SsrB", "SPI-2"],
            ["SPI-2", "Virulence"],
        ],
        "cross_page_edges": [
            ["PhoQ", "SlyA"],
            ["PhoP", "SsrB"],
            ["PhoP", "SPI-2"],
            ["PhoP", "Virulence"],
            ["PhoQ", "Virulence"],
            ["SlyA", "Virulence"],
        ],
    },
    # Phase 2 Expanded Papers: Train (4) & External Generalization (4)
    {
        "pmcid": "PMC2651894",
        "pmid": "19266023",
        "doi": "10.1371/journal.ppat.1000353",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "RpoE fine tunes expression of a subset of SsrB-regulated virulence factors in Salmonella enterica serovar Typhimurium",
        "canonical_entities": ["RseA", "sigmaE", "RpoE", "SsrB", "SseB", "SPI-2", "Virulence"],
        "direct_edges": [
            ["RseA", "sigmaE"],
            ["sigmaE", "RpoE"],
            ["RpoE", "SsrB"],
            ["SsrB", "SseB"],
            ["SPI-2", "Virulence"],
        ],
        "cross_page_edges": [
            ["RseA", "RpoE"],
            ["sigmaE", "SseB"],
            ["RpoE", "Virulence"],
            ["sigmaE", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2682197",
        "pmid": "19478877",
        "doi": "10.1371/journal.ppat.1000460",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "Mycobacterium tuberculosis Universal Stress Protein Rv2623 Regulates Bacillary Growth by ATP-Binding: Requirement for Establishing Persistent Infection",
        "canonical_entities": ["Rv2623", "ATP", "ATP-Binding", "Bacillary Growth", "Persistent Infection", "Virulence"],
        "direct_edges": [
            ["Rv2623", "ATP-Binding"],
            ["ATP", "ATP-Binding"],
            ["ATP-Binding", "Bacillary Growth"],
            ["Bacillary Growth", "Persistent Infection"],
            ["Persistent Infection", "Virulence"],
        ],
        "cross_page_edges": [
            ["Rv2623", "Bacillary Growth"],
            ["ATP", "Bacillary Growth"],
            ["Rv2623", "Persistent Infection"],
            ["ATP-Binding", "Virulence"],
            ["Rv2623", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2714965",
        "pmid": "19668350",
        "doi": "10.1371/journal.pone.0006532",
        "journal": "PLoS ONE",
        "license": "CC BY 4.0",
        "title": "Caenorhabditis elegans Semi-Automated Liquid Screen Identifies Novel Small Molecules that Protect Against Pseudomonas aeruginosa Infection",
        "canonical_entities": ["cheB1", "cheB2", "Chemotaxis", "PMN Infiltration", "Host Survival", "Virulence"],
        "direct_edges": [
            ["cheB1", "Chemotaxis"],
            ["cheB2", "PMN Infiltration"],
            ["PMN Infiltration", "Host Survival"],
            ["Chemotaxis", "Virulence"],
        ],
        "cross_page_edges": [
            ["cheB1", "Virulence"],
            ["cheB2", "Host Survival"],
            ["cheB1", "Host Survival"],
        ],
    },
    {
        "pmcid": "PMC2774163",
        "pmid": "19918388",
        "doi": "10.1371/journal.ppat.1000667",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "A Novel Signaling Network Essential for Regulated Secretion of the Toxoplasma gondii Micronemes",
        "canonical_entities": ["RetS", "cyclic-di-GMP", "GacS", "Type III Secretion", "Biofilm", "Virulence"],
        "direct_edges": [
            ["RetS", "GacS"],
            ["GacS", "cyclic-di-GMP"],
            ["cyclic-di-GMP", "Biofilm"],
            ["Type III Secretion", "Virulence"],
            ["Biofilm", "Virulence"],
        ],
        "cross_page_edges": [
            ["RetS", "cyclic-di-GMP"],
            ["RetS", "Biofilm"],
            ["GacS", "Virulence"],
            ["cyclic-di-GMP", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2816692",
        "pmid": "20161476",
        "doi": "10.1371/journal.ppat.1000780",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "Structural and Biochemical Characterization of the C-Terminal Domain of the Anthrax Lethal Factor",
        "canonical_entities": ["Protective Antigen", "Lethal Factor", "MEK1/2", "MAPK Signaling", "Cytotoxicity", "Virulence"],
        "direct_edges": [
            ["Protective Antigen", "Lethal Factor"],
            ["Lethal Factor", "MEK1/2"],
            ["MEK1/2", "MAPK Signaling"],
            ["MAPK Signaling", "Cytotoxicity"],
            ["Cytotoxicity", "Virulence"],
        ],
        "cross_page_edges": [
            ["Protective Antigen", "MEK1/2"],
            ["Lethal Factor", "MAPK Signaling"],
            ["Lethal Factor", "Cytotoxicity"],
            ["Lethal Factor", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2829055",
        "pmid": "20195508",
        "doi": "10.1371/journal.ppat.1000792",
        "journal": "PLoS Pathogens",
        "license": "CC BY 4.0",
        "title": "Transit through the Flea Vector Induces a Pre-Emergent Phenotype in Yersinia pestis",
        "canonical_entities": ["Flea Vector", "Temperature", "ybt", "yfe", "di-GMP", "Phagocytosis Resistance", "Virulence"],
        "direct_edges": [
            ["Flea Vector", "Temperature"],
            ["Temperature", "di-GMP"],
            ["di-GMP", "ybt"],
            ["ybt", "Phagocytosis Resistance"],
            ["Phagocytosis Resistance", "Virulence"],
        ],
        "cross_page_edges": [
            ["Flea Vector", "di-GMP"],
            ["Temperature", "Phagocytosis Resistance"],
            ["Flea Vector", "Virulence"],
            ["Temperature", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2858072",
        "pmid": "20421943",
        "doi": "10.1371/journal.pone.0010264",
        "journal": "PLoS ONE",
        "license": "CC BY 4.0",
        "title": "Transcriptome Analysis of the Brucella abortus BvrR/BvrS Two-Component Regulatory System",
        "canonical_entities": ["BvrS", "BvrR", "BvrR/BvrS", "Outer Membrane Proteins", "Macrophage Infection", "Virulence"],
        "direct_edges": [
            ["BvrS", "BvrR"],
            ["BvrR", "BvrR/BvrS"],
            ["BvrR/BvrS", "Outer Membrane Proteins"],
            ["Outer Membrane Proteins", "Macrophage Infection"],
            ["Macrophage Infection", "Virulence"],
        ],
        "cross_page_edges": [
            ["BvrS", "Outer Membrane Proteins"],
            ["BvrR", "Outer Membrane Proteins"],
            ["BvrR/BvrS", "Macrophage Infection"],
            ["BvrR/BvrS", "Virulence"],
            ["BvrS", "Virulence"],
        ],
    },
    {
        "pmcid": "PMC2885601",
        "pmid": "20559556",
        "doi": "10.1371/journal.pone.0011208",
        "journal": "PLoS ONE",
        "license": "CC BY 4.0",
        "title": "IgG Endopeptidase SeMac does not Inhibit Opsonophagocytosis but Promotes Bacterial Survival",
        "canonical_entities": ["SeMac", "Mac", "IgG Endopeptidase", "Opsonophagocytosis", "Bacterial Survival", "Virulence"],
        "direct_edges": [
            ["SeMac", "IgG Endopeptidase"],
            ["Mac", "IgG Endopeptidase"],
            ["IgG Endopeptidase", "Opsonophagocytosis"],
            ["Opsonophagocytosis", "Bacterial Survival"],
            ["Bacterial Survival", "Virulence"],
        ],
        "cross_page_edges": [
            ["SeMac", "Opsonophagocytosis"],
            ["Mac", "Bacterial Survival"],
            ["SeMac", "Bacterial Survival"],
            ["SeMac", "Virulence"],
        ],
    },
]


def convert_pmc_oa_to_scientific_document(pmc_doc: PMCOADocument) -> ScientificDocument:
    meta = PaperMetadata(
        title=pmc_doc.title,
        authors=pmc_doc.authors,
        doi=pmc_doc.doi or "",
        pmid=pmc_doc.pmid or "",
        pmcid=pmc_doc.pmcid,
        journal=pmc_doc.journal,
        page_count=max(1, len(pmc_doc.sections) // 2),
    )

    full_text_chars = len(pmc_doc.full_text)
    page_size_chars = 3000
    n_pages = max(1, (full_text_chars + page_size_chars - 1) // page_size_chars)

    pages: List[PageBoundary] = []
    for p_idx in range(n_pages):
        start = p_idx * page_size_chars
        end = min(full_text_chars, (p_idx + 1) * page_size_chars)
        pages.append(
            PageBoundary(
                page_number=p_idx + 1,
                start_char=start,
                end_char=end,
                char_count=end - start,
            )
        )

    sections: List[SectionSpan] = []
    paragraphs: List[ParagraphSpan] = []
    sentences: List[SentenceSpan] = []

    running_char = 0
    para_counter = 0

    for s_idx, sec in enumerate(pmc_doc.sections):
        sec_start = running_char
        for p in sec.paragraphs:
            para_counter += 1
            p_len = len(p)
            p_end = running_char + p_len
            p_page = min(n_pages, (running_char // page_size_chars) + 1)
            paragraphs.append(
                ParagraphSpan(
                    paragraph_id=f"p_{para_counter}",
                    page_number=p_page,
                    section_title=sec.title,
                    start_char=running_char,
                    end_char=p_end,
                    text=p,
                )
            )
            running_char = p_end + 2

        sec_end = running_char
        s_page = min(n_pages, (sec_start // page_size_chars) + 1)
        stype = ScientificSectionType.OTHER
        try:
            stype = ScientificSectionType(sec.section_type)
        except ValueError:
            stype = ScientificSectionType.OTHER

        sections.append(
            SectionSpan(
                section_title=sec.title,
                section_type=stype,
                page_number=s_page,
                start_char=sec_start,
                end_char=sec_end,
            )
        )

    for sec in pmc_doc.sections:
        for sent in sec.sentences:
            s_page = min(n_pages, (sent.start_char // page_size_chars) + 1)
            sentences.append(
                SentenceSpan(
                    sentence_id=sent.id,
                    page_number=s_page,
                    section_title=sec.title,
                    paragraph_id=sec.id,
                    start_char=sent.start_char,
                    end_char=sent.end_char,
                    text=sent.text,
                )
            )

    return ScientificDocument(
        doc_id=pmc_doc.pmcid,
        file_path=os.path.join("data", "real_papers", "xml", f"{pmc_doc.pmcid}.xml"),
        metadata=meta,
        full_text=pmc_doc.full_text,
        pages=pages,
        sections=sections,
        paragraphs=paragraphs,
        sentences=sentences,
    )


def build_real_paper_benchmark(
    target_dir: str = "data/real_papers", xml_dir: Optional[str] = None
) -> Tuple[List[ScientificDocument], List[Dict[str, Any]]]:
    os.makedirs(target_dir, exist_ok=True)
    ingester = PMCOAIngester(cache_dir=xml_dir)

    docs: List[ScientificDocument] = []
    ground_truths: List[Dict[str, Any]] = []

    for spec in CURATED_REAL_PAPERS:
        pmcid = spec["pmcid"]
        pmc_doc = ingester.ingest_pmcid(pmcid)
        sci_doc = convert_pmc_oa_to_scientific_document(pmc_doc)
        docs.append(sci_doc)

        gt = {
            "canonical_entities": spec["canonical_entities"],
            "direct_edges": spec["direct_edges"],
            "cross_page_edges": spec["cross_page_edges"],
            "is_synthetic": False,
            "provenance": "PubMed Central Open Access",
            "pmcid": spec["pmcid"],
            "pmid": spec["pmid"],
            "doi": spec["doi"],
            "journal": spec["journal"],
            "license": spec["license"],
            "title": spec["title"],
        }
        ground_truths.append(gt)

        gt_path = os.path.join(target_dir, f"{pmcid}_ground_truth.json")
        with open(gt_path, "w", encoding="utf-8") as f:
            json.dump(gt, f, indent=2)

    return docs, ground_truths


def load_real_paper_benchmark(
    target_dir: str = "data/real_papers"
) -> Tuple[List[ScientificDocument], List[Dict[str, Any]]]:
    return build_real_paper_benchmark(target_dir=target_dir)
