CASES = [
    {
        "fixture": "hardcoded_aws_key.diff",
        "description": "hardcoded AWS credentials in config",
        "expect_verdict": "CHANGES_REQUESTED",
        "findings_contain": ["secret", "credential", "key", "aws"],
    },
    {
        "fixture": "readme_typo.diff",
        "description": "readme typo fix",
        "expect_verdict": "LGTM",
        "findings_contain": [],
    },
    {
        "fixture": "sql_string_concat.diff",
        "description": "SQL string concatenation vulnerability",
        "expect_verdict": "CHANGES_REQUESTED",
        "findings_contain": ["sql", "injection", "query", "parameteris", "parameteriz"],
    },
    {
        "fixture": "clean_refactor.diff",
        "description": "clean refactor with tests included",
        "expect_verdict": "LGTM",
        "findings_contain": [],
    },
]
