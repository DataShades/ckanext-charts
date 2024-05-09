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

            this.options.config.type = "line";
            this.options.config.data.datasets = this.options.config.data;

            new Chart(this.el[0], this.options.config);
        }
    };
});
