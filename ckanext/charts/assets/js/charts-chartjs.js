ckan.module("charts-chartjs", function ($) {
    "use strict";
    const DEFAULT_SCALE = {grace: "5%", ticks: {precision: 0}};

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
		    x: DEFAULT_SCALE,  y: DEFAULT_SCALE
		},
		borderWidth: 1,
                // backgroundColor: "#EE0000",
                // borderColor: "grey",

	    }
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

            this.chart = new Chart(ctx, { type, data, options });
        },

        getOptions: function () {
            return $.extend(true, {}, this.options.defaultOptions, this.options.options);
        },

        getData: async function () {
            const {
                data: data,
                dataUrl: url,
                dataAction: action,
                actionParams: params,
            } = this.options;

            if (action) {
                const remoteData = await new Promise((ok, err) =>
                    this.sandbox.client.call(
                        "GET",
                        action,
                        "?" + new URLSearchParams(params),
                        (resp) => ok(resp.success ? resp.result : null),
                        (error) => {
                            console.warn("Data fetch error", err);
			    ok(null);
                        }
                    )
                );

                return remoteData;
            } else {
                return data || fakeData();
            }
        },
    };
});
