.PHONY: docs test unittest

PYTHON := $(shell which python)

PROJ_DIR  := $(shell readlink -f ${CURDIR})
DOC_DIR   := ${PROJ_DIR}/docs
BUILD_DIR := ${PROJ_DIR}/build
DIST_DIR  := ${PROJ_DIR}/dist
TEST_DIR  := ${PROJ_DIR}/test
SRC_DIR   := ${PROJ_DIR}/ditk

RANGE_DIR      ?= .
RANGE_TEST_DIR := ${TEST_DIR}/${RANGE_DIR}
RANGE_SRC_DIR  := ${SRC_DIR}/${RANGE_DIR}

COV_TYPES ?= xml term-missing

package:
	$(PYTHON) -m build --sdist --wheel --outdir ${DIST_DIR}
clean:
	rm -rf ${DIST_DIR} ${BUILD_DIR} *.egg-info

test: unittest

unittest:
	pytest "${RANGE_TEST_DIR}" \
		-sv -m unittest \
		$(shell for type in ${COV_TYPES}; do echo "--cov-report=$$type"; done) \
		--cov="${RANGE_SRC_DIR}" \
		$(if ${MIN_COVERAGE},--cov-fail-under=${MIN_COVERAGE},) \
		$(if ${WORKERS},-n ${WORKERS},)

docs:
	$(MAKE) -C "${DOC_DIR}" build
pdocs:
	$(MAKE) -C "${DOC_DIR}" prod

format:
	yapf --in-place --recursive -p --verbose --style .style.yapf ${RANGE_SRC_DIR}
	yapf --in-place --recursive -p --verbose --style .style.yapf ${RANGE_TEST_DIR}
format_test:
	bash format.sh ${RANGE_SRC_DIR} --test
	bash format.sh ${RANGE_TEST_DIR} --test
flake_check:
	flake8 ${RANGE_SRC_DIR}
	flake8 ${RANGE_TEST_DIR}
