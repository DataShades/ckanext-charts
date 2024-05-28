ckan.module("charts-render-plotly", function ($, _) {
    "use strict";

    return {
        options: {
            config: null
        },

        initialize: function () {
            $.proxyAll(this, /_/);

            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            Plotly.newPlot(this.el[0], this.options.config);
        }
    };
});
