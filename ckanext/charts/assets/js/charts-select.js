/**
 * CKAN Charts select using tom select
 */
ckan.module("charts-select", function ($, _) {
    "use strict";

    return {
        options: {
            multiple: false,
            clearButton: false,
            maxOptions: null
        },
        initialize: function () {
            $.proxyAll(this, /_/);

            let selectEl = this.el[0];

            if (this.el[0].tomselect) {
                selectEl.tomselect.destroy();
            }

            var config = {
                plugins: {},
                maxOptions: this.options.maxOptions,
                placeholder: "Add more..."
            }

            if (this.options.clearButton) {
                config.plugins.clear_button = {
                    title: this.options.clearButton
                };
            }

            if (this.options.multiple) {
                config.plugins.checkbox_options = {
                    checkedClassNames: ['ts-checked'],
                    uncheckedClassNames: ['ts-unchecked'],
                };

                config.plugins.remove_button = {};

                config.maxItems = selectEl.getAttribute("maxitems") || null;
            }

            new TomSelect(selectEl, config);
        }
    };
});
