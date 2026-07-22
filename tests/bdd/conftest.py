# Shared BDD-level fixtures beyond what tests/conftest.py provides.
#
# `requests_mock` (from the requests-mock package) is available automatically
# as a pytest fixture for stubbing calls to the real Mealie/KitchenOwl APIs -
# acceptance scenarios should never hit live services.
