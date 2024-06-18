ckan.module("charts-global", function ($, _) {
    "use strict";

    return {
        options: {
            reinitJs: false
        },
        initialize: function () {
            $.proxyAll(this, /_/);

            // initialize CKAN modules for HTMX loaded pages
            if (this.options.reinitJs) {
                htmx.on("htmx:afterSettle", function (event) {
                    var elements = event.target.querySelectorAll("[data-module]");

                    for (let node of elements) {
                        if (node.getAttribute("dm-initialized")) {
                            continue;
                        }

                        ckan.module.initializeElement(node);
                        node.setAttribute("dm-initialized", true)
                    }
                });
            }
        }
    };
});
