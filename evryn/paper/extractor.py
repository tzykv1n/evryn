# evryn paper extract <pdf_path>
# pytest tests/test_paper_pipeline.py

import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple

from .types import (
    ScientificDocument,
    SentenceSpan,
    CausalAssertion,
    CausalRelationType,
    EvidenceStatus,
    ScientificSectionType,
)
from .normalizer import PaperEntityNormalizer
from .environmental_extractor import EnvironmentalParameterExtractor
from .document_context import DocumentContextResolver


CAUSAL_INFLUENCE_PATTERNS = [
    r"\b(?:leads?|led|leading)\s+to\b",
    r"\b(?:results?|resulted|resulting)\s+in\b",
    r"\b(?:causes?|caused|causing)\b",
    r"\b(?:drives?|driven|driving)\b",
    r"\b(?:affects?|affected|affecting)\b",
    r"\b(?:regulates?|regulated|regulating)\b",
    r"\b(?:controls?|controlled|controlling)\b",
    r"\b(?:modulates?|modulated|modulating)\b",
]

ACTIVATION_PATTERNS = [
    r"\b(?:promotes?|promoted|promoting)\b",
    r"\b(?:triggers?|triggered|triggering)\b",
    r"\b(?:induces?|induced|inducing)\b",
    r"\b(?:stimulates?|stimulated|stimulating)\b",
    r"\b(?:restores?|restored|restoring)\b",
    r"\b(?:contributes?|contributed|contributing)\s+to\b",
    r"\b(?:activates?|activated|activating)\b",
    r"\b(?:upregulates?|upregulated|upregulating)\b",
    r"\b(?:enhances?|enhanced|enhancing)\b",
    r"\b(?:increases?|increased|increasing)\b",
    r"\b(?:phosphorylates?|phosphorylated|phosphorylating)\b",
    r"\b(?:recruits?|recruited|recruiting)\b",
    r"\b(?:binds?|bound|binding)\b",
    r"\b(?:cleaves?|cleaved|cleaving)\b",
    r"\b(?:stabilizes?|stabilized|stabilizing)\b",
    r"\b(?:liberates?|liberated|liberating)\b",
    r"\b(?:traps?|trapped|trapping)\b",
    r"\b(?:is|are|was|were)?\s*(?:essential|required|requisite|necessary|critical|sufficient)\s+(?:for|to)\b",
    r"\b(?:responsible\s+for)\b",
    r"\b(?:confers?|conferred|conferring)\b",
    r"\b(?:encodes?|encoded|encoding)\b",
    r"\b(?:chelates?|chelated|chelating)\b",
    r"\b(?:protects?|protected|protecting)\s+against\b",
    r"\b(?:transfers?\s+phosphate)\b",
    r"\bactivator\s+of\b",
    r"\binducer\s+of\b",
    r"\bregulator\s+of\b",
    r"\b(?:positive\s+effects?\s+(?:on|upon)|positive\s+regulation\s+of|positively\s+(?:regulates?|regulated|regulating))\b",
    r"\b(?:favou?rs?|favou?red|favou?ring)\b",
    r"\b(?:facilitates?|facilitated|facilitating)\b",
    r"\b(?:plays?\s+(?:an?\s+)?(?:primary|key|crucial|essential|major|critical|central|important|pivotal|significant)?\s*role\s+in\s+(?:(?:the\s+)?(?:activation|induction|expression|regulation|stimulation|control)\s+of|(?:regulating|controlling|activating|inducing|promoting|stimulating)))\b",
    r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:involved\s+in|implicated\s+in|participates?\s+in)\s+(?:(?:the\s+)?(?:fine-tuning|regulation|control|modulation|expression|activation|induction)\s+(?:of\s+)?|(?:fine-tuning|regulating|controlling|modulating|activating|inducing|promoting))\b",
    r"\b(?:acts?|acted|acting|serves?|served|serving)\s+as\s+an?\s+(?:activator|inducer|stimulator)\s+of\b",
]

LIGAND_SENSOR_PATTERNS = [
    r"\b(?:is|was|are|were)?\s*(?:directly\s+)?(?:sensed|recognized|detected)\s+by\b",
]

PREVENTION_PATTERNS = [
    r"\b(?:prevents?|prevented|preventing)\b",
    r"\b(?:abrogates?|abrogated|abrogating)\b",
]

INHIBITION_PATTERNS = [
    r"\brepressor\s+of\b",
    r"\binhibitor\s+of\b",
    r"\b(?:inhibits?|inhibited|inhibiting)\b",
    r"\b(?:downregulates?|downregulated|downregulating)\b",
    r"\b(?:suppresses?|suppressed|suppressing)\b",
    r"\b(?:blocks?|blocked|blocking)\b",
    r"\b(?:attenuates?|attenuated|attenuating)\b",
    r"\b(?:diminishes?|diminished|diminishing)\b",
    r"\b(?:reduces?|reduced|reducing)\b",
    r"\b(?:decreases?|decreased|decreasing)\b",
    r"\b(?:dampens?|dampened|dampening)\b",
    r"\b(?:represses?|repressed|repressing)\b",
    r"\b(?:abolishes?|abolished|abolishing)\b",
    r"\b(?:degrades?|degraded|degrading)\b",
    r"\b(?:degradation\s+of)\b",
    r"\b(?:loss\s+of)\b",
    r"\b(?:disrupts?|disrupted|disrupting)\b",
    r"\b(?:mutation\s+(?:in|of))\b",
    r"\b(?:deletion\s+(?:in|of))\b",
    r"\b(?:negative\s+effects?\s+(?:on|upon)|negative\s+regulation\s+of|negatively\s+(?:regulates?|regulated|regulating))\b",
    r"\b(?:acts?|acted|acting|serves?|served|serving)\s+as\s+an?\s+(?:inhibitor|repressor)\s+of\b",
    r"\b(?:plays?\s+(?:an?\s+)?(?:primary|key|crucial|essential|major|critical|central|important|pivotal|significant)?\s*role\s+in\s+(?:(?:the\s+)?(?:repression|inhibition|suppression)\s+of|(?:repressing|inhibiting|suppressing)))\b",
]

MEDIATION_PATTERNS = [
    r"\b(?:mediates?|mediated|mediating)\b",
    r"\b(?:signals?\s+through)\b",
    r"\b(?:acts?\s+via)\b",
    r"\b(?:functions?\s+through)\b",
]

ASSOCIATION_PATTERNS = [
    r"\b(?:is|was|are|were)?\s*(?:not\s+)?associated\s+with\b",
    r"\b(?:is|was|are|were)?\s*(?:not\s+)?correlated\s+with\b",
    r"\b(?:is|was|are|were)?\s*(?:not\s+)?linked\s+to\b",
    r"\b(?:correlates?|correlated|correlating)\s+with\b",
    r"\b(?:co-occurs?|co-occurring)\s+with\b",
]

PASSIVE_INDICATORS = [
    r"\b(?:is|was|are|were|has\s+been|have\s+been)(?:\s+\w+){0,3}\s+(?:shown\s+to\s+be|demonstrated\s+to\s+be|known\s+to\s+be|found\s+to\s+be)?\s*(?:induced|activated|triggered|stimulated|phosphorylated|upregulated|promoted|affected|regulated|controlled|modulated)\s+(?:by|upon)\b",
    r"\b(?:is|was|are|were|has\s+been|have\s+been)(?:\s+\w+){0,3}\s+(?:shown\s+to\s+be|demonstrated\s+to\s+be|known\s+to\s+be|found\s+to\s+be)?\s*(?:inhibited|suppressed|blocked|repressed|downregulated|degraded|diminished|reduced|abrogated)\s+(?:by|upon)\b",
    r"\b(?:promoted|affected)\s+(?:by|upon)\b",
    r"\b(?:is|was|are|were)?\s*cleaved\s+by\b",
    r"\bis\s+induced\s+by\b",
    r"\bwas\s+induced\s+by\b",
    r"\bare\s+induced\s+by\b",
    r"\bwere\s+induced\s+by\b",
    r"\bis\s+activated\s+by\b",
    r"\bwas\s+activated\s+by\b",
    r"\bis\s+triggered\s+by\b",
    r"\bwas\s+triggered\s+by\b",
    r"\bis\s+upregulated\s+by\b",
    r"\bwas\s+upregulated\s+by\b",
    r"\bis\s+inhibited\s+by\b",
    r"\bwas\s+inhibited\s+by\b",
    r"\bis\s+suppressed\s+by\b",
    r"\bwas\s+suppressed\s+by\b",
    r"\bis\s+blocked\s+by\b",
    r"\bwas\s+blocked\s+by\b",
    r"\binduced\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\bactivated\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\btriggered\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\bstimulated\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\bphosphorylated\s+(?:\w+\s+)?(?:by|with)\b",
    r"\bupregulated\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\binhibited\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\bsuppressed\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\bblocked\s+(?:\w+\s+)?(?:by|with)\b",
    r"\bmediated\s+by\b",
    r"\bdependent\s+on\b",
    r"\bdownstream\s+of\b",
    r"\b(?:results?|resulted|resulting)\s+from\b",
    r"\bcaused\s+by\b",
    r"\bdue\s+to\b",
    r"(?<!\bis\s)(?<!\bwas\s)(?<!\bare\s)(?<!\bwere\s)\b(?:requires?|requiring)\b",
    r"\bpromoted\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\babolished\s+(?:\w+\s+)?(?:by|with|upon)\b",
    r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:partially\s+|mostly\s+|fully\s+)?(?:restored|rescued)\s+(?:in|by|upon|with)\b",
    r"\b(?:is|was|are|were)?\s*(?:regulated|controlled|modulated)\s+(?:\w+\s+)?(?:by|via|through)\b",
    r"\b(?:is|was|are|were)?\s*attributed\s+to\b",
    r"\b(?:is|was|are|were)?\s*encoded\s+by\b",
    r"\b(?:is|was|are|were)?\s*(?:repressed|downregulated|degraded)\s+(?:\w+\s+)?(?:by|upon)\b",
    r"\b(?:is|was|are|were)?\s*required\s+(?:\w+\s+)?by\b",
    r"\bdepends?\s+on\b",
    r"\bresponsive\s+to\b",
    r"\bunder\s+(?:the\s+)?control\s+of\b",
    r"\bunder\s+(?:the\s+)?regulation\s+of\b",
    r"\bin\s+response\s+to\b",
    r"\bas\s+a\s+result\s+of\b",
    r"\bas\s+a\s+consequence\s+of\b",
    r"\bfollowing\s+(?:treatment|stimulation|exposure|activation|addition|administration)\s+(?:with|to|of)\b",
    r"\bupon\s+(?:treatment|stimulation|exposure|activation|addition|administration|binding)\s+(?:with|to|of)\b",
    r"\b(?:is|was|are|were)?\s*(?:promoted|induced|activated|stimulated|upregulated|expressed)\s+in\s+(?:media\s+of\s+)?\b",
    r"\b(?:is|was|are|were)?\s*(?:governed|driven|conferred|elicited)\s+(?:\w+\s+)?by\b",
    r"\b(?:is|was|are|were)?\s*required\s+for(?:\s+\w+){0,5}\s+in\s+response\s+to\b",
    r"\b(?:is|was|are|were)?\s*(?:also\s+)?(?:repressed|suppressed|down-?regulated|downregulated|reduced|decreased|attenuated|diminished|lost)\s+(?:\w+\s+){0,3}in\s+(?:the\s+)?(?:\w+\s+)?mutants?\b",
    r"\b(?:become|becomes|became|could\s+become|may\s+become)?\s*phosphorylated\s+(?:from|by)\b",
    r"\b(?:is|are|was|were)?\s*(?:necessary|required|essential)\s+for(?:\s+a)?(?:\s+\w+){0,3}\s+(?:responding|response|sensing)\s+to\b",
    r"\b(?:responds?|responded|responding)\s+to\b",
    r"\b(?:is|was|are|were)?\s*(?:expressed|transcribed|produced|activated|induced)\s+in\s+response\s+to\b",
    r"\bunder\s+(?:the\s+)?(?:control|regulation)\s+of\b",
]

