from crits.vocabulary.vocab import vocab


class ThreatTypes(vocab):
    """
    Vocabulary for Actor Threat Types.
    """


    CYBER_ESPIONAGE_OPERATIONS = "Cyber Espionage Operations"
    HACKER_WHITE_HAT = "Hacker - White Hat"
    HACKER_GRAY_HAT = "Hacker - Gray Hat"
    HACKER_BLACK_HAT = "Hacker - Black Hat"
    HACKTIVIST = "Hacktivist"
    STATE_ACTOR_AGENCY = "State Actor / Agency"
    CREDENTIAL_THEFT_BOTNET_OPERATOR = "Credential Theft Botnet Operator"
    CREDENTIAL_THEFT_BOTNET_SERVICE = "Credential Theft Botnet Service"
    MALWARE_DEVELOPER = "Malware Developer"
    MONEY_LAUNDERING_NETWORK = "Money Laundering Network"
    ORGANIZED_CRIME = "Organized Crime"
    SPAM_SERVICE = "Spam Service"
    TRAFFIC_SERVICE = "Traffic Service"
    UNDERGROUND_CALL_SERVICE = "Underground Call Service"
    INSIDER_THREAT = "Insider Threat"
    DISGRUNTLED_CUSTOMER_USER = "Disgruntled Customer / User"


class Motivations(vocab):
    """
    Vocabulary for Actor Motivations.
    """


    ANTI_CORRUPTION = "Anti-Corruption"
    ANTI_ESTABLISHMENT = "Anti-Establishment"
    EGO = "Ego"
    ENVIRONMENTAL = "Environmental"
    ETHNIC_NATIONALIST = "Ethnic / Nationalist"
    FINANCIAL_OR_ECONOMIC = "Financial or Economic"
    HUMAN_RIGHTS = "Human Rights"
    INFORMATION_FREEDOM = "Information Freedom"
    MILITARY = "Military"
    OPPORTUNISTIC = "Opportunistic"
    POLITICAL = "Political"
    RELIGIOUS = "Religious"
    SECURITY_AWARENESS = "Security Awareness"


class Sophistications(vocab):
    """
    Vocabulary for Actor Sophistications.
    """


    ASPIRANT = "Aspirant"
    EXPERT = "Expert"
    INNOVATOR = "Innovator"
    NOVICE = "Novice"
    PRACTITIONER = "Practitioner"


class IntendedEffects(vocab):
    """
    Vocabulary for Actor Intended Effects.
    """


    ACCOUNT_TAKEOVER = "Account Takeover"
    BRAND_DAMAGE = "Brand Damage"
    COMPETITIVE_ADVANTAGE = "Competitive Advantage"
    CREDENTIAL_THEFT = "Credential Theft"
    DEGREDATION_OF_SERVICE = "Degredation of Service"
    DENIAL_AND_DECEPTION = "Denial and Deception"
    DESTRUCTION = "Destruction"
    DISRUPTION = "Disruption"
    ECONOMIC = "Economic"
    EMBARRASSMENT = "Embarrassment"
    EXPOSURE = "Exposure"
    EXTORTION = "Extortion"
    FRAUD = "Fraud"
    HARASSMENT = "Harassment"
    ICS_CONTROL = "ICS Control"
    IDENTITY_THEFT = "Identity Theft"
    INTELLECTUAL_PROPERTY = "Intellectual Property"
    MILITARY = "Military"
    POLITICAL = "Political"
    PROPRIETARY_INFORMATION = "Proprietary Information"
    TRAFFIC_DIVERSION = "Traffic Diversion"
    UNAUTHORIZED_ACCESS = "Unauthorized Access"
