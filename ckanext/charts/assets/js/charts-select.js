/**
 * CKAN Charts select using tom select
 */
ckan.module("charts-select", function ($, _) {
    "use strict";

    return {
        initialize: function () {
            $.proxyAll(this, /_/);

            let selectEl = this.el.find("select")[0];

            if (selectEl.tomselect) {
                selectEl.tomselect.destroy();
            }

            new TomSelect(selectEl, {
                plugins: {
                    'checkbox_options': {
                        'checkedClassNames': ['ts-checked'],
                        'uncheckedClassNames': ['ts-unchecked'],
                    },
                    'remove_button': {},
                    'clear_button': {
                        'title': 'Remove all selected options',
                    }
                },
                maxItems: selectEl.getAttribute("maxitems") || null,
            });
        }
    };
});