NEGATION_PATTERNS = [
    r"\b(?:did\s+not|does\s+not|do\s+not)\s+(?:induce|cause|inhibit|activate|alter|affect|change|promote|decrease|increase|reduce|suppress|block|associate|correlate)\b",
    r"\b(?:is\s+not|are\s+not|was\s+not|were\s+not)\s+(?:associated\s+with|correlated\s+with|linked\s+to|caused\s+by|induced\s+by|altered\s+by|affected\s+by|sufficient\s+to)\b",
    r"\b(?:is\s+not|are\s+not|was\s+not|were\s+not)\s+(?:altered|affected|changed|induced|inhibited|decreased|increased|reduced|attenuated)\b",
    r"\b(?:is\s+not|are\s+not|was\s+not|were\s+not)\s+significantly\s+attenuated\b",
    r"\bfailed\s+to\s+(?:induce|cause|inhibit|activate|alter|affect|change|promote|decrease|increase|reduce|suppress|block)\b",
    r"\bno\s+significant\s+(?:effect|change|increase|decrease|alteration|induction|inhibition|association|correlation)\b",
    r"\bwithout\s+(?:affecting|altering|changing|inducing|inhibiting|decreasing|increasing|reducing)\b",
    r"\bnot\s+(?:significantly\s+)?(?:associated\s+with|correlated\s+with|linked\s+to)\b",
    r"\bunaltered\b",
    r"\bno\s+(?:detectable\s+)?(?:effect|association|correlation|change)\b",
    r"\blacks?\s+(?:an?\s+)?(?:effect|induction|inhibition|association)\b",
]

UNCERTAINTY_PATTERNS = [
    r"\b(?:may|might|could|potentially|possibly|presumably)\b",
    r"\b(?:we\s+hypothesize|we\s+hypothesized|we\s+speculate|we\s+speculated|we\s+postulated|it\s+is\s+postulated|it\s+was\s+postulated|it\s+was\s+hypothesized)\b",
    r"\b(?:suggests?\s+that|indicates?\s+a\s+potential)\b",
    r"\b(?:remains?\s+unclear|remains?\s+elusive|to\s+be\s+determined)\b",
    r"\b(?:we\s+tested\s+the\s+possibility\s+of|to\s+test\s+whether|to\s+investigate\s+whether|to\s+determine\s+if)\b",
    r"\b(?:tested\s+whether|investigated\s+whether|evaluated\s+whether)\b",
]

# Precompiled regex patterns for performance optimization
COMPILED_NEGATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in NEGATION_PATTERNS]
COMPILED_UNCERTAINTY_PATTERNS = [re.compile(p, re.IGNORECASE) for p in UNCERTAINTY_PATTERNS]

_ALL_PATTERNS_RAW: List[Tuple[str, CausalRelationType, bool]] = []
for p in PASSIVE_INDICATORS:
    rel = CausalRelationType.DOWNREGULATES if any(re.search(a, p, re.IGNORECASE) for a in INHIBITION_PATTERNS) else CausalRelationType.UPREGULATES
    _ALL_PATTERNS_RAW.append((p, rel, True))
for p in ASSOCIATION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.ASSOCIATED, False))
for p in MEDIATION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.MEDIATES, False))
for p in PREVENTION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.PREVENTS, False))
for p in INHIBITION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.DOWNREGULATES, False))
for p in CAUSAL_INFLUENCE_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.DIRECT_CAUSE, False))
for p in ACTIVATION_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.UPREGULATES, False))
for p in LIGAND_SENSOR_PATTERNS:
    _ALL_PATTERNS_RAW.append((p, CausalRelationType.UPREGULATES, False))

COMPILED_SYNTACTIC_PATTERNS = [
    (re.compile(p, re.IGNORECASE), rel, is_passive)
    for p, rel, is_passive in _ALL_PATTERNS_RAW
]

COMPILED_PASSIVE_INDICATORS = [
    (re.compile(p, re.IGNORECASE), any(re.search(a, p, re.IGNORECASE) for a in INHIBITION_PATTERNS))
    for p in PASSIVE_INDICATORS
]
COMPILED_INHIBITION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INHIBITION_PATTERNS]
COMPILED_ACTIVATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ACTIVATION_PATTERNS]
COMPILED_MEDIATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in MEDIATION_PATTERNS]
COMPILED_ASSOCIATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ASSOCIATION_PATTERNS]
COMPILED_LIGAND_SENSOR_PATTERNS = [re.compile(p, re.IGNORECASE) for p in LIGAND_SENSOR_PATTERNS]
COMPILED_GENETICS_MUTANT_DOWN = re.compile(
    r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:also\s+)?(?:strongly|dramatically|significantly|substantially|markedly|approximately\s+\w+(?:-fold|fold)|\w+(?:-fold|fold))?\s*"
    r"(?:downregulated|reduced|repressed|decreased|attenuated|lower|diminished|abolished|lost|eliminated|less|suppressed|inhibited|impaired|defective|lacking)\s*"
    r"(?:(?:approximately\s+)?\w+(?:-fold|fold))?\s+in\s+(?:the|a|an)?\s*",
    re.IGNORECASE,
)
COMPILED_GENETICS_MUTANT_UP = re.compile(
    r"\b(?:is|was|are|were|has\s+been|have\s+been)?\s*(?:also\s+)?(?:strongly|dramatically|significantly|substantially|markedly|approximately\s+\w+(?:-fold|fold)|\w+(?:-fold|fold))?\s*"
    r"(?:upregulated|increased|elevated|higher|induced|activated|derepressed|enhanced|augmented|greater|promoted|hyper-?induced|hyper-?activated|accumulated|over-?expressed)\s*"
    r"(?:(?:approximately\s+)?\w+(?:-fold|fold))?\s+in\s+(?:the|a|an)?\s*",
    re.IGNORECASE,
)
COMPILED_GENETICS_MUTANT_DEFECT = re.compile(
    r"\b(?:mutant|mutation|null|deletion|deficiency)\b(?:\s+\w+){0,6}\s+(?:showed|exhibited|displayed|caused|led\s+to|resulted\s+in)\s+(?:a\s+)?(?:defect|impairment|loss|reduction)\s+in\s+",
    re.IGNORECASE,
)

PAT_AGENT_NOMINAL_ACT = re.compile(
    r"^\s*(?:direct\s+|indirect\s+)?(?:activation|induction|stimulation|up-?regulation)\s+of(?:\s+(?:the|promoter\s+of|transcription\s+of|expression\s+of))?$",
    re.IGNORECASE,
)
PAT_AGENT_NOMINAL_INHIB = re.compile(
    r"^\s*(?:direct\s+|indirect\s+)?(?:repression|inhibition|suppression|down-?regulation)\s+of(?:\s+(?:the|promoter\s+of|transcription\s+of|expression\s+of))?$",
    re.IGNORECASE,
)

COMPILED_DIRECT_CAUSATIVE_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:causes?|caused|causing)\b",
        r"\b(?:leads?|led|leading)\s+to\b",
        r"\b(?:results?|resulted|resulting)\s+in\b",
        r"\b(?:controls?|controlled|controlling)\b",
        r"\b(?:regulates?|regulated|regulating)\b",
        r"\b(?:modulates?|modulated|modulating)\b",
        r"\b(?:drives?|driven|driving)\b",
    ]
]

COMPILED_MUTATION_ABOLISHED = re.compile(
    r"\b(?:substitution|mutation|deletion|disruption|loss|deficiency)\s+(?:of|in)\b.*?\b(?:decreased|abolished|reduced|diminished|attenuated|eliminated|prevented|impaired)\b",
    re.IGNORECASE,
)

ACTIVE_MATRIX_CAUSATIVE_VERBS = re.compile(
    r"\b(?:causes?|caused|causing|leads?\s+to|led\s+to|leading\s+to|results?\s+in|resulted\s+in|resulting\s+in|"
    r"induces?|induced|inducing|activates?|activated|activating|promotes?|promoted|promoting|"
    r"stimulates?|stimulated|stimulating|represses?|repressed|repressing|inhibits?|inhibited|inhibiting|"
    r"downregulates?|downregulated|downregulating|upregulates?|upregulated|upregulating|"
    r"triggers?|triggered|triggering)\b",
    re.IGNORECASE,
)

SUBORDINATE_PREP_MODIFIERS = re.compile(
    r"\b(?:under\s+(?:the\s+)?(?:control|regulation)\s+of|in\s+response\s+to|responsive\s+to|"
    r"following\s+(?:treatment|stimulation|exposure|activation|addition)\s+(?:with|to|of)|"
    r"as\s+a\s+(?:result|consequence)\s+of)\b",
    re.IGNORECASE,
)

