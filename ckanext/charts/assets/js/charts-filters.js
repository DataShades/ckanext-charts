ckan.module("charts-filters", function ($, _) {
    "use strict";

    return {
        const: {
            cls: {
                FILTER_PAIR: 'filter-pair',
                REMOVE_PAIR: 'remove-pair',
                ADD_FILTER_BTN: 'add-filter-btn',
                FILTER_CONTAINER: 'filter-container',
                SELECT_COLUMN: 'column-selector',
                SELECT_VALUE: 'value-selector',
                FILTER_INPUT: 'filters-input'
            },
            PAIR_DIVIDER: '|',
            KEY_VALUE_DIVIDER: ':',

        },
        options: {
            resourceId: null,
            columns: null
        },
        initialize: function () {
            $.proxyAll(this, /_/);

            if (!this.options.resourceId || !this.options.columns) {
                console.error("Resource ID and columns are required");
                return;
            }

            this.filterInput = $(`.${this.const.cls.FILTER_INPUT}`);

            // Add event listeners
            $(`.${this.const.cls.ADD_FILTER_BTN}`).on("click", this._addFilterPair);

            // Add event listeners on dynamic elements
            $('body').on('click', `.${this.const.cls.REMOVE_PAIR}`, this._removeFilterPair);

            // On init
            this._recreateFilterPairs();
        },

        /**
         * Recreate the filter pairs based on the input value.
         * When we're initializing the chart form, we need to recreate the
         * filter pairs based on the field that stores the filter params.
         */
        _recreateFilterPairs: function () {
            const parsedData = this._decodeFilterParams();

            if (!parsedData) {
                this._addFilterPair();
            }

            for (const [key, value] of Object.entries(parsedData)) {
                this._addFilterPair(key, value);
            };
        },

        /**
         * Add a new filter pair
         */
        _addFilterPair: function (column, value) {
            var filterPair = $('<div></div>').attr({
                class: this.const.cls.FILTER_PAIR,
            });

            var selectIdx = this._countFilterPairs() + 1;

            var fieldColumnSelect = $('<select></select>').attr({
                id: `chart-column-${selectIdx}`,
                name: `chart-column-${selectIdx}`,
                class: this.const.cls.SELECT_COLUMN,
                filterIndex: selectIdx,
            });

            var fieldValueSelect = $('<select></select>').attr({
                id: `chart-value-${selectIdx}`,
                name: `chart-value-${selectIdx}`,
                class: this.const.cls.SELECT_VALUE,
                multiple: true,
                disabled: true,
                filterIndex: selectIdx,
            });

            var removeButton = $('<a></a>').attr({
                class: 'btn btn-primary remove-pair',
                href: '#'
            }).text('Remove');

            filterPair.append(fieldColumnSelect);
            filterPair.append(fieldValueSelect);
            filterPair.append(removeButton);

            $(`.${this.const.cls.FILTER_CONTAINER}`).append(filterPair);

            this._initColumnSelector(fieldColumnSelect, column);
            this._initValueSelector(fieldValueSelect, value);
        },

        /**
         * Initialize the column selector for a given select element
         *
         * @param {JQuery<HTMLElement>} selectEl
         * @param {String} value
         */
        _initColumnSelector: function (selectEl, value) {
            let control = new TomSelect(selectEl, {
                valueField: 'id',
                labelField: 'title',
                searchField: 'title',
                options: this.options.columns,
                maxOptions: null,
                plugins: {
                    'input_autogrow': {},
                    'clear_button': {
                        'title': 'Remove all selected options',
                    }
                },
                onChange: (value) => {
                    this._changeValueSelectorState(selectEl.attr("filterindex"), value);
                }
            });

            if (value) {
                control.setValue(value, true);
            };
        },

        _initValueSelector: function (selectEl, value) {
            let control = new TomSelect(selectEl, {
                valueField: 'id',
                labelField: 'title',
                searchField: 'title',
                maxOptions: null,
                placeholder: "Add more...",
                plugins: {
                    'remove_button': {},
                    'input_autogrow': {}
                },
                onChange: (_) => {
                    this._encodeFilterParams();
                }
            });

            let colSelector = selectEl.parent().find("select.column-selector");

            if (colSelector.val()) {
                this._initValueSelectorOptions(control, colSelector.val(), value);
            }
        },

        /**
         * Remove a filter pair
         *
         * @param {Event} e
         */
        _removeFilterPair: function (e) {
            e.target.parentElement.remove()

            this._recalculateColumnSelectorIndexes();

            // we want to recalculate the filter params after removing a pair
            this._encodeFilterParams();

            // trigger a change event on the tab content to update the chart
            htmx.trigger($(".tab-content").get(0), "change")
        },

        /**
         * Count the number of filter pairs
         *
         * @returns {Number} The number of filter pairs
         */
        _countFilterPairs: function () {
            return $(`.${this.const.cls.FILTER_PAIR}`).length;
        },

        /**
         * Change the state of the value selector based on the column selector value
         *
         * @param {Number} index
         * @param {String} column_value
         */
        _changeValueSelectorState: function (index, column_value) {
            let element = $(`select.value-selector[filterindex=${index}]`).get(0);

            element.tomselect.clear();
            element.tomselect.clearOptions();

            if (!!column_value) {
                element.tomselect.enable();
                this._initValueSelectorOptions(element.tomselect, column_value);
            } else {
                element.tomselect.disable();
            }
        },

        _initValueSelectorOptions: function (control, column, value) {
            control.enable()

            $.ajax({
                url: this.sandbox.url(`/api/utils/charts/get-values`),
                data: { "resource_id": this.options.resourceId, "column": column },
                success: (options) => {
                    console.debug(options);
                    let selectValue = value;

                    for (let index = 0; index < options.length; index++) {
                        control.addOption({
                            id: options[index],
                            title: options[index],
                        });
                    }

                    if (selectValue) {
                        control.setValue(selectValue);
                    }
                }
            });
        },

        /**
         * Encode the filter params to be stored in the input value
         */
        _encodeFilterParams: function () {
            let pairs = [];

            $(`.${this.const.cls.FILTER_PAIR}`).each((_, element) => {
                let columnSelector = element.querySelector(`select.${this.const.cls.SELECT_COLUMN}`);
                let valueSelector = element.querySelector(`select.${this.const.cls.SELECT_VALUE}`);

                valueSelector.tomselect.getValue().forEach(value => {
                    pairs.push(`${columnSelector.tomselect.getValue()}${this.const.KEY_VALUE_DIVIDER}${value}`);
                });
            });

            this._updateFilterInput(pairs.join(this.const.PAIR_DIVIDER));
        },

        /**
         * Decode the filter params from the input value
         *
         * @returns {Object} The parsed filter params
         */
        _decodeFilterParams: function () {
            let filterVal = this.filterInput.val();

            if (!filterVal) {
                return {};
            }

            const keyValuePairs = filterVal.split(this.const.PAIR_DIVIDER);

            const parsedData = {};

            keyValuePairs.forEach(pair => {
                const [key, value] = pair.split(this.const.KEY_VALUE_DIVIDER);

                if (parsedData[key]) {
                    parsedData[key].push(value);
                } else {
                    parsedData[key] = [value];
                }
            });
            return parsedData;
        },

        /**
         * Update the hidden input value
         *
         * @param {String} value
         */
        _updateFilterInput: function (value) {
            this.filterInput.val(value);
        },

        _recalculateColumnSelectorIndexes: function () {
            $(`select.${this.const.cls.SELECT_COLUMN}`).each((index, element) => {
                element.setAttribute("filterindex", index + 1);
            });

            $(`select.${this.const.cls.SELECT_VALUE}`).each((index, element) => {
                element.setAttribute("filterindex", index + 1);
            });
        }
    };
});
