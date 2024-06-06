ckan.module("charts-select", function ($, _) {
    "use strict";

    return {
        initialize: function () {
            $.proxyAll(this, /_/);

            console.log('charts-select');
            new TomSelect(this.el.find("select")[0], { plugins: ['remove_button'], });
        }
    };
});