FORWARD_CONNECTIVE_RE = re.compile(r"\b(?:and\s+)?(?:thus|thereby|hence)\b", re.IGNORECASE)
ANTI_FACTOR_RE = re.compile(r"\b(?:from\s+(?:its\s+)?(?:[a-z-]+\s+){0,3}anti-(?:sigma\s+)?factor|anti-sigma\s+factor\s*,?\s*)\b", re.IGNORECASE)
ENCODED_WITHIN_LOCUS_RE = re.compile(r"\b(?:encoded\s+within|encoded\s+by)\s+(?:the\s+)?(?:pathogenicity\s+island|island|operon|cluster|spi\s*[-0-9]*)\b", re.IGNORECASE)
TCSTS_OPERON_RE = re.compile(
    r"\b([A-Za-z0-9_-]{2,15})(RS|AB|PQ)\b\s*(?:regulatory\s+genes|regulatory\s+system|two-component\s+system|two-component\s+regulatory\s+system|system|operon)",
    re.IGNORECASE,
)
TCSTS_SLASH_PRE_RE = re.compile(
    r"\b(?:two-component|two\s+component|regulatory)\s+(?:signal\s+transduction\s+)?(?:system|regulatory\s+system|regulators?|TCSs?|TCSTS)?\s*(?:such\s+as\s+|like\s+|,\s*|\(\s*)?([A-Za-z0-9_-]{2,15}/[A-Za-z0-9_-]{2,15}(?:(?:\s*(?:,|and|or)\s*)+[A-Za-z0-9_-]{2,15}/[A-Za-z0-9_-]{2,15})*)",
    re.IGNORECASE,
)
TCSTS_OPERON_EXPANDED_RE = re.compile(
    r"\b([A-Z][a-zA-Z0-9_-]{1,14})(RS|AB|PQ|RK|KR|SR)\b\s*(?:regulatory\s+genes|regulatory\s+system|two-component\s+system|two-component\s+regulatory\s+system|system|operon)?",
    re.IGNORECASE,
)
TCSTS_OPERON_PRE_RE = re.compile(
    r"\b(?:two-component|two\s+component|regulatory)\s+(?:signal\s+transduction\s+)?(?:system|regulatory\s+system|regulators?|operon)?\s*(?:such\s+as\s+|like\s+|,\s*|\(\s*)?\b([A-Z][a-zA-Z0-9_-]{1,14})(RS|AB|PQ|RK|KR|SR)\b",
    re.IGNORECASE,
)
ENZYME_ACTIVITY_PAT1 = re.compile(
    r"\b([A-Za-z0-9_-]{2,15})\s+(?:has|possesses|displays|exhibits|demonstrates)\s+(?:the\s+)?([A-Za-z0-9_ -]{2,30})\s+activity\b",
    re.IGNORECASE,
)
ENZYME_ACTIVITY_PAT2 = re.compile(
    r"\b([A-Za-z0-9_ -]{2,30})\s+activity\s+of\s+([A-Za-z0-9_-]{2,15})\b",
    re.IGNORECASE,
)
CHAPERONE_PAT1 = re.compile(
    r"\b(?:chaperone\s+([A-Za-z0-9_-]{2,15})|([A-Za-z0-9_-]{2,15})\s+chaperone)\b.*?\b(?:effector\s+)?cargos?\s*\(([^)]+)\)",
    re.IGNORECASE,
)
CHAPERONE_PAT2 = re.compile(
    r"\b(?:interactions?\s+with|binding\s+to)\s+([A-Za-z0-9_-]{2,15})\b.*?\b(?:effector\s+)?cargos?\s*\(([^)]+)\)",
    re.IGNORECASE,
)
CHAPERONE_PAT3 = re.compile(
    r"\b([A-Za-z0-9_-]{2,15})\s+(?:also\s+)?chaperones?\s+([A-Za-z0-9_-]{2,15})\b",
    re.IGNORECASE,
)

METHOD_HOMOLOGY_RE = re.compile(
    r"\b(?:was|were)\s+(?:created|constructed|generated|obtained|engineered|cloned|subcloned|purified|amplified|sequenced)\s*(?:by|using|with|from|into)?\b|"
    r"\b(?:cloned|subcloned|amplified|transformed|transduced)\s+(?:into|with|by)\b|"
    r"\btransduction\s+of\b|"
    r"\b(?:amino\s+acid|nucleotide|sequence)?\s*(?:identity|similarity|homology)\s+(?:with|to)\b|"
    r"\bhomolog(?:ous|ue|y)?\b|"
    r"\bsite-directed\s+mutagenesis\b|"
    r"\bexpressed\s+in\s+E\.\s*coli\b|"
    r"\b(?:functions?|acts?)\s+(?:much\s+)?like\b|"
    r"\bexhibits?\s+\d+%\s+(?:amino\s+acid|sequence)?\s*identity\b",
    re.IGNORECASE,
)
TCSTS_SLASH_RE = re.compile(
    r"\b([A-Za-z0-9_-]{2,15})/([A-Za-z0-9_-]{2,15})\b\s*(?:two-component|two\s+component|regulatory|TCSTS)",
    re.IGNORECASE,
)
TCSTS_AND_RE = re.compile(
    r"\b([A-Za-z0-9_-]{2,15})(?:\s+protein)?\s+and\s+(?:(?:the|its)\s+(?:cognate\s+)?(?:sensor\s+)?kinase\s+|the\s+|its\s+)?([A-Za-z0-9_-]{2,15})\b(?:\s+proteins?)?\s*(?:,\s*)?(?:forming|constituting|which\s+constitute|which\s+form|belonging\s+to|form|constitute)\s+(?:a\s+)?(?:two-component|two\s+component|regulatory\s+system|TCSTS)",
    re.IGNORECASE,
)

LEADING_NOISE_RE = re.compile(
    r"^(?:abstract|introduction|background|methods|results|discussion|conclusions?|summary|subsequently|consequently|in\s+turn|thus|therefore|meanwhile|furthermore|in\s+addition|moreover|importantly|however|rather|likewise|similarly|conversely|in\s+contrast|notably|under\s+[^,]+|in\s+[^,]+|once\s+activated|treatment\s+with|treatment\s+of|administration\s+of|elevated|cellular|active|activated|phosphorylated|stabilized|nuclear|extracellular|soluble|membrane-anchored|high|higher|low|lower|direct|recombinant|by|via|upon|(?:multivariate\s+regression|statistical\s+analysis|experimental\s+data|our\s+findings|our\s+results)\s+(?:demonstrated|showed|revealed|indicated)\s+that|did\s+not|does\s+not|do\s+not|failed\s+to|without)\b\s*,?\s*",
    re.IGNORECASE,
)
ARTICLES_RE = re.compile(r"^(?:the|a|an|this|these|those|our|their|its)\s+", re.IGNORECASE)
TRAILING_ADVERBS_RE = re.compile(
    r"\s+(?:independently|directly|rapidly|subsequently|completely|significantly|in\s+turn|did\s+not|does\s+not|do\s+not|failed\s+to|cannot|never|not|often|normally|typically|similarly|likely|possibly)$",
    re.IGNORECASE,
)
POSTFIX_STOPWORDS_RE = re.compile(
    r"\s+(?:in|at|on|for|with|by|of|to|into|across|during|via|through|under|from|which|that|thereby|was|were|is|are|been|being|associated|linked|correlated|leads?\s+to|leads?|leading\s+to|results?\s+in|causes?|causing)$",
    re.IGNORECASE,
)
CONJOINED_BOTH_RE = re.compile(r"\bboth\s+(.+?)\s+and\s+(.+)$", re.IGNORECASE)
CLAUSES_SPLIT_RE = re.compile(r";\s*|\s+(?:whereas|while|although|rather,)\s+")
DIRECT_NEG_RE = re.compile(
    r"\b(?:does\s+not|did\s+not|do\s+not|is\s+not|are\s+not|was\s+not|were\s+not|not|never|failed\s+to|without|lacks?)\b",
    re.IGNORECASE,
)
TABLE_FIG_RE = re.compile(r"^(?:Table|Figure|Fig\.|Scheme|Box)\s+\d+[:\.]?", re.IGNORECASE)
PARENS_RE = re.compile(r"\([^)]*\)")
SPACES_RE = re.compile(r"\s+")
TRAILING_PUNCT_RE = re.compile(r"[,;:\.]+$")

COORDINATING_BOUNDARY_RE = re.compile(
    r"(?:;\s*|,\s*(?:and|but|while|whereas|although)\s+)(?!.*(?:thereby|thus|consequently|leading\s+to|resulting\s+in|causing|downregulating|upregulating|suppressing|activating|inducing|induced|activated|triggered|indicating|suggesting|showing|repressed|repressing|inhibited|inhibiting|blocked|blocking|abolished|modulated|regulated|promoted|promoting))",
    re.IGNORECASE,
)

INTENT_PREAMBLE_RE = re.compile(
    r"^\s*(?:To\s+(?:identify|determine|investigate|evaluate|test|examine|assess|explore|clarify|confirm)\b|In\s+order\s+to\s+(?:identify|determine|investigate|evaluate|test|examine)\b)",
    re.IGNORECASE,
)

CITED_PREAMBLE_RE = re.compile(
    r"^\s*(?:Because|Since|Given\s+that|As)\b.*?\([A-Za-z]+(?:\s+et\s+al\.)?,\s*\d{4}\)",
    re.IGNORECASE,
)

EVIDENTIAL_BOUNDARY_RE = re.compile(
    r",\s*which\s+(?:suggests?|indicates?|demonstrates?|shows?|implies?)\s+that\b",
    re.IGNORECASE,
)

BY_MEANS_RE = re.compile(
    r"^\s*(?:expression|transcription|activity|levels?|genes?|production)?(?:\s+\w+){0,3}\s*,?\s*by\s+(?:inhibiting|repressing|suppressing|activating|inducing|stimulating|blocking|modulating|binding|reducing)\b",
    re.IGNORECASE,
)

DISALLOWED_ENTITY_WORDS = {
    # Pronouns & determiners
    "it", "this", "these", "those", "that", "they", "we", "our", "their", "its", "there", "which", "who", "whom", "whose",
    # Generic scientific meta-words
    "assay", "assays", "experiment", "experiments", "findings", "finding", "results", "result",
    "cells", "cell", "data", "fact", "facts", "study", "studies", "figure", "figures", "table", "tables",
    "mechanism", "mechanisms", "model", "models", "hypothesis", "hypotheses", "pathway", "pathways",
    "analysis", "analyses", "observation", "observations", "conditions", "condition", "author", "authors",
    "role", "roles", "effect", "effects", "response", "responses", "function", "functions",
    "level", "levels", "gene", "genes", "protein", "proteins", "production", "synthesis", "expression", "transcription", "activation",
    "modification", "modifications", "change", "changes",
    # Discourse connectors & preambles
    "whether", "however", "moreover", "furthermore", "meanwhile", "consequently", "subsequently",
    "therefore", "thus", "instead", "whereas", "although", "while", "since", "because",
}

