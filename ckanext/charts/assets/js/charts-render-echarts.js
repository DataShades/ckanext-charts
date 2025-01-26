ckan.module("charts-render-echarts", function ($, _) {
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

            var myChart = echarts.init(this.el[0]);

            myChart.setOption(this.options.config);
        }
    };
});
