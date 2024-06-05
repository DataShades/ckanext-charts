ckan.module("charts-render-chartjs", function ($, _) {
    "use strict";

    return {
        options: {
            config: null
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            console.log(this.options.config);
            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            new Chart(this.el[0].getContext("2d"), this.options.config);
        }
    };
});