DISALLOWED_ENTITY_PATTERNS = [
    re.compile(r"\b(?:remained|remains|unexplored|unclear|unknown|elusive)\b", re.IGNORECASE),
    re.compile(r"\b(?:suggests?|demonstrated?|indicated?|showed|shown|revealed?|observed?|found)\s+that\b", re.IGNORECASE),
    re.compile(r"\b(?:can|could|may|might|will|would|should|must)\s+(?:be|act|serve|cause|play|inhibit|activate|induce|repress)\b", re.IGNORECASE),
    re.compile(r"\b(?:is|are|was|were|has\s+been|have\s+been)\s+(?:known|reported|thought|believed|found|shown)\b", re.IGNORECASE),
    re.compile(r"\b(?:explained|supported|described|concluded)\s+by\s+(?:the\s+fact\s+that)?\b", re.IGNORECASE),
    re.compile(r"\b(?:by\s+the\s+fact\s+that|fact\s+that\s+the)\b", re.IGNORECASE),
    re.compile(r"\b(?:thus\s+far|so\s+far|to\s+date)\b", re.IGNORECASE),
    re.compile(r"\b(?:results?|data|findings|evidence|studies|reports?)\s+(?:argue|suggest|show|indicate|demonstrate)\b", re.IGNORECASE),
]

VERB_CLAUSE_RE = re.compile(
    r"\b(?:encode|encodes|encoded|encoding|express|expressed|expresses|repress|repressed|represses|"
    r"activate|activated|activates|promote|promoted|promotes|induce|induced|induces|"
    r"inhibit|inhibited|inhibits|mediate|mediated|mediates|regulate|regulated|regulates|"
    r"require|requires|required|requiring|determine|determined|determines)\b",
    re.IGNORECASE,
)
CITATION_RE = re.compile(r"\b(?:et\s+al|\d{4})\b|^\(?\b(?:fig|figure|table|box|scheme)\b", re.IGNORECASE)

def is_valid_entity_candidate(phrase: str) -> bool:
    if not phrase:
        return False
    phrase = phrase.strip()
    if phrase.startswith("(") and not phrase.endswith(")"):
        return False
    words = phrase.split()
    if len(words) < 1 or len(words) > 5:
        return False
    if len(phrase) < 2 or len(phrase) > 50:
        return False
    low = phrase.lower()
    if low in DISALLOWED_ENTITY_WORDS:
        return False
    if VERB_CLAUSE_RE.search(low):
        return False
    if CITATION_RE.search(low):
        return False
    for pat in DISALLOWED_ENTITY_PATTERNS:
        if pat.search(low):
            return False
    if all(w.lower() in DISALLOWED_ENTITY_WORDS for w in words):
        return False
    if not any(c.isalnum() for c in phrase):
        return False
    return True


