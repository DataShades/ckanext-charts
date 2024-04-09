.DEFAULT_GOAL := help
.PHONY = help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


changelog:  ## compile changelog
	git changelog -c conventional -o CHANGELOG.md


vendor:
	cp node_modules/chart.js/dist/chart.umd.js ckanext/charts/assets/vendor/chart.js
	cp node_modules/plotly.js-dist/plotly.js ckanext/charts/assets/vendor/plotly.js
