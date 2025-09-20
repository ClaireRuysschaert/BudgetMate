OPERATION_TYPE_MAP = {
    "Carte bancaire": "CB",
    "CREDIT CARTE BANCAIRE": "RE",
    "Prelevement": "DD",
    "Cheque": "CH",
    "Especes": "CA",
    "Remboursement": "RE",
    "Interet": "IN",
    "Virement": "TR",
    "Virement recu": "TR",
    "Virement sortant": "TR",
    "Frais bancaires": "BF",
    "Autre": "OT",
    "ACHAT CB": "CB",
    "PRELEVEMENT DE": "DD",
    "VIREMENT DE": "TR",
    "VIREMENT POUR": "TR",
    "COTISATION": "BF",
}

REGEX_PURCHASE = r"(ACHAT\sCB)\s*(.*)\s(\d{2}\.\d{2}\.\d{2})"
REGEX_DIRECT_DEBIT = r"(PRELEVEMENT\sDE)\s(.*)\s(REF\s\:)"
REGEX_TRANSFER = r"(VIREMENT\sDE)\s(.*)\s(REFERENCE\s\:)"
REGEX_INSTANT_TRANSFER = r"VIREMENT INSTANTANE DE\s(.*)"
REGEX_OUTGOING_TRANSFER = r"(VIREMENT\sPOUR)\s(.*)"
REGEX_CREDIT_CARD_REFUND = r"(CREDIT\sCARTE\sBANCAIRE)\s*(.*)\s(\d{2}\.\d{2}\.\d{2})"
REGEX_BANK_FEE = r"(COTISATION\s.*)"