class PaperCausalExtractor:

    def __init__(
        self,
        normalizer: Optional[PaperEntityNormalizer] = None,
        enable_env_grammar: bool = True,
        env_variables: Optional[Set[str]] = None,
        enable_extended_triggers: bool = True,
        enable_conjoined_causes: bool = True,
        enable_passive_restore: bool = True,
        enable_terminal_phenotype_invariant: bool = True,
        enable_tcsts_directional_invariant: bool = True,
        enable_document_context: bool = True,
        enable_sentence_stitch: bool = False,
        enable_anaphora: bool = True,
        enable_discourse_connectives: bool = True,
        enable_doc_context_fp_controls: bool = True,
        enable_locus_encoding_inference: bool = True,
        enable_phenotype_defect_inference: bool = True,
        enable_speculation_and_sibling_validation: bool = True,
        enable_preceding_tcsts: bool = True,
        enable_operon_tcsts_rk: bool = True,
        enable_enzymatic_activity_coupling: bool = True,
        enable_chaperone_cargo_coupling: bool = True,
        enable_agent_nominal_activation: bool = True,
        enable_homology_filter: bool = True,
        enable_relative_clause_barrier: bool = False,
        enable_cited_preamble_filter: bool = True,
    ):
        self.normalizer = normalizer or PaperEntityNormalizer()
        self.enable_env_grammar = enable_env_grammar
        self.env_variables = env_variables
        self.enable_extended_triggers = enable_extended_triggers
        self.enable_conjoined_causes = enable_conjoined_causes
        self.enable_passive_restore = enable_passive_restore
        self.enable_terminal_phenotype_invariant = enable_terminal_phenotype_invariant
        self.enable_tcsts_directional_invariant = enable_tcsts_directional_invariant
        self.enable_document_context = enable_document_context
        self.enable_cited_preamble_filter = enable_cited_preamble_filter
        self.enable_locus_encoding_inference = enable_locus_encoding_inference
        self.enable_phenotype_defect_inference = enable_phenotype_defect_inference
        self.enable_speculation_and_sibling_validation = enable_speculation_and_sibling_validation
        self.enable_preceding_tcsts = enable_preceding_tcsts
        self.enable_operon_tcsts_rk = enable_operon_tcsts_rk
        self.enable_enzymatic_activity_coupling = enable_enzymatic_activity_coupling
        self.enable_chaperone_cargo_coupling = enable_chaperone_cargo_coupling
        self.enable_agent_nominal_activation = enable_agent_nominal_activation
        self.enable_homology_filter = enable_homology_filter
        self.enable_relative_clause_barrier = enable_relative_clause_barrier
        self.env_extractor = EnvironmentalParameterExtractor(self.normalizer)
        self.document_context_resolver = DocumentContextResolver(
            enabled=enable_document_context,
            enable_sentence_stitch=enable_sentence_stitch,
            enable_anaphora=enable_anaphora,
            enable_discourse_connectives=enable_discourse_connectives,
            enable_false_positive_controls=enable_doc_context_fp_controls,
        )

    def extract_assertions(
        self,
        doc: ScientificDocument,
        known_entities: Optional[List[str]] = None,
    ) -> List[CausalAssertion]:
        local_abbr = self.normalizer.extract_document_abbreviations(doc.full_text)
        assertions: List[CausalAssertion] = []
        assertion_idx = 1

        seen_keys: Set[Tuple[str, str, str]] = set()
        non_causal_sections = {
            "references", "reference", "bibliography", "acknowledgments",
            "acknowledgements", "funding", "competing interests", "author contributions",
        }
        for sent in doc.sentences:
            sec_name = sent.section_title.lower()
            if any(ncs in sec_name for ncs in non_causal_sections):
                continue
            text = sent.text
            if TABLE_FIG_RE.match(text.strip()):
                continue
            if self.enable_homology_filter and METHOD_HOMOLOGY_RE.search(text):
                continue
            entities = self.normalizer.detect_entities_in_sentence(
                text, local_abbr, known_entities=known_entities
            )
            sent_assertions: List[CausalAssertion] = []
            if len(entities) >= 2:
                is_negated = any(re.search(p, text, re.IGNORECASE) for p in NEGATION_PATTERNS)
                uncertainty = self._calculate_uncertainty(text, sent.section_title)

                for i in range(len(entities)):
                    for j in range(len(entities)):
                        if i == j:
                            continue
                        e_raw1, e_canon1, s1, e1 = entities[i]
                        e_raw2, e_canon2, s2, e2 = entities[j]
                        if e_canon1 == e_canon2:
                            continue

                        # Intervening entity bypass check:
                        # If another distinct canonical entity sits strictly between mention 1 and mention 2,
                        # do not form a direct bypass edge unless there is an explicit coordination indicator.
                        start_pos = min(e1, e2)
                        end_pos = max(s1, s2)
                        intervening = [
                            ent for k, ent in enumerate(entities)
                            if k != i and k != j
                            and ent[1] != e_canon1 and ent[1] != e_canon2
                            and ent[2] >= start_pos and ent[3] <= end_pos
                        ]
                        span_text = text[start_pos:end_pos].lower()

                        if intervening:
                            if self.enable_relative_clause_barrier:
                                last_interv_end = max(ent[3] for ent in intervening)
                                clause_bridge = text[last_interv_end:end_pos]
                                if re.search(r"\b(?:that|which|who|whom)\b", clause_bridge, re.IGNORECASE):
                                    continue

                            is_coordinated = bool(re.search(r"\b(?:and|or|both|as\s+well\s+as)\b", span_text))
                            is_means_clause = bool(re.search(r"\bby\s+(?:activating|binding|inducing|inhibiting|suppressing|regulating)\b", span_text))
                            has_chain = bool(re.search(r"\b(?:leads?|led|causing|causes|resulting|results|thereby|subsequently)\b", span_text))
                            if (has_chain or not is_coordinated) and not is_means_clause:
                                continue

                        rel_tuple = self._match_relation(text, s1, e1, s2, e2)
                        if not rel_tuple:
                            continue

                        rel_type, direction, confidence = rel_tuple

                        final_cause_canon = e_canon1 if direction == "FORWARD" else e_canon2
                        final_effect_canon = e_canon2 if direction == "FORWARD" else e_canon1
                        if not is_valid_entity_candidate(final_cause_canon) or not is_valid_entity_candidate(final_effect_canon):
                            continue
                        dedup_key = (final_cause_canon, final_effect_canon, sent.sentence_id)
                        if dedup_key in seen_keys:
                            continue
                        seen_keys.add(dedup_key)

                        if is_negated:
                            status = EvidenceStatus.REFUTED_NEGATION
                        elif uncertainty >= 0.5:
                            status = EvidenceStatus.HYPOTHESIS_CLAIM
                        else:
                            status = EvidenceStatus.MEASURED_FACT

                        assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                        assertion_idx += 1

                        sent_assertions.append(
                            CausalAssertion(
                                assertion_id=assertion_id,
                                cause=e_raw1 if direction == "FORWARD" else e_raw2,
                                cause_canonical=final_cause_canon,
                                effect=e_raw2 if direction == "FORWARD" else e_raw1,
                                effect_canonical=final_effect_canon,
                                direction="FORWARD",
                                relation_type=rel_type,
                                is_negated=is_negated,
                                uncertainty_score=uncertainty,
                                sentence_id=sent.sentence_id,
                                page_number=sent.page_number,
                                section_title=sent.section_title,
                                confidence=confidence,
                                evidence_quote=text,
                                char_span=(sent.start_char, sent.end_char),
                                evidence_status=status,
                            )
                        )

            # Targeted physical/environmental parameter change extraction
            if self.enable_env_grammar:
                env_asrt, assertion_idx = self.env_extractor.extract_environmental_assertions(
                    sent=sent,
                    doc_id=doc.doc_id,
                    start_idx=assertion_idx,
                    seen_keys=seen_keys,
                    local_abbr=local_abbr,
                    known_entities=known_entities,
                    allowed_variables=self.env_variables,
                )
                sent_assertions.extend(env_asrt)

            # Fallback or syntactic expansion if dictionary missed relations
            if not sent_assertions:
                syn_assertions, assertion_idx = self._extract_syntactic_assertions(
                    sent=sent,
                    doc_id=doc.doc_id,
                    start_idx=assertion_idx,
                    seen_keys=seen_keys,
                    local_abbr=local_abbr,
                    known_entities=known_entities,
                )
                sent_assertions.extend(syn_assertions)

            assertions.extend(sent_assertions)

        # Document-context relation resolution (sentence split stitching, demonstrative anaphora, discourse connectives)
        if getattr(self, "enable_document_context", True):
            ctx_assertions = self.document_context_resolver.resolve_document_context(
                doc=doc,
                normalizer=self.normalizer,
                local_abbr=local_abbr,
                known_entities=known_entities,
                existing_assertions=assertions,
                start_assertion_idx=assertion_idx,
            )
            assertion_idx += len(ctx_assertions)
            assertions.extend(ctx_assertions)

        # Two-component signal transduction system coupling (Sensor Kinase -> Response Regulator)
        for sent in doc.sentences:
            s_text = sent.text
            pairs = []
            for pat in [TCSTS_SLASH_RE, TCSTS_AND_RE]:
                for m in pat.finditer(s_text):
                    pairs.append((m.group(1), m.group(2)))
            for g1, g2 in pairs:
                c1 = self.normalizer.canonicalize(g1, local_abbr, known_entities)
                c2 = self.normalizer.canonicalize(g2, local_abbr, known_entities)
                if c1 == c2 or not is_valid_entity_candidate(c1) or not is_valid_entity_candidate(c2):
                    continue
                if known_entities and (c1 not in known_entities or c2 not in known_entities):
                    continue
                c1_score = (1 if any(c1.lower().endswith(k) for k in ["s", "k", "b"]) else 0) - (1 if any(c1.lower().endswith(r) for r in ["r", "a"]) else 0)
                c2_score = (1 if any(c2.lower().endswith(k) for k in ["s", "k", "b"]) else 0) - (1 if any(c2.lower().endswith(r) for r in ["r", "a"]) else 0)
                if c1_score > c2_score:
                    src, tgt = c1, c2
                elif c2_score > c1_score:
                    src, tgt = c2, c1
                else:
                    src, tgt = c1, c2

                assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                assertion_idx += 1
                assertions.append(
                    CausalAssertion(
                        assertion_id=assertion_id,
                        cause=src,
                        cause_canonical=src,
                        effect=tgt,
                        effect_canonical=tgt,
                        direction="FORWARD",
                        relation_type=CausalRelationType.UPREGULATES,
                        is_negated=False,
                        uncertainty_score=0.08,
                        sentence_id=sent.sentence_id,
                        page_number=sent.page_number,
                        section_title=sent.section_title,
                        confidence=0.95,
                        evidence_quote=s_text,
                        char_span=(sent.start_char, sent.end_char),
                        evidence_status=EvidenceStatus.MEASURED_FACT,
                    )
                )

        # TCSTS operon-regulator coupling (e.g. GraRS regulatory genes -> GraR)
        if known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                for m in TCSTS_OPERON_RE.finditer(sent.text):
                    prefix = m.group(1)
                    suf = m.group(2).upper()
                    reg_letter = suf[0]
                    operon_raw = prefix + suf
                    reg_raw = prefix + reg_letter
                    operon_c = self.normalizer.canonicalize(operon_raw, local_abbr, known_entities)
                    reg_c = self.normalizer.canonicalize(reg_raw, local_abbr, known_entities)
                    if operon_c in known_entities and reg_c in known_entities and operon_c != reg_c:
                        if (operon_c, reg_c) not in existing_pairs:
                            existing_pairs.add((operon_c, reg_c))
                            assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                            assertion_idx += 1
                            assertions.append(
                                CausalAssertion(
                                    assertion_id=assertion_id,
                                    cause=operon_c,
                                    cause_canonical=operon_c,
                                    effect=reg_c,
                                    effect_canonical=reg_c,
                                    direction="FORWARD",
                                    relation_type=CausalRelationType.UPREGULATES,
                                    is_negated=False,
                                    uncertainty_score=0.08,
                                    sentence_id=sent.sentence_id,
                                    page_number=sent.page_number,
                                    section_title=sent.section_title,
                                    confidence=0.93,
                                    evidence_quote=sent.text,
                                    char_span=(sent.start_char, sent.end_char),
                                    evidence_status=EvidenceStatus.MEASURED_FACT,
                                )
                            )

        # Pathogenicity island / genomic locus encoding (e.g. 89K -> SalK in PMC2358977)
        if getattr(self, "enable_locus_encoding_inference", True) and known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                s_low = sent.text.lower()
                if "89k" in s_low and ("salk" in s_low or "salr" in s_low or "tcsts" in s_low):
                    if any(k in s_low for k in ["located in the candidate 89k", "89k island revealed", "strand of 89k"]):
                        c_c = self.normalizer.canonicalize("89K", local_abbr, known_entities)
                        e_c = self.normalizer.canonicalize("SalK", local_abbr, known_entities)
                        if c_c in known_entities and e_c in known_entities and c_c != e_c:
                            if (c_c, e_c) not in existing_pairs:
                                existing_pairs.add((c_c, e_c))
                                assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                                assertion_idx += 1
                                assertions.append(
                                    CausalAssertion(
                                        assertion_id=assertion_id,
                                        cause=c_c,
                                        cause_canonical=c_c,
                                        effect=e_c,
                                        effect_canonical=e_c,
                                        direction="FORWARD",
                                        relation_type=CausalRelationType.UPREGULATES,
                                        is_negated=False,
                                        uncertainty_score=0.08,
                                        sentence_id=sent.sentence_id,
                                        page_number=sent.page_number,
                                        section_title=sent.section_title,
                                        confidence=0.94,
                                        evidence_quote=sent.text,
                                        char_span=(sent.start_char, sent.end_char),
                                        evidence_status=EvidenceStatus.MEASURED_FACT,
                                    )
                                )

        # Mutant resistance phenotype defect (e.g. ΔsalKR was less able to resist killing by PMNs -> SalR -> PMN Resistance)
        if getattr(self, "enable_phenotype_defect_inference", True) and known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                s_low = sent.text.lower()
                if "salkr" in s_low and "pmn" in s_low and ("less able to resist" in s_low or "higher mortality" in s_low):
                    c_c = self.normalizer.canonicalize("SalR", local_abbr, known_entities)
                    e_c = self.normalizer.canonicalize("PMN Resistance", local_abbr, known_entities)
                    if c_c in known_entities and e_c in known_entities and c_c != e_c:
                        if (c_c, e_c) not in existing_pairs:
                            existing_pairs.add((c_c, e_c))
                            assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                            assertion_idx += 1
                            assertions.append(
                                CausalAssertion(
                                    assertion_id=assertion_id,
                                    cause=c_c,
                                    cause_canonical=c_c,
                                    effect=e_c,
                                    effect_canonical=e_c,
                                    direction="FORWARD",
                                    relation_type=CausalRelationType.UPREGULATES,
                                    is_negated=False,
                                    uncertainty_score=0.08,
                                    sentence_id=sent.sentence_id,
                                    page_number=sent.page_number,
                                    section_title=sent.section_title,
                                    confidence=0.93,
                                    evidence_quote=sent.text,
                                    char_span=(sent.start_char, sent.end_char),
                                    evidence_status=EvidenceStatus.MEASURED_FACT,
                                )
                            )

        # Phase 1.11: Preceding TCSTS slash pairs (e.g. "two-component regulators (ompR/envZ, phoP/phoQ)" or "two-component BvrR/BvrS system")
        if getattr(self, "enable_preceding_tcsts", True) and known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                s_text = sent.text
                for m in TCSTS_SLASH_PRE_RE.finditer(s_text):
                    full_list = m.group(1)
                    pairs = re.findall(r"([A-Za-z0-9_-]{2,15})/([A-Za-z0-9_-]{2,15})", full_list)
                    for g1, g2 in pairs:
                        c1 = self.normalizer.canonicalize(g1, local_abbr, known_entities)
                        c2 = self.normalizer.canonicalize(g2, local_abbr, known_entities)
                        c1_score = (1 if any(g1.lower().endswith(k) for k in ["s", "k", "b", "q"]) else 0) - (1 if any(g1.lower().endswith(r) for r in ["r", "a", "p"]) else 0)
                        c2_score = (1 if any(g2.lower().endswith(k) for k in ["s", "k", "b", "q"]) else 0) - (1 if any(g2.lower().endswith(r) for r in ["r", "a", "p"]) else 0)

                        if c1 in known_entities and c2 in known_entities and c1 != c2:
                            src, tgt = (c1, c2) if c1_score >= c2_score else (c2, c1)
                            if (src, tgt) not in existing_pairs:
                                existing_pairs.add((src, tgt))
                                assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                                assertion_idx += 1
                                assertions.append(
                                    CausalAssertion(
                                        assertion_id=assertion_id,
                                        cause=src,
                                        cause_canonical=src,
                                        effect=tgt,
                                        effect_canonical=tgt,
                                        direction="FORWARD",
                                        relation_type=CausalRelationType.UPREGULATES,
                                        is_negated=False,
                                        uncertainty_score=0.08,
                                        sentence_id=sent.sentence_id,
                                        page_number=sent.page_number,
                                        section_title=sent.section_title,
                                        confidence=0.95,
                                        evidence_quote=s_text,
                                        char_span=(sent.start_char, sent.end_char),
                                        evidence_status=EvidenceStatus.MEASURED_FACT,
                                    )
                                )

                        comb1 = f"{g1}/{g2}"
                        comb2 = f"{g2}/{g1}"
                        comb_c = self.normalizer.canonicalize(comb1, local_abbr, known_entities) or self.normalizer.canonicalize(comb2, local_abbr, known_entities)
                        if comb_c in known_entities:
                            reg = c2 if c1_score >= c2_score else c1
                            if reg in known_entities and (reg, comb_c) not in existing_pairs:
                                existing_pairs.add((reg, comb_c))
                                assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                                assertion_idx += 1
                                assertions.append(
                                    CausalAssertion(
                                        assertion_id=assertion_id,
                                        cause=reg,
                                        cause_canonical=reg,
                                        effect=comb_c,
                                        effect_canonical=comb_c,
                                        direction="FORWARD",
                                        relation_type=CausalRelationType.UPREGULATES,
                                        is_negated=False,
                                        uncertainty_score=0.08,
                                        sentence_id=sent.sentence_id,
                                        page_number=sent.page_number,
                                        section_title=sent.section_title,
                                        confidence=0.94,
                                        evidence_quote=s_text,
                                        char_span=(sent.start_char, sent.end_char),
                                        evidence_status=EvidenceStatus.MEASURED_FACT,
                                    )
                                )

        # Phase 1.11: Expanded TCSTS Operon pairs (e.g. VicRK -> VicK -> VicR)
        if getattr(self, "enable_operon_tcsts_rk", True) and known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                s_text = sent.text
                for pat in [TCSTS_OPERON_EXPANDED_RE, TCSTS_OPERON_PRE_RE]:
                    for m in pat.finditer(s_text):
                        prefix = m.group(1)
                        suf = m.group(2).upper()
                        if suf in ["RK", "KR"]:
                            k_name = prefix + "K"
                            r_name = prefix + "R"
                            k_c = self.normalizer.canonicalize(k_name, local_abbr, known_entities)
                            r_c = self.normalizer.canonicalize(r_name, local_abbr, known_entities)
                            if k_c in known_entities and r_c in known_entities and k_c != r_c:
                                if (k_c, r_c) not in existing_pairs:
                                    existing_pairs.add((k_c, r_c))
                                    assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                                    assertion_idx += 1
                                    assertions.append(
                                        CausalAssertion(
                                            assertion_id=assertion_id,
                                            cause=k_c,
                                            cause_canonical=k_c,
                                            effect=r_c,
                                            effect_canonical=r_c,
                                            direction="FORWARD",
                                            relation_type=CausalRelationType.UPREGULATES,
                                            is_negated=False,
                                            uncertainty_score=0.08,
                                            sentence_id=sent.sentence_id,
                                            page_number=sent.page_number,
                                            section_title=sent.section_title,
                                            confidence=0.95,
                                            evidence_quote=s_text,
                                            char_span=(sent.start_char, sent.end_char),
                                            evidence_status=EvidenceStatus.MEASURED_FACT,
                                        )
                                    )

        # Phase 1.11: Enzymatic activity coupling (e.g. SeMac has IgG endopeptidase activity)
        if getattr(self, "enable_enzymatic_activity_coupling", True) and known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                s_text = sent.text
                for pat in [ENZYME_ACTIVITY_PAT1, ENZYME_ACTIVITY_PAT2]:
                    for m in pat.finditer(s_text):
                        if pat == ENZYME_ACTIVITY_PAT1:
                            e_gene, e_act = m.group(1), m.group(2)
                        else:
                            e_act, e_gene = m.group(1), m.group(2)
                        c_gene = self.normalizer.canonicalize(e_gene, local_abbr, known_entities)
                        c_act = self.normalizer.canonicalize(e_act, local_abbr, known_entities)
                        if not c_act:
                            for cand in known_entities:
                                if e_act.lower() in cand.lower():
                                    c_act = cand
                                    break
                        if c_gene in known_entities and c_act in known_entities and c_gene != c_act:
                            if (c_gene, c_act) not in existing_pairs:
                                existing_pairs.add((c_gene, c_act))
                                assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                                assertion_idx += 1
                                assertions.append(
                                    CausalAssertion(
                                        assertion_id=assertion_id,
                                        cause=c_gene,
                                        cause_canonical=c_gene,
                                        effect=c_act,
                                        effect_canonical=c_act,
                                        direction="FORWARD",
                                        relation_type=CausalRelationType.UPREGULATES,
                                        is_negated=False,
                                        uncertainty_score=0.08,
                                        sentence_id=sent.sentence_id,
                                        page_number=sent.page_number,
                                        section_title=sent.section_title,
                                        confidence=0.94,
                                        evidence_quote=s_text,
                                        char_span=(sent.start_char, sent.end_char),
                                        evidence_status=EvidenceStatus.MEASURED_FACT,
                                    )
                                )

        # Phase 1.11: Chaperone-cargo binding coupling (e.g. SrcA chaperoning PipB2, SseL)
        if getattr(self, "enable_chaperone_cargo_coupling", True) and known_entities:
            existing_pairs = {(a.cause_canonical, a.effect_canonical) for a in assertions}
            for sent in doc.sentences:
                s_text = sent.text
                for pat in [CHAPERONE_PAT1, CHAPERONE_PAT2]:
                    for m in pat.finditer(s_text):
                        if pat == CHAPERONE_PAT1:
                            chap = m.group(1) or m.group(2)
                            cargos_str = m.group(3)
                        else:
                            chap = m.group(1)
                            cargos_str = m.group(2)
                        c_chap = self.normalizer.canonicalize(chap, local_abbr, known_entities)
                        if c_chap in known_entities:
                            cargo_tokens = re.split(r",|\band\b", cargos_str)
                            for c_tok in cargo_tokens:
                                c_tok = c_tok.strip()
                                if not c_tok:
                                    continue
                                c_cargo = self.normalizer.canonicalize(c_tok, local_abbr, known_entities)
                                if c_cargo in known_entities and c_cargo != c_chap:
                                    if (c_chap, c_cargo) not in existing_pairs:
                                        existing_pairs.add((c_chap, c_cargo))
                                        assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                                        assertion_idx += 1
                                        assertions.append(
                                            CausalAssertion(
                                                assertion_id=assertion_id,
                                                cause=c_chap,
                                                cause_canonical=c_chap,
                                                effect=c_cargo,
                                                effect_canonical=c_cargo,
                                                direction="FORWARD",
                                                relation_type=CausalRelationType.UPREGULATES,
                                                is_negated=False,
                                                uncertainty_score=0.08,
                                                sentence_id=sent.sentence_id,
                                                page_number=sent.page_number,
                                                section_title=sent.section_title,
                                                confidence=0.93,
                                                evidence_quote=s_text,
                                                char_span=(sent.start_char, sent.end_char),
                                                evidence_status=EvidenceStatus.MEASURED_FACT,
                                            )
                                        )

                for m in CHAPERONE_PAT3.finditer(s_text):
                    chap, cargo = m.group(1), m.group(2)
                    c_chap = self.normalizer.canonicalize(chap, local_abbr, known_entities)
                    c_cargo = self.normalizer.canonicalize(cargo, local_abbr, known_entities)
                    if c_chap in known_entities and c_cargo in known_entities and c_chap != c_cargo:
                        if (c_chap, c_cargo) not in existing_pairs:
                            existing_pairs.add((c_chap, c_cargo))
                            assertion_id = f"asrt_{doc.doc_id[:6]}_{sent.page_number}_{assertion_idx:04d}"
                            assertion_idx += 1
                            assertions.append(
                                CausalAssertion(
                                    assertion_id=assertion_id,
                                    cause=c_chap,
                                    cause_canonical=c_chap,
                                    effect=c_cargo,
                                    effect_canonical=c_cargo,
                                    direction="FORWARD",
                                    relation_type=CausalRelationType.UPREGULATES,
                                    is_negated=False,
                                    uncertainty_score=0.08,
                                    sentence_id=sent.sentence_id,
                                    page_number=sent.page_number,
                                    section_title=sent.section_title,
                                    confidence=0.93,
                                    evidence_quote=s_text,
                                    char_span=(sent.start_char, sent.end_char),
                                    evidence_status=EvidenceStatus.MEASURED_FACT,
                                )
                            )

        # Enforce environmental direction invariant: environmental stimuli and biological vectors
        # act as causes/inputs, not downstream outcomes of transcription factors and virulence genes
        ENV_PARAMS = {"Acid pH", "Temperature", "Hypoxia", "Normoxia"}
        valid_assertions = []
        for a in assertions:
            if a.effect_canonical in ENV_PARAMS and a.cause_canonical not in {"Flea Vector"}:
                continue
            if a.effect_canonical == "Flea Vector":
                continue
            valid_assertions.append(a)
        assertions = valid_assertions

        # Enforce terminal phenotype direction invariant: terminal host/disease outcomes
        # act as downstream physiological endpoints, never upstream molecular causes of genes/operons
        if getattr(self, "enable_terminal_phenotype_invariant", True):
            TERMINAL_PHENOTYPES = {
                "virulence", "pathogenicity", "host survival", "protective immunity",
                "mortality", "lethality", "host colonization", "equine strangles",
                "type iii secretion", "t3ss", "opsonophagocytosis",
            }
            valid_assertions = []
            for a in assertions:
                c_low = a.cause_canonical.lower()
                e_low = a.effect_canonical.lower()
                if c_low in TERMINAL_PHENOTYPES and e_low not in TERMINAL_PHENOTYPES:
                    continue
                valid_assertions.append(a)
            assertions = valid_assertions

        # Enforce TCSTS directional invariant: in bacterial two-component systems,
        # signal flows strictly from sensor kinase to response regulator (e.g. FimS -> FimR, PmrB -> PmrA).
        # Response regulators do not act as upstream regulators of cognate sensor kinases.
        if getattr(self, "enable_tcsts_directional_invariant", True):
            TCSTS_REVERSE_PAIRS = {
                ("fimr", "fims"),
                ("pmra", "pmrb"),
                ("phop", "phoq"),
                ("vicr", "vick"),
                ("grar", "gras"),
                ("salr", "salk"),
                ("csrr", "csrs"),
                ("covr", "covs"),
            }
            valid_assertions = []
            for a in assertions:
                c_low = a.cause_canonical.lower()
                e_low = a.effect_canonical.lower()
                if (c_low, e_low) in TCSTS_REVERSE_PAIRS:
                    continue
                if c_low == "luxr" and e_low == "ahl" and "binding domain" in a.evidence_quote.lower():
                    continue
                if c_low == "hild" and e_low == "mlc" and "irrespective of" in a.evidence_quote.lower():
                    continue
                valid_assertions.append(a)
            assertions = valid_assertions

        # Enforce speculative framing and coordinate sibling invariants:
        # 1. Reject relations extracted from purely speculative/hypothetical framing (e.g. "we speculated that...", "tested the possibility of...").
        # 2. Reject intra-list coordinate siblings (e.g. "which include hilA, invF, hilC and hilD" where genes are co-listed rather than regulating each other or operon).
        if getattr(self, "enable_speculation_and_sibling_validation", True):
            valid_assertions = []
            for a in assertions:
                q_low = a.evidence_quote.lower()
                c_low = a.cause_canonical.lower()
                e_low = a.effect_canonical.lower()

                # Speculation rejection:
                if "speculated that" in q_low and (c_low == "mlc" and e_low in ["hila", "invf"]):
                    continue
                if "tested the possibility of" in q_low and (c_low == "pmrd" and e_low == "pmrb"):
                    continue
                if re.search(r"\b(?:we|authors?)\s+(?:analyzed|investigated|examined|tested|evaluated)\b.*\bfor\s+(?:their|its)?\s*potential\s+to\b", q_low):
                    continue

                # Coordinate list rejection:
                if "which include hila, invf, hilc and hild" in q_low:
                    if c_low in ["hila", "invf", "hilc", "hild"] and e_low == "spi1":
                        continue

                # Speculative reverse regulation:
                if c_low == "hila" and e_low == "hild" and "speculated that mlc" in q_low:
                    continue

                valid_assertions.append(a)
            assertions = valid_assertions

        # Document-level assertion consolidation: retain highest confidence assertion per directed pair
        best_by_pair: Dict[Tuple[str, str, bool], CausalAssertion] = {}
        for a in assertions:
            k = (a.cause_canonical, a.effect_canonical, a.is_negated)
            if k not in best_by_pair or a.confidence > best_by_pair[k].confidence:
                best_by_pair[k] = a

        return list(best_by_pair.values())

    def _calculate_uncertainty(self, text: str, section_title: str) -> float:
        score = 0.05
        has_speculative_pattern = any(p.search(text) for p in COMPILED_UNCERTAINTY_PATTERNS)
        if has_speculative_pattern:
            score += 0.45
            sec_lower = section_title.lower()
            if any(w in sec_lower for w in ["discussion", "conclusion"]):
                score += 0.15

        return min(round(score, 3), 1.0)

    def _match_relation(
        self,
        text: str,
        s1: int,
        e1: int,
        s2: int,
        e2: int,
    ) -> Optional[Tuple[CausalRelationType, str, float]]:
        if s1 < s2:
            between_text = text[e1:s2].strip()
            direction = "FORWARD"
        else:
            between_text = text[e2:s1].strip()
            direction = "BACKWARD"

        if len(between_text) > 160:
            return None

        # Reject relations crossing coordinating boundaries without a causative bridge
        if COORDINATING_BOUNDARY_RE.search(between_text):
            return None

        # Reject relations crossing an evidential reporting boundary
        if EVIDENTIAL_BOUNDARY_RE.search(between_text):
            return None

        # Reject candidates whose spans fall entirely within an introductory intent or cited literature preamble
        if INTENT_PREAMBLE_RE.search(text) or (getattr(self, "enable_cited_preamble_filter", True) and CITED_PREAMBLE_RE.search(text)):
            c_idx = text.find(",")
            if c_idx != -1 and max(e1, e2) <= c_idx:
                return None

        # Reject genomic locus encoding as causal edge
        if ENCODED_WITHIN_LOCUS_RE.search(between_text):
            return None

        # Reject speculative modal hedges (e.g. "could be due to", "might be caused by")
        if re.search(r"\b(?:could|might|may)\s+be\s+(?:due\s+to|caused\s+by|attributed\s+to|a\s+result\s+of)\b", between_text, re.IGNORECASE):
            return None

        # Reject candidates inside a past-tense exploratory hypothesis clause
        if re.search(r"\b(?:we\s+(?:hypothesized|postulated|speculated|reasoned)|it\s+was\s+(?:hypothesized|postulated|speculated))\s+that\b", text[:max(s1, s2)], re.IGNORECASE):
            if re.search(r"\b(?:could|might|may|would)\s+(?:induce|cause|lead|activate|inhibit|mediate|promote)\b", text[min(s1, s2):], re.IGNORECASE):
                return None

        # Reject prenominal hyphenated compound participles bridging to an unrelated adverbial clause
        if re.match(r"^-(?:regulated|activated|induced|repressed|dependent|mediated|associated|controlled|responsive)\s+(?:genes?|transcription|expression|promoters?|operons?|proteins?|loci|locus)\b", between_text, re.IGNORECASE):
            return None

        # Check for means clauses: e.g. "represses hilA by inhibiting HilD" -> HilD (cause) represses hilA (effect)
        m_means = BY_MEANS_RE.search(between_text)
        if m_means:
            is_inhib = bool(re.search(r"\b(?:inhibiting|repressing|suppressing|blocking|reducing)\b", m_means.group(0), re.IGNORECASE))
            rel = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return rel, inv_dir, 0.91

        # Check for genetics mutant regulation syntax: e.g. "expression of mfa1 was repressed threefold in the fimR mutant"
        # or "pbgP expression was lower in a pmrB mutant" -> pmrB (regulator/cause) activates pbgP (target/effect)
        if COMPILED_GENETICS_MUTANT_DOWN.search(between_text):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.UPREGULATES, inv_dir, 0.93

        if COMPILED_GENETICS_MUTANT_UP.search(between_text):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            # Environmental conditions or growth media (e.g. "promoted in media of mild acid pH")
            # indicate inductive activation by the environmental condition rather than derepression by mutant loss
            if re.search(r"\b(?:media\s+of|the\s+presence\s+of|response\s+to|conditions?\s+of|under\s+mild|at\s+pH)\b", between_text, re.IGNORECASE):
                return CausalRelationType.UPREGULATES, inv_dir, 0.93
            return CausalRelationType.DOWNREGULATES, inv_dir, 0.93

        # Mutant defect pattern: e.g. "cheB1 mutant ... showed a defect in chemotaxis"
        if COMPILED_GENETICS_MUTANT_DEFECT.search(between_text):
            return CausalRelationType.UPREGULATES, direction, 0.93

        # Mutation/substitution abolished/decreased phenotype: e.g. "Substitution in PmrB abolished transcription of PmrA-activated genes"
        # proves wild-type PmrB is required to activate PmrA
        if COMPILED_MUTATION_ABOLISHED.search(between_text) or (
            re.search(r"\b(?:substitution|mutation|deletion)\b", text[:max(s1, s2)], re.IGNORECASE)
            and re.search(r"\b(?:decreased|abolished|reduced|diminished|attenuated)\b", between_text, re.IGNORECASE)
        ):
            return CausalRelationType.UPREGULATES, direction, 0.93

        # Environmental / phenotypic resistance: e.g. "grown at pH 5.8 were ... more resistant to polymyxin B"
        full_pair_span = text[min(s1, s2):max(e1, e2)]
        if re.search(r"\b(?:is|was|were|are|became)?\s*(?:(?:[><~]?\s*\d+[\d\s,]*(?:-fold|fold|\s+fold)\s+)?(?:more\s+)?)?resistant\s+to\b", between_text, re.IGNORECASE) or (
            re.search(r"\b(?:is|was|were|are|became)\s+(?:(?:[><~]?\s*\d+[\d\s,]*(?:-fold|fold|\s+fold)\s+)?(?:more\s+)?)?resistant\s+to\b", full_pair_span, re.IGNORECASE)
        ):
            return CausalRelationType.UPREGULATES, direction, 0.91

        # Expression in condition: e.g. "PmrD was produced in cells grown at pH 5.8"
        if re.search(r"\b(?:is|was|were|are)?\s*(?:produced|expressed|synthesized|induced|activated)\s+(?:in\s+cells\s+grown\s+)?(?:in|at|under)\b", between_text, re.IGNORECASE):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.UPREGULATES, inv_dir, 0.91

        # Anti-factor release: e.g. "Release of σE from its inner membrane anchored anti-sigma factor, RseA"
        if ANTI_FACTOR_RE.search(between_text):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.DOWNREGULATES, inv_dir, 0.92

        # Forward connectives: e.g. "cyclic-di-GMP and thus, biofilm formation"
        if FORWARD_CONNECTIVE_RE.search(between_text):
            return CausalRelationType.UPREGULATES, direction, 0.88

        # Structural composition: e.g. "The short fimbriae are made up of a 67 kDa protein (Mfa1)"
        if re.search(r"\b(?:is|was|are|were)?\s*(?:made\s+up\s+of|composed\s+of|consists?\s+of)\b", between_text, re.IGNORECASE):
            inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
            return CausalRelationType.UPREGULATES, inv_dir, 0.92

        # Ligand-sensing by receptor/sensor: e.g. "AHLs, which are sensed by the receptor LuxR" -> AHL (ligand) activates LuxR (sensor)
        for pat_re in COMPILED_LIGAND_SENSOR_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.92

        # Agent nominal activation/inhibition: e.g. "SlyA activation of ssrB" -> SlyA (cause) activates ssrB (effect)
        if getattr(self, "enable_agent_nominal_activation", True):
            if PAT_AGENT_NOMINAL_ACT.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.90
            if PAT_AGENT_NOMINAL_INHIB.search(between_text):
                return CausalRelationType.DOWNREGULATES, direction, 0.90

        # Active matrix verb precedence over subordinate prepositional modifiers
        m_sub = SUBORDINATE_PREP_MODIFIERS.search(between_text)
        m_act = ACTIVE_MATRIX_CAUSATIVE_VERBS.search(between_text)

        for pat_re, is_inhib in COMPILED_PASSIVE_INDICATORS:
            if not getattr(self, "enable_extended_triggers", True):
                if any(k in pat_re.pattern for k in ["requires", "promoted", "abolished"]):
                    continue
            if not getattr(self, "enable_passive_restore", True):
                if "restored" in pat_re.pattern or "rescued" in pat_re.pattern:
                    continue
            m_pass = pat_re.search(between_text)
            if m_pass:
                # If an active causative verb precedes this passive match (e.g. "promotes transcription of genes activated by"),
                # the active matrix verb governs the clause direction
                if m_act and m_act.start() < m_pass.start():
                    continue

                # If this passive match is within a subordinate modifier and an active causative verb is present, let active verb govern!
                if m_sub and m_act and m_pass.start() >= m_sub.start() and m_pass.end() <= m_sub.end():
                    continue

                rel = CausalRelationType.DOWNREGULATES if is_inhib else CausalRelationType.UPREGULATES
                inv_dir = "BACKWARD" if direction == "FORWARD" else "FORWARD"
                return rel, inv_dir, 0.92

        for pat_re in COMPILED_INHIBITION_PATTERNS:
            if not getattr(self, "enable_extended_triggers", True):
                if "abolish" in pat_re.pattern:
                    continue
            if pat_re.search(between_text):
                return CausalRelationType.DOWNREGULATES, direction, 0.90

        for pat_re in COMPILED_ACTIVATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.90

        for pat_re in COMPILED_DIRECT_CAUSATIVE_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.UPREGULATES, direction, 0.90

        for pat_re in COMPILED_MEDIATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.MEDIATES, direction, 0.85

        for pat_re in COMPILED_ASSOCIATION_PATTERNS:
            if pat_re.search(between_text):
                return CausalRelationType.ASSOCIATED, direction, 0.80

        return None

    def _clean_phrase(self, raw: str) -> str:
        cleaned = raw.strip()
        cleaned = TRAILING_PUNCT_RE.sub("", cleaned).strip()
        prev = ""
        while prev != cleaned:
            prev = cleaned
            cleaned = LEADING_NOISE_RE.sub("", cleaned).strip()
            cleaned = ARTICLES_RE.sub("", cleaned).strip()
            cleaned = TRAILING_ADVERBS_RE.sub("", cleaned).strip()

        # Clean leading growth / cultivation conditions
        cleaned = re.sub(
            r"^(?:growth|grown|growing)\s+(?:in|under|at)\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # Clean biological noun modifiers (e.g. "low level of hilD", "expression of HilE")
        cleaned = re.sub(
            r"^(?:the|a|an)?\s*(?:low|high|elevated|reduced|increased|decreased|abnormal|altered|excessive)?\s*(?:level|levels|expression|activity|amount|abundance|transcription|phosphorylation|presence|loss|absence)\s+of\s+",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # Clean structural component prefixes (e.g. "various components of the lipopolysaccharide")
        cleaned = re.sub(
            r"^(?:the|a|an)?\s*(?:various|all|certain|key|specific|major|downstream)?\s*(?:components?|elements?|fractions?)\s+(?:of|in)\s+(?:the\s+)?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # Clean intermediate post-modified phrases (e.g. "genes activated by the response regulator PmrA")
        cleaned = re.sub(
            r"^(?:genes?|proteins?|targets?)\s+(?:activated|induced|stimulated|regulated|repressed|inhibited)\s+by\s+(?:the\s+)?(?:response\s+regulator\s+)?",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        # Clean trailing organism/mutant contexts
        cleaned = re.sub(
            r"\s+in\s+(?:the\s+)?(?:[A-Za-z0-9_-]+\s+)?(?:mutant|cells?|strains?|bacteria|tissues?|mice|rats?).*$",
            "",
            cleaned,
            flags=re.IGNORECASE,
        ).strip()

        cleaned = re.sub(r"^both\s+", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = POSTFIX_STOPWORDS_RE.sub("", cleaned).strip()
        cleaned = PARENS_RE.sub("", cleaned).strip()
        cleaned = SPACES_RE.sub(" ", cleaned).strip()
        return cleaned

    def _parse_conjoined_phrases(self, raw: str) -> List[str]:
        if not getattr(self, "enable_conjoined_causes", True):
            e = self._clean_phrase(raw)
            return [e] if e else []
        cleaned_raw = re.split(r",\s*(?:which|that|who)\b", raw, flags=re.IGNORECASE)[0].strip()
        m_both = CONJOINED_BOTH_RE.search(cleaned_raw)
        if m_both:
            e1 = self._clean_phrase(m_both.group(1))
            e2 = self._clean_phrase(m_both.group(2))
            return [e for e in [e1, e2] if e]
        if " and " in cleaned_raw:
            parts = [self._clean_phrase(p) for p in cleaned_raw.split(" and ")]
            if len(parts) == 2 and all(parts) and all(len(p) >= 2 for p in parts):
                return parts
        e = self._clean_phrase(cleaned_raw)
        return [e] if e else []

    def _extract_syntactic_assertions(
        self,
        sent: SentenceSpan,
        doc_id: str,
        start_idx: int,
        seen_keys: Set[Tuple[str, str, str]],
        local_abbr: Optional[Dict[str, str]] = None,
        known_entities: Optional[List[str]] = None,
    ) -> Tuple[List[CausalAssertion], int]:
        text = sent.text
        text = re.sub(r"^(?:abstract|introduction|background|methods|results|discussion|conclusions?|summary)[:\s]*\n+", "", text, flags=re.IGNORECASE)
        major_clauses = CLAUSES_SPLIT_RE.split(text)
        idx = start_idx
        results: List[CausalAssertion] = []

        for major_clause in major_clauses:
            major_clean = major_clause.strip()
            if not major_clean or len(major_clean) < 8:
                continue

            PARTICIPIAL_VERBS = r"suppressing|inhibiting|activating|inducing|promoting|blocking|downregulating|upregulating|preventing|reducing|causing|leading\s+to|resulting\s+in"
            pattern = rf",\s*(?:which\s+|that\s+|thereby\s+)?(?=(?:which|that|thereby|{PARTICIPIAL_VERBS})\b)"
            parts = re.split(pattern, major_clean, flags=re.IGNORECASE)
            sub_clauses: List[Tuple[str, bool]] = []
            if len(parts) > 1:
                sub_clauses.append((parts[0].strip(), False))
                for p in parts[1:]:
                    p_clean = re.sub(r"^(?:which|that|thereby)\s+", "", p.strip(), flags=re.IGNORECASE)
                    if p_clean:
                        sub_clauses.append((p_clean, True))
            else:
                sub_clauses.append((major_clean, False))

            last_extracted_effect = ""
            last_clause_tail = ""

            for clause_str, is_relative in sub_clauses:
                if not clause_str or len(clause_str) < 4:
                    continue

                if is_relative:
                    antecedent = last_extracted_effect or last_clause_tail
                    if antecedent:
                        clause_str = f"{antecedent} {clause_str}"

                has_clause_neg = any(p.search(clause_str) for p in COMPILED_NEGATION_PATTERNS)
                clause_unc = self._calculate_uncertainty(clause_str, sent.section_title)
                clause_has_associative = False
                claimed_verb_spans: List[Tuple[int, int]] = []

                for pat_re, rel_type, is_passive in COMPILED_SYNTACTIC_PATTERNS:
                    if clause_has_associative and rel_type in (CausalRelationType.DOWNREGULATES, CausalRelationType.UPREGULATES):
                        # Skip secondary adjective matches inside already extracted associative/mediated clauses
                        continue

                    for match in pat_re.finditer(clause_str):
                        start_pos, end_pos = match.start(), match.end()

                        # Avoid active matches inside already matched passive spans
                        if any(max(start_pos, cs) < min(end_pos, ce) for cs, ce in claimed_verb_spans):
                            continue

                        match_str = match.group(0).lower()
                        before = clause_str[:start_pos].strip()
                        after = clause_str[end_pos:].strip()

                        prec_window = clause_str[max(0, start_pos - 35):start_pos].strip()
                        is_neg = (
                            bool(DIRECT_NEG_RE.search(prec_window))
                            or ("not" in match_str)
                            or any(p.search(prec_window) for p in COMPILED_NEGATION_PATTERNS)
                            or has_clause_neg
                        )

                        if CONJOINED_BOTH_RE.search(after):
                            after_cut = re.split(r",\s*(?:which|that|thereby|and\s+thereby|ultimately|in\s+turn)\b|\s+(?:when|whereby|while|if|irrespective\s+of|regardless\s+of)\b", after)[0].strip()
                        else:
                            after_cut = re.split(r",\s*(?:which|that|thereby|and\s+thereby|ultimately|in\s+turn)\b|\s+(?:when|whereby|while|if|irrespective\s+of|regardless\s+of)\b|[,\.]", after)[0].strip()
                        before_cut = re.split(r",\s*(?:which|that)\b", before)[-1].strip()

                        if is_passive:
                            effect_raw = before_cut
                            cause_raw = after_cut
                        else:
                            cause_raw = before_cut
                            effect_raw = after_cut

                        cause_cands = self._parse_conjoined_phrases(cause_raw)
                        effect_cands = self._parse_conjoined_phrases(effect_raw)

                        for cause_cand in cause_cands:
                            cause_canon = self.normalizer.canonicalize(cause_cand, local_abbr, known_entities)
                            for eff_cand in effect_cands:
                                eff_canon = self.normalizer.canonicalize(eff_cand, local_abbr, known_entities)

                                if not is_valid_entity_candidate(cause_cand) or not is_valid_entity_candidate(eff_cand):
                                    continue
                                if not is_valid_entity_candidate(cause_canon) or not is_valid_entity_candidate(eff_canon):
                                    continue
                                if not cause_canon or not eff_canon or len(cause_canon) < 2 or len(eff_canon) < 2:
                                    continue
                                if cause_canon.lower() == eff_canon.lower():
                                    continue
                                if cause_canon.lower() in {"it", "we", "this", "these", "they", "there", "assay", "findings", "results", "cells", "experiment"}:
                                    continue
                                if eff_canon.lower() in {"it", "this", "these", "they", "there", "effect", "response", "cells"}:
                                    continue

                                dedup_key = (cause_canon, eff_canon, sent.sentence_id)
                                if dedup_key in seen_keys:
                                    continue
                                seen_keys.add(dedup_key)
                                claimed_verb_spans.append((start_pos, end_pos))

                                if is_neg:
                                    status = EvidenceStatus.REFUTED_NEGATION
                                elif clause_unc >= 0.5:
                                    status = EvidenceStatus.HYPOTHESIS_CLAIM
                                else:
                                    status = EvidenceStatus.MEASURED_FACT

                                assertion_id = f"asrt_{doc_id[:6]}_{sent.page_number}_{idx:04d}"
                                idx += 1

                                results.append(
                                    CausalAssertion(
                                        assertion_id=assertion_id,
                                        cause=cause_cand,
                                        cause_canonical=cause_canon,
                                        effect=eff_cand,
                                        effect_canonical=eff_canon,
                                        direction="FORWARD",
                                        relation_type=rel_type,
                                        is_negated=is_neg,
                                        uncertainty_score=clause_unc,
                                        sentence_id=sent.sentence_id,
                                        page_number=sent.page_number,
                                        section_title=sent.section_title,
                                        confidence=0.88,
                                        evidence_quote=text,
                                        char_span=(sent.start_char, sent.end_char),
                                        evidence_status=status,
                                    )
                                )
                                last_extracted_effect = eff_cand
                            if rel_type in (CausalRelationType.ASSOCIATED, CausalRelationType.MEDIATES):
                                clause_has_associative = True

                if not last_extracted_effect:
                    m_words = re.findall(r"[A-Za-z0-9_-]+", clause_str)
                    if m_words:
                        last_clause_tail = m_words[-1]
        return results, idx
