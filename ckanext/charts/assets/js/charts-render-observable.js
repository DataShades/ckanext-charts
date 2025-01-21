ckan.module("charts-render-observable", function($, _) {
    "use strict";

    return {
        options: {
            config: null,
        },

        initialize: function() {
            $.proxyAll(this, /_/);

            this.chartControl = this.el.next(".chart-control");
            this.chartId = this.el[0].id;

            window.charts_obvservable = window.charts_obvservable || {};

            if (!this.options.config) {
                console.error("No configuration provided");
                return;
            }

            var plot;

            switch (this.options.config.type) {
                case "bar":
                    plot = Plot.barY(this.options.config.data, this.options.config.settings).plot(this.options.config.plot);
                    break;
                case "horizontal-bar":
                    plot = Plot.barX(this.options.config.data, this.options.config.settings).plot(this.options.config.plot);
                    break;
                case "scatter":
                    plot = Plot.dot(this.options.config.data, this.options.config.settings).plot(this.options.config.plot);
                    break;
                case "line":
                    plot = Plot.line(this.options.config.data, this.options.config.settings).plot(this.options.config.plot);
                    break;
                case "pie":
                    plot = PieChart(this.options.config.data, this.options.config.settings);
                    break;
                default:
                    return;
            }

            this.el[0].replaceChildren(plot);

            window.charts_obvservable[this.chartId] = plot;

            this.chartControl.find("#makeSnapshot").on(
                "click", (e) => this._makeSnapshot(e, this.chartId)
            );
        },

        _makeSnapshot: function(event, chartId) {
            event.preventDefault();

            var chart = window.charts_obvservable[chartId];

            if (!chart) {
                console.error("Chart not found");
                return;
            }

            //get svg element.
            var svg = chart.querySelector("svg");

            //get svg source.
            var serializer = new XMLSerializer();
            var source = serializer.serializeToString(svg);

            //add name spaces.
            if(!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
                source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
            }

            if(!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)){
                source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
            }

            //add xml declaration
            source = '<?xml version="1.0" standalone="no"?>\r\n' + source;

            //convert svg source to URI data scheme.
            var dataUrl = "data:image/svg+xml;charset=utf-8,"+encodeURIComponent(source);
            var link = document.createElement('a')
            link.download = 'view-snapshot-' + Date.now() + '.svg';
            link.href = dataUrl
            link.click()

        }
    };
});

// Copyright 2018-2023 Observable, Inc.
// Released under the ISC license.
// https://observablehq.com/@d3/pie-chart

function PieChart(data, {
    names, // given d in data, returns the (ordinal) label
    values, // given d in data, returns the (quantitative) value
    title, // given d in data, returns the title text
    width = 640, // outer width, in pixels
    height = 400, // outer height, in pixels
    innerRadius = 0, // inner radius of pie, in pixels (non-zero for donut)
    outerRadius = Math.min(width, height) / 2, // outer radius of pie, in pixels
    labelRadius = (innerRadius * 0.2 + outerRadius * 0.8), // center radius of labels
    format = ",", // a format specifier for values (in the label)
    // names, // array of names (the domain of the color scale)
    colors, // array of colors for names
    stroke = innerRadius > 0 ? "none" : "white", // stroke separating widths
    strokeWidth = 1, // width of stroke separating wedges
    strokeLinejoin = "round", // line join of stroke separating wedges
    padAngle = stroke === "none" ? 1 / outerRadius : 0, // angular separation between wedges, in radians
    opacity = 1, // opacity of svg
    fontSize = 12 // font size of labels
} = {}) {
    // Compute values.
    const N = d3.map(data, (data) => data[names]);
    const V = d3.map(data, (data) => data[values]);

    const I = d3.range(N.length).filter(i => !isNaN(V[i]));

    // Unique the names.
    if (names === undefined) names = N;
    names = new d3.InternSet(names);

    // Chose a default color scheme based on cardinality.
    if (colors === undefined) colors = d3.schemeSpectral[names.size];
    if (colors === undefined) colors = d3.quantize(t => d3.interpolateSpectral(t * 0.8 + 0.1), names.size);

    // Construct scales.
    const color = d3.scaleOrdinal(names, colors);

    // Compute titles.
    if (title === undefined) {
        const formatValue = d3.format(format);
        title = i => `${N[i]}\n${formatValue(V[i])}`;
    } else {
        const O = d3.map(data, d => d);
        const T = title;
        title = i => T(O[i], i, data);
    }

    // Construct arcs.
    const arcs = d3.pie().padAngle(padAngle).sort(null).value(i => V[i])(I);
    const arc = d3.arc().innerRadius(innerRadius).outerRadius(outerRadius);
    const arcLabel = d3.arc().innerRadius(labelRadius).outerRadius(labelRadius);

    const svg = d3.create("svg")
        .attr("width", width)
        .attr("height", height)
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .attr("style", "max-width: 100%; height: auto; height: intrinsic;");

    svg.append("g")
        .attr("stroke", stroke)
        .attr("stroke-width", strokeWidth)
        .attr("stroke-linejoin", strokeLinejoin)
        .selectAll("path")
        .data(arcs)
        .join("path")
        .attr("fill", d => color(N[d.data]))
        .attr("d", arc)
        .append("title")
        .text(d => title(d.data));

    svg.append("g")
        .attr("font-family", "sans-serif")
        .attr("font-size", fontSize)
        .attr("text-anchor", "middle")
        .selectAll("text")
        .data(arcs)
        .join("text")
        .attr("transform", d => `translate(${arcLabel.centroid(d)})`)
        .selectAll("tspan")
        .data(d => {
            const lines = `${title(d.data)}`.split(/\n/);
            return (d.endAngle - d.startAngle) > 0.25 ? lines : lines.slice(0, 1);
        })
        .join("tspan")
        .attr("x", 0)
        .attr("y", (_, i) => `${i * 1.1}em`)
        .attr("font-weight", (_, i) => i ? null : "bold")
        .text(d => d);

    const resultSvg = Object.assign(svg.node(), {
        scales: {
            color
        }
    });

    resultSvg.setAttribute("opacity", opacity);

    return resultSvg;
}
