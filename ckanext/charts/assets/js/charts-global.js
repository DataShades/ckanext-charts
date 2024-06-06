ckan.module("charts-global", function ($, _) {
    "use strict";

    return {
        options: {
            config: null
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            // this hack is to dispatch a change event when a select2 element is selected
            // so the HTMX could update the chart
            this.el.find('select').on('change', function (e) {
                htmx.trigger($(this).closest('.tab-content').get(0), "change")
            });

            new TomSelect(".tom-select", { plugins: ['remove_button'], });
        }
    };
});
