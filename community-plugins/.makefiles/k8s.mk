# Deployment with Kubernetes

# KUBE_CA_PEM_FILE is the path of a certificate file. It automatically set by GitLab
# if you enable Kubernetes integration in a project.
#
# As of this writing, Kubernetes integration can not be set on a group level, so it has to
# be manually set in every project.
# Alternatively, we use a custom KUBE_CA_BUNDLE environment variable, which can be set at
# the group level. In this case, the variable contains the whole content of the certificate,
# which we dump to a temporary file
#
# Check if the KUBE_CA_PEM_FILE exists. Otherwise, create it from KUBE_CA_BUNDLE
KUBE_CA_TEMP=false
ifndef KUBE_CA_PEM_FILE
KUBE_CA_PEM_FILE:=$$PWD/.ca.crt
CREATED:=$(shell printf '%b\n' '$(KUBE_CA_BUNDLE)' > $(KUBE_CA_PEM_FILE))
endif 
KUBE_TOKEN?=""
KUBE_NAMESPACE?=$(NAME)
KUBECTL=docker run --rm -v $(KUBE_CA_PEM_FILE):/tmp/ca.pem -i lachlanevenson/k8s-kubectl --server="$(KUBE_URL)" --token="$(KUBE_TOKEN)" --certificate-authority="/tmp/ca.pem" -n $(KUBE_NAMESPACE)
CI_COMMIT_REF_NAME?=master

info:: ## Print variables. Useful for debugging.
	@echo "#KUBERNETES"
	@echo KUBE_URL=$(KUBE_URL)
	@echo KUBE_CA_PEM_FILE=$(KUBE_CA_PEM_FILE)
	@echo KUBE_CA_BUNDLE=$$KUBE_CA_BUNDLE
	@echo KUBE_TOKEN=$(KUBE_TOKEN)
	@echo KUBE_NAMESPACE=$(KUBE_NAMESPACE)
	@echo KUBECTL=$(KUBECTL)

	@echo "#CI"
	@echo CI_PROJECT_NAME=$(CI_PROJECT_NAME)
	@echo CI_REGISTRY=$(CI_REGISTRY)
	@echo CI_REGISTRY_USER=$(CI_REGISTRY_USER)
	@echo CI_COMMIT_REF_NAME=$(CI_COMMIT_REF_NAME)
	@echo "CREATED=$(CREATED)"

#
# Deployment and advanced features
# 


deploy: ## Deploy to kubernetes using the credentials in KUBE_CA_PEM_FILE (or KUBE_CA_BUNDLE ) and TOKEN
	@ls k8s/*.yaml k8s/*.yml k8s/*.tmpl 2>/dev/null || true
	@cat k8s/*.yaml k8s/*.yml k8s/*.tmpl 2>/dev/null | envsubst | $(KUBECTL) apply -f -

deploy-check: ## Get the deployed configuration.
	@$(KUBECTL) get deploy,pods,svc,ingress

.PHONY:: info deploy deploy-check
