PYTHON ?= /opt/conda/glwy/envs/py311/bin/python
COMMANDS := help setup dev stop status lint format-check type-check test contract-test integration-test build security-scan clean pre-commit ci
.PHONY: $(COMMANDS)
$(COMMANDS):
	$(PYTHON) scripts/dev.py $@ $(DEV_ARGS)
