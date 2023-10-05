ckan.module("charts-chartjs", function ($) {
    "use strict";
    // HTMX extension for in-place chart updates

    $(document).ready(function () {
        window.htmx &&
            htmx.defineExtension("ckanext-charts:chartjs", {
                transformResponse: function (text, xhr, elt) {
                    console.log("hey ho");
                    const targetId = elt.getAttribute("data-charts-target");
                    if (!targetId) {
                        console.log(
                            "'data-charts-target' is missinf from %o",
                            elt
                        );
                    }

                    const container = document.getElementById(targetId);
                    const canvas = container.querySelector("canvas");
                    const chart = Chart.getChart(canvas);

                    const data = JSON.parse(text);
                    Object.assign(chart.data, data);
                    chart.update();
                    return "";
                },
            });
    });
    const DEFAULT_SCALE = { grace: "5%", ticks: { precision: 0 } };

    function fakeData() {
        const labels = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "June",
            "June",
        ];
        const data = {
            labels: labels,
            datasets: [
                {
                    label: "My First dataset",
                    backgroundColor: "rgb(255, 99, 132)",
                    borderColor: "rgb(255, 99, 132)",
                    data: [0, 10, 5, 2, 20, 30, 45],
                },
            ],
        };

        return data;
    }

    return {
        options: {
            type: "line",
            data: null,
            dataUrl: null,
            dataAction: null,
            actionParams: null,
            options: {},
            defaultOptions: {
                scales: {
                    x: DEFAULT_SCALE,
                    y: DEFAULT_SCALE,
                },
                borderWidth: 1,
                // backgroundColor: "#EE0000",
                // borderColor: "grey",
            },
        },

        initialize: function () {
            if (this.el.is("canvas")) {
                this.canvas = this.el[0];
            } else {
                this.canvas = document.createElement("canvas");
                this.el.append(this.canvas);
            }

            this.buildChart();
        },
        buildChart: async function () {
            const ctx = this.canvas.getContext("2d");
            const options = this.getOptions();
            const data = await this.getData();
            const type = this.options.type;

            console.log(options);
            this.chart = new Chart(ctx, { type, data, options });
        },

        getOptions: function () {
            return $.extend(
                true,
                {},
                this.options.defaultOptions,
                this.options.options
            );
        },

        getData: async function () {
            return this.options.data || fakeData();
        },
    };
});
