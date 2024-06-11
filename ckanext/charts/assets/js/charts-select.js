ckan.module("charts-select", function ($, _) {
    "use strict";

    return {
        initialize: function () {
            $.proxyAll(this, /_/);

            new TomSelect(this.el.find("select")[0], {
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
                maxItems: this.el.find("select").attr("maxItems") || null,
            });
        }
    };
});
