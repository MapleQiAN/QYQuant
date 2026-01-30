import os


def test_api_contract_exists():
    assert os.path.exists('docs/api-contract.md')
