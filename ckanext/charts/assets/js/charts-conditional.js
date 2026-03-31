ckan.module("charts-conditional", function ($) {
    "use strict";

    return {
        options: {
            conditions: [],
            fieldName: null,
        },
        initialize: function () {
            $.proxyAll(this, /_/);

            this._form = this.el.closest("form");
            this._evaluate();

            htmx.on("htmx:configRequest", this._beforeRequest);
        },

        _evaluate: function() {
            var allMet = this.options.conditions.every((condition) => {
                var current = this._getFieldValue(condition.field);
                return current === condition.value;
            });

            this.el.toggle(!!allMet);

            return allMet;
        },

        _beforeRequest: function (e) {
            var allMet = this._evaluate();

            if (!allMet) {
                delete e.detail.parameters[this.options.fieldName]
            }
        },

        _getFieldValue: function (fieldName) {
            // Collect all elements with this name (handles hidden + checkbox pair).
            var elements = this._form.find("[name='" + fieldName + "']");

            if (!elements.length) {
                return null;
            }

            var value = null;

            elements.each(function () {
                var el = $(this);
                var type = (el.attr("type") || "").toLowerCase();

                if (type === "checkbox") {
                    // Checkbox is only "authoritative" when it is checked;
                    // otherwise the hidden sibling already provided "false".
                    if (el.prop("checked")) {
                        value = el.val();
                    }
                } else {
                    // hidden inputs, selects, text inputs
                    value = el.val();
                }
            });

            return value;
        }
    };
});
