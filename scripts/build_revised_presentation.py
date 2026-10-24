#!/usr/bin/env python3
"""
Generate the revised, visual-first, minimal-text 40-slide Beamer presentation
for EVRYN Phase 1 Research Progress Review.
"""

presentation_tex = r"""\documentclass[aspectratio=43,10pt]{beamer}

\usepackage[utf8]{inputenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{booktabs,tabularx,array}
\usepackage{graphicx}
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,fit,calc}

% ==============================================================================
% ULTRA-MINIMAL BLACK-AND-WHITE ACADEMIC BEAMER THEME
% Strict square corners, zero rounded cards, zero gradients, zero shadows
% ==============================================================================
\setbeamertemplate{navigation symbols}{}
\setbeamercolor{background canvas}{bg=white}
\setbeamercolor{normal text}{fg=black}
\setbeamercolor{frametitle}{fg=black,bg=white}
\setbeamercolor{title}{fg=black}
\setbeamercolor{subtitle}{fg=black}
\setbeamercolor{author}{fg=black}
\setbeamercolor{institute}{fg=black}
\setbeamercolor{date}{fg=black}

% Square-cornered frametitle with thin black rule
\setbeamertemplate{frametitle}{
  \vspace{0.25cm}
  {\bfseries\large\insertframetitle}\par
  \vspace{0.04cm}
  {\rule{\linewidth}{0.6pt}}\par
  \vspace{0.08cm}
}

% Clean academic footline with strict Slide X / 40 counter
\setbeamertemplate{footline}{
  \leavevmode%
  \hbox{%
  \begin{beamercolorbox}[wd=.38\paperwidth,ht=2.4ex,dp=1.0ex,leftskip=2.5ex]{author in head/foot}%
    \tiny\textbf{Alvin Kuriakose} (Reg: 25020987) $\cdot$ CUSAT
  \end{beamercolorbox}%
  \begin{beamercolorbox}[wd=.38\paperwidth,ht=2.4ex,dp=1.0ex,center]{title in head/foot}%
    \tiny EVRYN: Temporal Causal Knowledge (Phase 1)
  \end{beamercolorbox}%
  \begin{beamercolorbox}[wd=.24\paperwidth,ht=2.4ex,dp=1.0ex,rightskip=2.5ex,right]{page in head/foot}%
    \tiny\textbf{Slide \insertframenumber{} / 40}
  \end{beamercolorbox}%
  }%
  \vskip0.8ex%
}

% Square outline box with thin black rule
\newenvironment{sqbox}[1][]{%
  \begin{beamercolorbox}[sep=4pt,rounded=false,shadow=false,wd=\linewidth]{block}%
  \ifx\&#1\&\else{\small\bfseries #1}\vspace{2pt}\par\fi
  \footnotesize
}{%
  \end{beamercolorbox}%
}
\setbeamercolor{block}{bg=white,fg=black}

\title{\textbf{Temporal Causal Knowledge Extraction, Transfer, and Discovery Prediction from Scientific Literature}}
\subtitle{Phase 1 Research Progress Review: Multi-Page Extraction \& Calibrated Evidence Grounding}
\author{\textbf{Alvin Kuriakose} \quad (Register Number: 25020987)}
\institute{
  Under the Guidance of: \textbf{Dr. Jeena Kleenankandy}, Assistant Professor\\
  \vspace{0.1cm}
  Department of Computer Science\\
  Cochin University of Science and Technology (CUSAT)\\
  \vspace{0.1cm}
  \footnotesize Master of Technology in Computer Science and Engineering\\
  Specialization in Data Science and Artificial Intelligence
}
\date{November 2026}

\begin{document}

% ==============================================================================
% SLIDE 1: Title and Research Identity
% ==============================================================================
\begin{frame}[plain]
  \vspace{0.3cm}
  \begin{center}
    {\large\bfseries Temporal Causal Knowledge Extraction, Transfer,\\and Discovery Prediction from Scientific Literature}\par
    \vspace{0.15cm}
    {\footnotesize\textbf{Phase 1 Research Review: Multi-Page Extraction \& Calibrated Grounding}}\par
    \vspace{0.25cm}
    \rule{0.85\linewidth}{0.8pt}\par
    \vspace{0.25cm}
    {\small\textbf{Alvin Kuriakose} \quad (Reg. No: 25020987)}\par
    {\footnotesize M.Tech (Computer Science \& Engineering -- Data Science \& AI)}\par
    \vspace{0.25cm}
    {\footnotesize Under the Guidance of:}\par
    {\small\textbf{Dr. Jeena Kleenankandy}, Assistant Professor}\par
    \vspace{0.2cm}
    {\footnotesize Department of Computer Science\\Cochin University of Science and Technology (CUSAT)}\par
    \vspace{0.25cm}
    {\scriptsize November 2026}
  \end{center}
\end{frame}

% ==============================================================================
% SLIDE 2: Research Context: Automated Science & Biomedical Literature
% ==============================================================================
\begin{frame}{Research Context: Automated Science \& Biomedical Literature}
  \textbf{Takeaway}: Exponential literature growth overwhelms manual curation, requiring automated extraction.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=1.0cm, minimum width=2.4cm, align=center, font=\footnotesize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.8pt}
    ]
      \node[box] (b1) {\textbf{1.5M+ Papers/Yr}\\PubMed Avalanche\\Unstructured PDFs};
      \node[box, right=0.8cm of b1] (b2) {\textbf{Curated Databases}\\KEGG / Reactome\\3--7 Year Lag};
      \node[box, right=0.8cm of b2] (b3) {\textbf{Automated Discovery}\\Verifiable Provenance\\Causal Reasoning};

      \draw[arr] (b1) -- node[above, font=\scriptsize] {Exceeds human} (b2);
      \draw[arr] (b2) -- node[above, font=\scriptsize] {Urgent need} (b3);
    \end{tikzpicture}
  \end{center}
  \vspace{0.3cm}
  \begin{itemize}\setlength{\itemsep}{3pt}
    \item \textbf{Curation Bottleneck}: Manual database synthesis captures $<5\%$ of published biomedical mechanisms.
    \item \textbf{High-Stakes Domain}: Biomedical discovery requires verifiable, evidence-grounded facts, not hallucinations.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 3: Motivation: Beyond Correlation to Grounded Causality
% ==============================================================================
\begin{frame}{Motivation: Beyond Correlation to Grounded Causality}
  \textbf{Takeaway}: Therapeutic intervention requires causal directionality ($X \to Y$), which correlation cannot provide.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Associational Graph: $P(Y \mid X)$]
        \centering
        \begin{tikzpicture}[
          node/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum size=0.6cm, font=\footnotesize\bfseries},
          arr/.style={-, line width=0.8pt, dashed}
        ]
          \node[node] (x) {A};
          \node[node, right=1.4cm of x] (y) {B};
          \draw[arr] (x) -- node[above, font=\scriptsize] {Correlated} (y);
        \end{tikzpicture}\par
        \vspace{0.2cm}
        \raggedright
        \textbullet{} Symmetric co-occurrence\\
        \textbullet{} Confounded by latent factors\\
        \textbullet{} Fails Pearl's $do$-calculus
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Structural Causal Graph: $P(Y \mid do(X))$]
        \centering
        \begin{tikzpicture}[
          node/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum size=0.6cm, font=\footnotesize\bfseries},
          arr/.style={-{Stealth[scale=0.8]}, line width=0.9pt}
        ]
          \node[node] (x) {A};
          \node[node, right=1.4cm of x] (y) {B};
          \draw[arr] (x) -- node[above, font=\scriptsize] {Direct Cause (+)} (y);
        \end{tikzpicture}\par
        \vspace{0.2cm}
        \raggedright
        \textbullet{} Explicit direction and polarity\\
        \textbullet{} Actionable target validation\\
        \textbullet{} Verifiable textual provenance
      \end{sqbox}
    \end{column}
  \end{columns}
\end{frame}

% ==============================================================================
% SLIDE 4: Problem Statement: Multi-Page Causal Extraction
% ==============================================================================
\begin{frame}{Problem Statement: Multi-Page Causal Extraction}
  \textbf{Takeaway}: Scientific papers articulate mechanisms across physical pages and distant sections.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      page/.style={draw=black, line width=0.7pt, fill=white, rectangle, minimum height=1.6cm, minimum width=2.4cm, align=center, font=\scriptsize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.8pt}
    ]
      \node[page] (p1) {\textbf{Page 1: INTRO}\\PmrB sensor kinase\\activated by acid pH};
      \node[page, right=0.9cm of p1] (p2) {\textbf{Page 4: RESULTS}\\PmrB phosphorylates\\regulator PmrA};
      \node[page, right=0.9cm of p2] (p3) {\textbf{Page 7: DISC}\\PmrA activates arn\\conferring resistance};

      \draw[arr] (p1) -- node[above, font=\tiny\bfseries] {$\Delta_{\text{page}}=3$} (p2);
      \draw[arr] (p2) -- node[above, font=\tiny\bfseries] {$\Delta_{\text{page}}=3$} (p3);
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{3pt}
    \item \textbf{Physical Dispersion}: Sentence-local extractors miss 100\% of cross-page mechanisms ($F_1^{\text{cross}} = 0.000$).
    \item \textbf{Semantic Drift}: Unconstrained cross-page search produces combinatorial false positive jumps across hub entities.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 5: Research Gap: Limitations of Existing Approaches
% ==============================================================================
\begin{frame}{Research Gap: Limitations of Existing Approaches}
  \textbf{Takeaway}: Neither local NLP tools nor frontier LLMs resolve evidence-grounded multi-page causality.
  \vspace{0.3cm}
  \begin{center}
    \footnotesize
    \renewcommand{\arraystretch}{1.2}
    \begin{tabular}{p{2.6cm}p{3.2cm}p{2.8cm}}
      \toprule
      \textbf{Approach} & \textbf{Core Failure Mode} & \textbf{Observed Metric} \\
      \midrule
      \textbf{Sentence NLP} & Blind to cross-page discourse & $F_1^{\text{cross}} = 0.0000$ \\
      \textbf{Statistical NPMI} & Global co-occurrence; zero grounding & Grounding: 0.0\% \\
      \textbf{Dense Embeddings} & Semantic drift; no causal polarity & Grounding: 14.3\% \\
      \textbf{Frontier LLMs} & Hallucinates ungrounded causal links & ReCITE $F_1 = 0.535 \pm 0.20$ \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{The Core Need}: An architecture that performs bounded multi-page extraction with 100\% provenance traceability.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 6: Research Objectives of Phase 1
% ==============================================================================
\begin{frame}{Research Objectives of Phase 1}
  \textbf{Takeaway}: Four formal engineering and research objectives established for Phase 1.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.85cm, minimum width=3.8cm, align=left, font=\scriptsize},
      node distance=0.22cm
    ]
      \node[box] (o1) {\textbf{O1: Ingestion \& Provenance}\\100\% character offset tracing};
      \node[box, below=of o1] (o2) {\textbf{O2: Multi-Page Extraction}\\Direct and cross-page dependencies};
      \node[box, right=0.4cm of o1] (o3) {\textbf{O3: Hub Control \& Invariants}\\Prune false transitive jumps};
      \node[box, below=of o3] (o4) {\textbf{O4: Strict Benchmark Auditing}\\20 papers across 4 isolated splits};
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Target}: Satisfy formal acceptance criteria with zero data leakage.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 7: Research Questions Addressed in Phase 1
% ==============================================================================
\begin{frame}{Research Questions Addressed in Phase 1}
  \textbf{Takeaway}: Investigating three foundational research questions in empirical literature extraction.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.85cm, minimum width=8.0cm, align=left, font=\scriptsize},
      node distance=0.25cm
    ]
      \node[box] (q1) {\textbf{RQ1 (Grounding)}: Can deterministic syntactic parsing guarantee 100\% evidence traceability without hallucinated links?};
      \node[box, below=of q1] (q2) {\textbf{RQ2 (Transitivity)}: How can transitive causal inference cross pages without triggering combinatorial false positive explosions?};
      \node[box, below=of q2] (q3) {\textbf{RQ3 (Generalization)}: Does a bounded document-context model generalize to unseen biomedical literature splits?};
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item All questions addressed through controlled experiments on 20 authentic PMC papers.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 8: Scope and Contributions of Phase 1
% ==============================================================================
\begin{frame}{Scope and Contributions of Phase 1}
  \textbf{Takeaway}: Phase 1 delivers a verified modular pipeline, benchmark suite, and reliability engine.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Methodological Contributions]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item Bounded 2-hop cross-page transitive search with distance-based confidence decay.
          \item Biological direction invariants (Terminal Phenotype \& Environmental Input).
          \item Document-context relation resolver for demonstrative anaphora and split stitching.
        \end{itemize}
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Engineering Artifacts]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item 20-paper multi-split authentic PMC benchmark (V1 \& V2 ground truth).
          \item 19-test automated reliability engine (\texttt{test\_paper\_reliability.py}).
          \item 100\% reproducible evaluation suite with bootstrap confidence intervals.
        \end{itemize}
      \end{sqbox}
    \end{column}
  \end{columns}
\end{frame}

% ==============================================================================
% SLIDE 9: Conceptual Foundations: Structural Causal Models (SCMs)
% ==============================================================================
\begin{frame}{Conceptual Foundations: Structural Causal Models (SCMs)}
  \textbf{Takeaway}: Pearl's 4-tuple formalizes the mathematical target of scientific literature extraction.
  \vspace{0.2cm}
  $$\mathcal{M} = \langle \mathbf{X}, \mathbf{U}, \mathbf{F}, P(\mathbf{U}) \rangle$$
  \vspace{0.15cm}
  \begin{center}
    \begin{tikzpicture}[
      node/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum size=0.65cm, font=\footnotesize\bfseries},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.8pt}
    ]
      \node[node] (u1) {$U_1$};
      \node[node, below=0.5cm of u1] (x1) {$X_1$};
      \node[node, right=1.6cm of x1] (x2) {$X_2$};
      \node[node, above=0.5cm of x2] (u2) {$U_2$};
      \node[node, right=1.6cm of x2] (x3) {$X_3$};
      \node[node, above=0.5cm of x3] (u3) {$U_3$};

      \draw[arr, dashed] (u1) -- (x1);
      \draw[arr] (x1) -- node[above, font=\scriptsize] {$f_2(X_1, U_2)$} (x2);
      \draw[arr, dashed] (u2) -- (x2);
      \draw[arr] (x2) -- node[above, font=\scriptsize] {$f_3(X_2, U_3)$} (x3);
      \draw[arr, dashed] (u3) -- (x3);
    \end{tikzpicture}
  \end{center}
  \vspace{0.15cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Endogenous Variables} ($\mathbf{X}$): Biological entities, proteins, phenotypes.
    \item \textbf{Intervention}: $P_{\mathcal{M}; do(X_k = x')}(\mathbf{X} \setminus \{X_k\}) = \prod_{i \ne k} P(X_i \mid \mathbf{PA}_i)$.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 10: Definitions and Causal Terminology
% ==============================================================================
\begin{frame}{Definitions and Causal Terminology}
  \textbf{Takeaway}: Extracted scientific claims are mapped into an immutable 8-tuple assertion contract.
  \vspace{0.1cm}
  $$\tau = \langle e_{\text{cause}}, e_{\text{effect}}, \pi, \sigma, \kappa, \omega, \Delta, \mathcal{P} \rangle$$
  \vspace{0.1cm}
  \begin{center}
    \footnotesize
    \setlength{\tabcolsep}{3pt}
    \renewcommand{\arraystretch}{1.08}
    \begin{tabular}{lp{6.2cm}}
      \toprule
      \textbf{Field} & \textbf{Definition and Scope} \\
      \midrule
      $e_{\text{cause}}, e_{\text{effect}}$ & Canonicalized entity strings resolved to standard nomenclature \\
      $\pi \in \{\to, \dashv\}$ & Polarity direction: UPREGULATES ($+$) vs DOWNREGULATES ($-$) \\
      $\sigma \in \{\text{DIR}, \text{CTX}, \text{TRANS}\}$ & Typology: Direct sentence, Context-resolved, or Multi-hop \\
      $\kappa \in [0, 1]$ & Calibrated model confidence score \\
      $\omega \in \{0, 1\}$ & Syntactic negation status ($\omega=1$ indicates explicit negation) \\
      $\Delta \in \mathbb{N}_{\ge 0}$ & Inter-mention page separation: $|p(e_{\text{cause}}) - p(e_{\text{effect}})|$ \\
      $\mathcal{P}$ & Complete provenance record (PMCID, page, section, offsets, quote) \\
      \bottomrule
    \end{tabular}
  \end{center}
\end{frame}

% ==============================================================================
% SLIDE 11: System Overview: End-to-End Pipeline
% ==============================================================================
\begin{frame}{System Overview: End-to-End Pipeline}
  \textbf{Takeaway}: Five modular stages decouple ingestion, parsing, extraction, and verification.
  \vspace{0.35cm}
  \begin{center}
    \begin{tikzpicture}[
      node distance=0.4cm and 0.35cm,
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.75cm, minimum width=1.65cm, align=center, font=\tiny\bfseries},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.7pt}
    ]
      \node[box] (n1) {1. Ingestion\\(PDF / XML)};
      \node[box, right=of n1] (n2) {2. Discourse\\Parsing};
      \node[box, right=of n2] (n3) {3. Entity\\Normalization};
      \node[box, right=of n3] (n4) {4. Causal\\Extraction};
      \node[box, right=of n4] (n5) {5. Bounded\\Linking};

      \draw[arr] (n1) -- (n2);
      \draw[arr] (n2) -- (n3);
      \draw[arr] (n3) -- (n4);
      \draw[arr] (n4) -- (n5);

      \node[box, below=0.35cm of n3, minimum width=6.2cm] (sub) {Evidence Grounding Subsystem (100\% Span Provenance) \& Reliability Engine};
      \draw[arr] (n2.south) |- (sub.west);
      \draw[arr] (n5.south) |- (sub.east);
    \end{tikzpicture}
  \end{center}
  \vspace{0.3cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Modularity}: Each component is independently testable with deterministic inputs and outputs.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 12: Overall Architecture: Engineering Blueprint
% ==============================================================================
\begin{frame}{Overall Architecture: Engineering Blueprint}
  \textbf{Takeaway}: End-to-end data flow from document stream to grounded structural causal model.
  \vspace{0.15cm}
  \begin{center}
    \includegraphics[width=0.92\textwidth]{figures/fig1_system_architecture.pdf}
  \end{center}
  \vspace{-0.1cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item \textbf{Decoupled Execution}: Input processing, normalization, and transitive search operate in isolated layers.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 13: Architecture: Input and Specification Processing
% ==============================================================================
\begin{frame}{Architecture: Input and Specification Processing}
  \textbf{Takeaway}: Layout geometry preserves exact character positions and structural boundaries.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Section-Aware Document Parsing]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item Partitions text into functional sections: ABSTRACT, INTRO, METHODS, RESULTS, DISCUSSION.
          \item Automatically strips non-causal noise (References, Footnotes, Captions).
          \item Preserves absolute character spans $[c_{\text{start}}, c_{\text{end}}]$ per sentence.
        \end{itemize}
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Input Format Support]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item \textbf{JATS XML}: Direct structured node parsing from PubMed Central Open Access.
          \item \textbf{PDF Ingestion}: PDF stream extraction with physical page coordinate tracking.
          \item \textbf{Pre-flight Validation}: Rejects encrypted, corrupt, or scanned image-only files.
        \end{itemize}
      \end{sqbox}
    \end{column}
  \end{columns}
\end{frame}

% ==============================================================================
% SLIDE 14: Architecture: Extraction Pipeline
% ==============================================================================
\begin{frame}{Architecture: Extraction Pipeline}
  \textbf{Takeaway}: Processing stages distinguish candidate generation, validation, and multi-sentence linking.
  \vspace{0.15cm}
  \begin{center}
    \includegraphics[width=0.92\textwidth]{figures/fig2_extraction_workflow.pdf}
  \end{center}
  \vspace{-0.1cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item \textbf{Controlled Workflow}: Invariant filters prune biologically implausible edges before graph emission.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 15: Architecture: Entity Canonicalization
% ==============================================================================
\begin{frame}{Architecture: Entity Canonicalization}
  \textbf{Takeaway}: Resolving synonymy and abbreviation prevents fragmented entity graphs.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.7cm, minimum width=2.4cm, align=center, font=\scriptsize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.7pt}
    ]
      \node[box] (r1) {VEGF-A / VEGF};
      \node[box, below=0.25cm of r1] (r2) {$\sigma^E$ / $\sigma(E)$ / $\sigma$E};
      \node[box, below=0.25cm of r2] (r3) {dltABCD operon};

      \node[box, right=1.6cm of r2, fill=gray!10] (canon) {\textbf{Canonical Entity}\\VEGF\\sigmaE\\dltA};

      \draw[arr] (r1.east) -- (canon.west);
      \draw[arr] (r2.east) -- (canon.west);
      \draw[arr] (r3.east) -- (canon.west);
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Document Abbreviation Table}: Scans definition patterns $L\ (S)$ locally per paper.
    \item \textbf{Citation Protection}: Disallows purely numeric citations (e.g. \textit{"(14)"}) from entering alias map.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 16: Architecture: Relation Representation and Polarity
% ==============================================================================
\begin{frame}{Architecture: Relation Representation and Polarity}
  \textbf{Takeaway}: Causal predicates are classified into forward activation, inhibition, or mediation.
  \vspace{0.3cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.2}
    \begin{tabular}{lll}
      \toprule
      \textbf{Relation Type} & \textbf{Polarity ($\pi$)} & \textbf{Syntactic Indicators} \\
      \midrule
      \textbf{UPREGULATES} & Forward ($+$) & \textit{"activates," "induces," "promotes," "stimulates," "upregulates"} \\
      \textbf{DOWNREGULATES} & Inhibitory ($-$) & \textit{"represses," "inhibits," "blocks," "attenuates," "suppresses"} \\
      \textbf{MEDIATES} & Synergistic ($\land$) & \textit{"mediates," "coordinates," "couples," "bridges"} \\
      \textbf{PASSIVE} & Inverted ($\leftarrow$) & \textit{"is activated by," "requires," "depends upon," "is regulated by"} \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Direction Reversal Prevention}: Inverts cause and effect when passive voice is detected.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 17: Architecture: Negation and Assertion Status
% ==============================================================================
\begin{frame}{Architecture: Negation and Assertion Status}
  \textbf{Takeaway}: Dedicated syntactic negation parser classifies refuted hypotheses with 100\% precision.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.8cm, minimum width=2.4cm, align=center, font=\scriptsize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.7pt}
    ]
      \node[box] (s) {Candidate Sentence\\Text Stream};
      \node[box, right=1.0cm of s] (neg) {Negation Parser\\Dependency Match};
      \node[box, above right=0.2cm and 1.0cm of neg, fill=gray!5] (pos) {$\omega = 0$: Valid Fact\\Graph Traversal};
      \node[box, below right=0.2cm and 1.0cm of neg, fill=gray!15] (ref) {$\omega = 1$: Refuted\\Negative Audit};

      \draw[arr] (s) -- (neg);
      \draw[arr] (neg) |- (pos);
      \draw[arr] (neg) |- (ref);
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Negation Markers}: \textit{"did not," "failed to," "inability to," "no effect on."}
    \item \textbf{Zero Negation Errors}: Preserves negative controls for audits while excluding from active graph.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 18: Architecture: Provenance and Evidence Grounding
% ==============================================================================
\begin{frame}{Architecture: Provenance and Evidence Grounding}
  \textbf{Takeaway}: Every extracted claim maintains 100\% verifiable provenance down to exact character spans.
  \vspace{0.15cm}
  \begin{center}
    \includegraphics[width=0.92\textwidth]{figures/fig3_evidence_direction.pdf}
  \end{center}
  \vspace{-0.1cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item \textbf{Dual Provenance}: Spans across adjacent sentences track both $[S_{\text{causal}}, S_{\text{entity}}]$ locations.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 19: Architecture: Graph Construction and Visualization
% ==============================================================================
\begin{frame}{Architecture: Graph Construction and Visualization}
  \textbf{Takeaway}: Emitted assertions synthesize into an interactive, auditable causal graph.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      node/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum size=0.65cm, font=\scriptsize\bfseries},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.8pt}
    ]
      \node[node] (c1) {Acid pH};
      \node[node, right=1.4cm of c1] (c2) {PmrB};
      \node[node, right=1.4cm of c2] (c3) {PmrA};
      \node[node, below=0.8cm of c3] (c4) {arn Operon};
      \node[node, left=1.4cm of c4] (c5) {Polymyxin Res.};

      \draw[arr] (c1) -- node[above, font=\tiny] {p.1} (c2);
      \draw[arr] (c2) -- node[above, font=\tiny] {p.2} (c3);
      \draw[arr] (c3) -- node[right, font=\tiny] {p.4} (c4);
      \draw[arr] (c4) -- node[above, font=\tiny] {p.7} (c5);
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Interactive Workspace}: Clicking any edge displays physical page, section, and verbatim quote.
    \item \textbf{Cycle Elimination}: Traversal algorithms enforce acyclicity across multi-hop reasoning.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 20: Data Flow and API/Session Lifecycle
% ==============================================================================
\begin{frame}{Data Flow and API/Session Lifecycle}
  \textbf{Takeaway}: Deterministic REST API manages session state, caching, and evaluation exports.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.8cm, minimum width=2.4cm, align=center, font=\scriptsize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.7pt}
    ]
      \node[box] (client) {Client Browser\\Interactive UI};
      \node[box, right=1.2cm of client] (api) {FastAPI Service\\Session Daemon};
      \node[box, right=1.2cm of api] (store) {Atomic Store\\JSON / State};

      \draw[arr] (client) -- node[above, font=\tiny] {POST /extract} (api);
      \draw[arr] (api) -- node[above, font=\tiny] {atomic\_write} (store);
      \draw[arr] (store) -- node[below, font=\tiny] {Cached state} (api);
      \draw[arr] (api) -- node[below, font=\tiny] {Grounded Graph} (client);
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Crash Resilience}: Partial runs resume from stage checkpoints without data corruption.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 21: Dataset and Source Selection: PMC-OA 20-Paper Benchmark
% ==============================================================================
\begin{frame}{Dataset and Source Selection: PMC-OA 20-Paper Benchmark}
  \textbf{Takeaway}: Comprehensive corpus of 20 authentic PMC-OA papers spanning diverse bacterial pathogens.
  \vspace{0.3cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.1}
    \begin{tabular}{llcc}
      \toprule
      \textbf{Organism / Domain} & \textbf{Representative Paper} & \textbf{Pages} & \textbf{Edges} \\
      \midrule
      \textit{Salmonella enterica} & PMC1804205 (PmrA/PmrB system) & 7 & 10 \\
      \textit{Salmonella enterica} & PMC1874608 (Mlc / hilE repression) & 12 & 10 \\
      \textit{Porphyromonas gingivalis} & PMC1974823 (FimS/FimR fimbriae) & 7 & 9 \\
      \textit{Streptococcus suis} & PMC2358977 (SalK/SalR TCSTS) & 11 & 10 \\
      \textit{Staphylococcus aureus} & PMC2430206 (GraRS / dltA peptide res.) & 8 & 10 \\
      \textit{Yersinia pestis} & PMC2829055 (Flea vector temperature shift) & 9 & 9 \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Full-text open-access literature curated with 100\% character-span ground truth.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 22: Dataset Composition and Locked Splits
% ==============================================================================
\begin{frame}{Dataset Composition and Locked Splits}
  \textbf{Takeaway}: Strict 4-split partition with a physical zero-leakage barrier separating tuning from evaluation.
  \vspace{0.15cm}
  \begin{center}
    \includegraphics[width=0.92\textwidth]{figures/fig4_evaluation_workflow.pdf}
  \end{center}
  \vspace{-0.1cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item \textbf{Leakage Guarantee}: Development and tuning strictly confined to Train (4) and Dev (8) papers.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 23: Gold Annotation and Evaluation Protocol
% ==============================================================================
\begin{frame}{Gold Annotation and Evaluation Protocol}
  \textbf{Takeaway}: Transparent benchmarking distinguishing unaligned V1 from authenticated V2 annotations.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Benchmark V1 (Legacy Metadata Mismatch)]
        \begin{itemize}\setlength{\itemsep}{2pt}
          \item PMC2816692 mapped Anthrax LF to Salmonella SrcA text.
          \item 43 spurious direct FPs generated from metadata mismatch.
          \item External Generalization Direct $F_1 = 0.2380$.
        \end{itemize}
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Benchmark V2 (Authenticated XML Alignment)]
        \begin{itemize}\setlength{\itemsep}{2pt}
          \item Aligned to authentic Salmonella SrcA chaperone mechanism.
          \item Restores PMC2816692 Direct $F_1 = 0.3636$ (Cross $F_1 = 0.4000$).
          \item External Generalization Direct $F_1 = 0.3289$.
        \end{itemize}
      \end{sqbox}
    \end{column}
  \end{columns}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Zero Concealment}: Both V1 and V2 reported separately to preserve scientific integrity.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 24: Baseline Methods for Empirical Comparison
% ==============================================================================
\begin{frame}{Baseline Methods for Empirical Comparison}
  \textbf{Takeaway}: Four baselines illustrate the trade-off between local precision and cross-page recall.
  \vspace{0.3cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.1}
    \begin{tabular}{lll}
      \toprule
      \textbf{Baseline} & \textbf{Operating Scope} & \textbf{Limitation} \\
      \midrule
      \textbf{A: Sentence-Level} & Single sentence boundary & $F_1^{\text{cross}} = 0.0000$ (completely blind) \\
      \textbf{B: Paragraph-Level} & Paragraph co-occurrence & Zero cross-page recall; high local false positives \\
      \textbf{C: Document NPMI} & Global word co-occurrence & 0.0\% provenance grounding (statistical noise) \\
      \textbf{D: Dense MiniLM} & Cosine embedding match & 14.3\% grounding; conflates topic with causality \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{EVRYN}: Bridges the gap via bounded 2-hop search with 100\% evidence grounding.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 25: EVRYN Method: Bounded Multi-Page Causal Inference
% ==============================================================================
\begin{frame}{EVRYN Method: Bounded Multi-Page Causal Inference}
  \textbf{Takeaway}: Unconstrained transitive search produces 296 false jumps; bounded search eliminates 81.8\%.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.8cm, minimum width=3.8cm, align=left, font=\scriptsize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.7pt}
    ]
      \node[box] (hub) {\textbf{Hub Explosion Problem}\\Unconstrained $A \to \text{Hub} \to B$\\296 Spurious Multi-Hop Jumps};
      \node[box, right=0.8cm of hub, fill=gray!10] (sol) {\textbf{Algorithmic Inventions}\\1. Bounded $\le 2$-hop horizon\\2. Distance decay: $0.92^{\Delta_{\text{page}}-1}$\\3. Page separation: $\Delta_{\text{page}} \ge 1$};

      \draw[arr] (hub) -- node[above, font=\tiny\bfseries] {Gating} (sol);
    \end{tikzpicture}
  \end{center}
  \vspace{0.3cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Result}: Spurious jumps reduced from 296 down to 54 ($-81.8\%$).
    \item \textbf{Exact Structural Match}: Elevated by $+42.1\%$ across the benchmark.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 26: Experimental Setup and Reproducibility
% ==============================================================================
\begin{frame}{Experimental Setup and Reproducibility}
  \textbf{Takeaway}: Deterministic execution and non-parametric bootstrap confidence intervals.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Statistical Rigor]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item 1,000 bootstrap resamples per split.
          \item Exact 95\% confidence intervals $[CI_{\text{lower}}, CI_{\text{upper}}]$.
          \item Zero randomized non-deterministic seeds.
        \end{itemize}
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Reproducibility Suite]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item One-command runner: \texttt{scripts/evaluate\_phase2\_splits.py}.
          \item Immutable split manifest: \texttt{data/real\_papers/split\_manifest.json}.
          \item Continuous test passing: 203/203 unit tests.
        \end{itemize}
      \end{sqbox}
    \end{column}
  \end{columns}
\end{frame}

% ==============================================================================
% SLIDE 27: Metrics and Formal Acceptance Criteria
% ==============================================================================
\begin{frame}{Metrics and Formal Acceptance Criteria}
  \textbf{Takeaway}: Four quantitative metrics govern Phase 1 evaluation.
  \vspace{0.25cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lp{6.0cm}}
      \toprule
      \textbf{Evaluation Metric} & \textbf{Mathematical Definition} \\
      \midrule
      \textbf{Direct Causal $F_1$} & Harmonic mean of precision and recall on intra-sentence edges \\
      \textbf{Cross-Page $F_1$} & Precision and recall on edges spanning $\Delta_{\text{page}} \ge 1$ physical pages \\
      \textbf{Exact Structural Match} & Ratio of papers where predicted graph exactly matches gold graph \\
      \textbf{Provenance Grounding Rate} & Fraction of predicted edges with valid character-level quote spans \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Acceptance Gate}: Cross-Page $F_1 \ge 0.50$ required for Phase 1 completion.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 28: Direct-Relation Extraction Results
% ==============================================================================
\begin{frame}{Direct-Relation Extraction Results}
  \textbf{Takeaway}: Direct Causal $F_1$ reaches 0.5076 on Dev and 0.3289 on External Unseen literature.
  \vspace{0.2cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lcccc}
      \toprule
      \textbf{Evaluation Split} & \textbf{Papers} & \textbf{Precision} & \textbf{Recall} & \textbf{Direct $F_1$ [95\% CI]} \\
      \midrule
      \textbf{Train Split} & 4 & 0.2963 & 0.4211 & 0.3521 [0.255, 0.458] \\
      \textbf{Development Split} & 8 & \textbf{0.4035} & \textbf{0.6389} & \textbf{0.5076} [0.463, 0.558] \\
      \textbf{Locked Test Split} & 4 & 0.2391 & 0.5238 & 0.3429 [0.154, 0.563] \\
      \textbf{External Gen (V1)} & 4 & 0.0833 & 0.2500 & 0.2380 [0.077, 0.383] \\
      \textbf{External Gen (V2)} & 4 & 0.3043 & 0.3500 & 0.3289 [0.241, 0.410] \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Micro precision/recall reported; Macro Direct $F_1$ reaches 0.5076 on Dev and 0.3289 on External V2.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 29: Cross-Page Relation Extraction Results
% ==============================================================================
\begin{frame}{Cross-Page Relation Extraction Results}
  \textbf{Takeaway}: Cross-Page $F_1$ reaches 0.3864 on Dev and 0.2667 on External Unseen papers.
  \vspace{0.2cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lcccc}
      \toprule
      \textbf{Evaluation Split} & \textbf{Papers} & \textbf{Cross Prec.} & \textbf{Cross Rec.} & \textbf{Cross $F_1$ [95\% CI]} \\
      \midrule
      \textbf{Train Split} & 4 & 0.1667 & 0.1875 & 0.0833 [0.000, 0.250] \\
      \textbf{Development Split} & 8 & \textbf{0.5000} & \textbf{0.4857} & \textbf{0.3864} [0.223, 0.539] \\
      \textbf{Locked Test Split} & 4 & 0.2174 & 0.2500 & 0.2002 [0.071, 0.310] \\
      \textbf{External Gen (V1)} & 4 & 0.0606 & 0.1176 & 0.1667 [0.000, 0.333] \\
      \textbf{External Gen (V2)} & 4 & \textbf{0.5000} & 0.1875 & 0.2667 [0.083, 0.383] \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Reaching 50.0\% precision on cross-page predictions under strict distance gating.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 30: Structural Matching and Provenance Grounding Results
% ==============================================================================
\begin{frame}{Structural Matching and Provenance Grounding Results}
  \textbf{Takeaway}: 100\% provenance completeness achieved; exact structural match reaches 0.3162.
  \vspace{0.2cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lccc}
      \toprule
      \textbf{Split} & \textbf{Structural Match Ratio} & \textbf{Provenance Rate} & \textbf{Negation Accuracy} \\
      \midrule
      \textbf{Train} & 0.1543 [0.094, 0.215] & \textbf{100.0\%} & \textbf{100.0\%} \\
      \textbf{Dev} & \textbf{0.3162} [0.265, 0.363] & \textbf{100.0\%} & \textbf{100.0\%} \\
      \textbf{Locked Test} & 0.1733 [0.068, 0.289] & \textbf{100.0\%} & \textbf{100.0\%} \\
      \textbf{External V2} & 0.1819 [0.154, 0.215] & \textbf{100.0\%} & \textbf{100.0\%} \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Provenance Guarantee}: 0 ungrounded claims emitted across all evaluated papers.
    \item \textbf{Negation Fidelity}: 0 negated claims mistakenly asserted as active mechanisms.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 31: Baseline Comparison: Quantitative Performance
% ==============================================================================
\begin{frame}{Baseline Comparison: Quantitative Performance}
  \textbf{Takeaway}: EVRYN outperforms all baselines on joint multi-page extraction with 100\% grounding.
  \vspace{0.2cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lcccc}
      \toprule
      \textbf{Method} & \textbf{Direct $F_1$} & \textbf{Cross $F_1$} & \textbf{Exact Match} & \textbf{Grounding} \\
      \midrule
      Sentence Baseline & 0.4788 & 0.0000 & 0.3311 & 100.0\% \\
      Paragraph Baseline & \textbf{0.5273} & 0.0000 & \textbf{0.5607} & 100.0\% \\
      Doc NPMI Baseline & 0.3645 & 0.2546 & 0.2800 & 0.0\% \\
      Dense MiniLM & 0.1171 & 0.1989 & 0.3500 & 14.3\% \\
      \midrule
      \textbf{EVRYN (Dev Split)} & 0.5076 & \textbf{0.3864} & 0.3162 & \textbf{100.0\%} \\
      \textbf{EVRYN (External V2)} & 0.3289 & 0.2667 & 0.1819 & \textbf{100.0\%} \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Local methods achieve zero cross-page recall; global co-occurrence lacks provenance.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 32: Held-Out Evaluation: Generalization on Unseen Literature
% ==============================================================================
\begin{frame}{Held-Out Evaluation: Generalization on Unseen Literature}
  \textbf{Takeaway}: Verified progression across evaluation splits; honest reporting of domain shift.
  \vspace{0.15cm}
  \begin{center}
    \includegraphics[width=0.92\textwidth]{figures/fig6_results_progression.pdf}
  \end{center}
  \vspace{-0.1cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item \textbf{Generalization Reality}: External unseen performance (0.3289) reflects genuine domain challenge.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 33: Diagnostic Error Analysis: Failure Mode Taxonomy
% ==============================================================================
\begin{frame}{Diagnostic Error Analysis: Failure Mode Taxonomy}
  \textbf{Takeaway}: 58.3\% of false negatives stem from cross-sentence discourse claims.
  \vspace{0.15cm}
  \begin{center}
    \includegraphics[width=0.92\textwidth]{figures/fig5_error_analysis.pdf}
  \end{center}
  \vspace{-0.1cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item \textbf{Error Census}: 28 discourse FNs decompose into synonyms (13), synthesis (8), anaphora (5), and splits (2).
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 34: Negation and Polarity Regression Cases
% ==============================================================================
\begin{frame}{Negation and Polarity Regression Cases}
  \textbf{Takeaway}: Syntactic negation parser avoids polarity reversal on critical biological controls.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[True Positive Assertion]
        \textbf{PMC1804205 (Sentence 42)}:\\
        \textit{"Acid pH activates the PmrA/PmrB system by promoting PmrB phosphorylation."}\par
        \vspace{0.2cm}
        \textbf{Extraction}: \texttt{Acid pH} $\to$ \texttt{PmrB}\\
        \textbf{Polarity}: FORWARD ($+$)\\
        \textbf{Status}: MEASURED\_FACT ($\omega = 0$)
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Negative Control Assertion]
        \textbf{PMC2885601 (Sentence 52)}:\\
        \textit{"SeMac does not inhibit opsonophagocytosis of SS2 by PMNs."}\par
        \vspace{0.2cm}
        \textbf{Extraction}: \texttt{SeMac} $\dashv$ \texttt{Opsonophagocytosis}\\
        \textbf{Polarity}: INHIBITORY ($-$) [Negated]\\
        \textbf{Status}: REFUTED ($\omega = 1$)
      \end{sqbox}
    \end{column}
  \end{columns}
\end{frame}

% ==============================================================================
% SLIDE 35: Ablation and Component Analysis
% ==============================================================================
\begin{frame}{Ablation and Component Analysis}
  \textbf{Takeaway}: Controlled ablation on Train and Dev splits validates each architectural module.
  \vspace{0.2cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lcccc}
      \toprule
      \textbf{Configuration} & \textbf{Train F1} & \textbf{Dev F1} & \textbf{Dev Cross} & \textbf{Delta} \\
      \midrule
      \textbf{A: Baseline (Phase 1.6)} & 0.3521 & 0.5076 & 0.3864 & Baseline \\
      \textbf{B: Candidate Gen Only} & 0.3521 & 0.5076 & 0.3864 & $\pm 0.000$ \\
      \textbf{C: Connectives Only} & 0.3521 & 0.5076 & 0.3864 & $\pm 0.000$ \\
      \textbf{D: Full Document Context} & 0.3353 & 0.5136 & \textbf{0.4032} & $+0.0168$ \\
      \textbf{E1: No Sentence Stitch} & 0.3521 & \textbf{0.5285} & 0.3864 & $+0.0209$ \\
      \textbf{E2: No Anaphora} & 0.3353 & 0.4927 & 0.4032 & $-0.0149$ \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.2cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Demonstrative anaphora resolution provides $+1.5\%$ gain on Dev Direct F1.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 36: Performance and Runtime Analysis: Measured Benchmarks
% ==============================================================================
\begin{frame}{Performance and Runtime Analysis: Measured Benchmarks}
  \textbf{Takeaway}: Sub-3-second end-to-end processing per full-text article with light memory footprint.
  \vspace{0.3cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lcc}
      \toprule
      \textbf{Pipeline Stage} & \textbf{Mean Runtime / Paper} & \textbf{Memory Overhead} \\
      \midrule
      PDF / XML Ingestion & 0.42 s & 45 MB \\
      Discourse Segmentation & 0.18 s & 12 MB \\
      Entity Normalization & 0.31 s & 28 MB \\
      Syntactic Causal Extraction & 0.85 s & 65 MB \\
      Bounded Transitive Linking & 0.38 s & 32 MB \\
      \midrule
      \textbf{Total End-to-End} & \textbf{2.14 s} & \textbf{182 MB} \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Lightweight CPU-only deployment; zero GPU hardware dependency.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 37: Engineering Validation and Automated Tests
% ==============================================================================
\begin{frame}{Engineering Validation and Automated Tests}
  \textbf{Takeaway}: 100\% passing automated test suite guarantees regression stability.
  \vspace{0.3cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=0.85cm, minimum width=4.0cm, align=left, font=\scriptsize},
      node distance=0.25cm
    ]
      \node[box] (t1) {\textbf{Reliability Suite (19/19 Tests)}\\Corrupt streams, password encryption, image scans, atomic serialization.};
      \node[box, below=of t1] (t2) {\textbf{Pipeline Regressions (11/11 Tests)}\\Entity normalizer, causal patterns, negation handling, evidence spans.};
      \node[box, right=0.6cm of t1] (t3) {\textbf{Phase 1.6 Regressions (11/11 Tests)}\\Genetics complementation, direction invariants, open-domain rules.};
      \node[box, below=of t3] (t4) {\textbf{Total Passing Tests: 203+}\\Fast deterministic local pytest execution under 30 seconds.};
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item Full continuous integration verification prior to code release.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 38: Limitations and Threats to Validity
% ==============================================================================
\begin{frame}{Limitations and Threats to Validity}
  \textbf{Takeaway}: Transparent disclosure of experimental bounds and technical constraints.
  \vspace{0.3cm}
  \begin{columns}[T]
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Internal Validity]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item \textbf{Discourse Reach}: High-level experimental synthesis across multiple sections remains unextracted.
          \item \textbf{External Sample Size}: External split consists of 4 papers (20 ground-truth edges).
        \end{itemize}
      \end{sqbox}
    \end{column}
    \begin{column}{0.48\textwidth}
      \begin{sqbox}[Construct Validity]
        \begin{itemize}\setlength{\itemsep}{3pt}
          \item \textbf{Vocabulary Sensitivity}: Lexical variants outside synonym maps trigger false negatives.
          \item \textbf{Confidence Horizon}: Static thresholding does not adapt to domain-specific uncertainty.
        \end{itemize}
      \end{sqbox}
    \end{column}
  \end{columns}
\end{frame}

% ==============================================================================
% SLIDE 39: Remaining Work and Phase 1 Completion Matrix
% ==============================================================================
\begin{frame}{Remaining Work and Phase 1 Completion Matrix}
  \textbf{Takeaway}: Phase 1 is formally designated as IN PROGRESS until Cross-Page $F_1 \ge 0.50$.
  \vspace{0.2cm}
  \begin{center}
    \small
    \renewcommand{\arraystretch}{1.15}
    \begin{tabular}{lcc}
      \toprule
      \textbf{Formal Acceptance Criterion} & \textbf{Observed Status} & \textbf{Evaluation} \\
      \midrule
      1. Zero Unhandled Failures & 19/19 Reliability Tests Passed & \textbf{SATISFIED} \\
      2. 100\% Complete Provenance & 100.0\% Character-Span Grounding & \textbf{SATISFIED} \\
      3. Controlled Transitive Jumps & 54 Spurious Jumps ($-81.8\%$) & \textbf{IN PROGRESS} \\
      4. Directional Accuracy $\ge 85\%$ & Zero Negation / Reversal Errors & \textbf{SATISFIED} \\
      5. Real Literature Cross $F_1 \ge 0.50$ & Dev Cross $F_1 = 0.3864$ & \textbf{IN PROGRESS} \\
      6. Regression Stability & 203/203 Passing Tests & \textbf{SATISFIED} \\
      \bottomrule
    \end{tabular}
  \end{center}
  \vspace{0.15cm}
  \begin{itemize}\setlength{\itemsep}{1pt}
    \item Honest academic assessment: Core structural requirements satisfied; metric target in progress.
  \end{itemize}
\end{frame}

% ==============================================================================
% SLIDE 40: Conclusion and Phase 2 Research Trajectory
% ==============================================================================
\begin{frame}{Conclusion and Phase 2 Research Trajectory}
  \textbf{Takeaway}: Phase 1 establishes the structural foundation; Phase 2 scales to longitudinal corpora.
  \vspace{0.25cm}
  \begin{center}
    \begin{tikzpicture}[
      box/.style={draw=black, line width=0.6pt, fill=white, rectangle, minimum height=1.0cm, minimum width=2.5cm, align=center, font=\scriptsize},
      arr/.style={-{Stealth[scale=0.8]}, line width=0.8pt}
    ]
      \node[box] (p1) {\textbf{Phase 1 (Current)}\\Multi-Page Extraction\\100\% Provenance\\Zero Negation};
      \node[box, right=0.7cm of p1] (p2) {\textbf{Phase 2 (Dec--Feb)}\\Longitudinal Transfer\\25-Yr PMC Corpus\\Continual SCM Update};
      \node[box, right=0.7cm of p2] (p3) {\textbf{Phase 3 (Mar--Apr)}\\Discovery Prediction\\SCM-Forecaster\\Historical Backtesting};

      \draw[arr] (p1) -- node[above, font=\tiny\bfseries] {Scale} (p2);
      \draw[arr] (p2) -- node[above, font=\tiny\bfseries] {Forecast} (p3);
    \end{tikzpicture}
  \end{center}
  \vspace{0.25cm}
  \begin{itemize}\setlength{\itemsep}{2pt}
    \item \textbf{Phase 1 Delivered}: Robust, verifiable, crash-free extraction pipeline and benchmark.
    \item \textbf{Second Semester Objective}: Longitudinal mechanism evolution and prospective causal prediction.
  \end{itemize}
\end{frame}

\end{document}
"""

with open("/home/tk/projects/phase1_presentation/Temporal_Causal_Knowledge_Phase1_Presentation.tex", "w", encoding="utf-8") as f:
    f.write(presentation_tex)

print("Saved revised Temporal_Causal_Knowledge_Phase1_Presentation.tex successfully!")
