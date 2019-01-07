NAME=senpy
GITHUB_REPO=git@github.com:gsi-upm/senpy.git

IMAGENAME=gsiupm/senpy

# The first version is the main one (used for quick builds)
# See .makefiles/python.mk for more info
PYVERSIONS=3.6 3.7

DEVPORT=5000

action="test-${PYMAIN}"
GITHUB_REPO=git@github.com:gsi-upm/senpy.git

include .makefiles/base.mk
include .makefiles/k8s.mk
include .makefiles/python.mk
