ckan.module("charts-conditional", function ($) {
    "use strict";

    return {
        options: {
            showIf: null
        },
        initialize: function () {
            $.proxyAll(this, /_/);

            this.conditions = JSON.parse(this.options.showIf);
            this._form = this.el.closest("form");

            this._evaluate();

            this._form.on("change", this._evaluate);
            htmx.on("htmx:afterSettle", this._evaluate);
        },

        teardown: function () {
            this._form.off("change", this._evaluate);
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
        },

        /**
         * Show or hide this element based on the ``data-show-if`` conditions.
         */
        _evaluate: function () {
            var allMet = this.conditions.every((condition) => {
                var current = this._getFieldValue(condition.field);
                return current === condition.value;
            });

            if (allMet) {
                this.el.show();
            } else {
                this.el.hide();
            }
        }
    };
});
