VERSION ?= $(shell git describe --tags --dirty 2>/dev/null)

.FORCE:

version: .FORCE
	@echo $(VERSION) > $(NAME)/VERSION
	@echo $(VERSION)

help:           ## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/\(.*:\)[^#]*##\s*\(.*\)/\1\t\2/' | column -t -s "	"

config:  ## Load config from the environment. You should run it once in every session before other tasks. Run: eval $(make config)
	@echo ". ../.env || true;"
	@awk '{ print "export " $$0}' .env
	@echo "# Please, run: "
	@echo "# eval \$$(make config)"
# If you need to run a command on the key/value pairs, use this:
# @awk '{ split($$0, a, "="); "echo " a[2] " | base64 -w 0" |& getline b64; print "export " a[1] "=" a[2]; print "export " a[1] "_BASE64=" b64}' .env

ci:  ## Run a task using gitlab-runner. Only use to debug problems in the CI pipeline
	gitlab-runner exec shell --builds-dir '.builds' --env CI_PROJECT_NAME=$(NAME) ${action}


.PHONY:: config help ci version .FORCE