ckan.module("charts-global", function ($, _) {
    "use strict";

    return {
        initialize: function () {
            $.proxyAll(this, /_/);

            // this hack is to dispatch a change event when a select2 element is selected
            // so the HTMX could update the chart
            // this.el.find('select').on('change', function (e) {
            //     htmx.trigger($(this).closest('.tab-content').get(0), "change")
            // });

            // initialize CKAN modules for HTMX loaded pages
            htmx.on("htmx:afterSettle", function (event) {
                var elements = event.target.querySelectorAll("[data-module]");

                for (let node of elements) {
                    ckan.module.initializeElement(node);
                }
            });
        }
    };
});
