import re
PHI_PATTERNS = [
    r"\bMRN\b", r"\bDOB\b", r"\bSSN\b",
    r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b",
    r"\b\(?(\d{3})\)?[- .]?(\d{3})[- .]?(\d{4})\b",
    r"\b\d{1,5} [A-Za-z0-9 .'-]+ (Ave|St|Rd|Dr|Blvd|Ln|Ct)\b",
]
def contains_phi(text: str) -> bool:
    t = text or ""
    return any(re.search(p, t, flags=re.I) for p in PHI_PATTERNS)
