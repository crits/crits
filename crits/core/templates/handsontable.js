{% comment %}
TODO: Move dynamically generated javascript to static files for performance
{% endcomment %}

{% if is_bulk_add_objects %}
    {% include "bulk_add_objects.js" %}
{% endif %}

var invalidEntries = [];

function myAutocompleteRenderer(instance, td, row, col, prop, value, cellProperties) {
    Handsontable.AutocompleteCell.renderer.apply(this, arguments);
    td.style.fontStyle = 'italic';
}

function processObjectTypeCellChange(table, row, newCellValue)
{
    var valueColIndex = getColumnIndexFromName(table, "Value")

    if(valueColIndex !== -1) {
        var valueColMetadata = table.handsontable('getCellMeta', row, valueColIndex);
        var choices = getChoiceOptions{{prefix}}(newCellValue)

        if(choices !== null) {
            valueColMetadata.type = {renderer: myAutocompleteRenderer,
                    editor: Handsontable.AutocompleteEditor,
                    source: choices.choices}
            table.handsontable('render')
        }
        else if(valueColMetadata.type.source) {
            // this code was intended to reset an autocomplete
            // box back into a text box but apparently you
            // can't set the cell metadata more than once since
            // subsequent changes get ignored? Here's a
            // workaround that could work if put into
            // the handsontable code to "reset" a cell's
            // metadata. Doesn't seem like a big deal for now
            // so we'll keep it as a autocomplete box instead
            // of trying to revert it back to a text box.
            //
            // this.resetCellMeta = function (meta, row, col) {
            //  priv.cellSettings[row][col] = new priv.columnSettings[col]();
            // }
            //
            /*valueColMetadata.type = {renderer: Handsontable.TextRenderer,
                    editor: Handsontable.TextEditor,
                    source: []}

            table.handsontable('render')*/
        }
    }
}

function getChoiceOptions{{prefix}}(type) {
    // optimize this, this shouldn't be here
    {% for field in formdict %}
        {% if field.type == "choice" %}
            if(!choice_{{prefix}}_dict) {
                var choice_{{prefix}}_dict = new Object()
            }
            {% for choice in field.choices %}
                {% if choice.attr.datatype == "enum" %}
                    var choice_array = [{% for choice in choice.attr.datatype_value %}'{{choice}}'{% if not forloop.last %}, {% endif %}{% endfor %}]
                    choice_{{prefix}}_dict['{{choice.key}}'] = {'datatype': '{{choice.attr.datatype}}', 'choices': choice_array}
                {% endif %}
            {% endfor %}
        {% endif %}
    {% endfor %}

    if(typeof choice_{{prefix}}_dict[type] !== 'undefined') {
        return choice_{{prefix}}_dict[type]
    }

    return null
}

function initializeHandsOnTable{{prefix}}(handsOnTableID, tableName, descriptor) {
    var table = $('#' + handsOnTableID);
    var columnsSettings = [

    {% for field in formdict %}
        {% if field.type == "choice" %}
            {% if field.choices %}
                {type: {renderer: myAutocompleteRenderer, editor: Handsontable.AutocompleteEditor},
                source: [
                {% for choice in field.choices %}{% if choice.key %}"{{ choice.key|escape }}"{% else %}"{{ choice|escape }}"{% endif %}{% if not forloop.last %}, {% endif %} {% endfor %} ],
                strict: false,
                options : { items : Infinity }},
            {% else %}
                {type: 'numeric'},
            {% endif %}
        {% elif field.type == "checkbox" %}
            {type: '{{field.type}}'},
        {% else %}
            {type: '{{field.type}}'},
        {% endif %}
    {% endfor %}
    ]

    var columnHeaderNames = [{% for field in formdict %} {% if field.isRequired or 'bulkrequired' in field.classes %}"<b>{{ field.label|escape }}<b>"{% else %} "{{ field.label|escape }}" {% endif %}{% if not forloop.last %}, {% endif %}{% endfor %}];

    var invalidEntries = [];
    var newRowsArray = []

    table.handsontable({
        minRows: 4,
        minSpareRows: 1,
        {% if is_bulk_add_objects %}
            contextMenu: getContextMenuArray(table, false, addObjectsHandler),
            afterInit:
                function() {
                    setObjectsClickEventAllCols(table);
                },
            afterCreateRow:
                function(index, amount) {
                    for(var offset = 0; offset < amount; offset++) {
                        newRowsArray.push(index + offset)
                    }

                    getCreateRowHandler(tableName).apply(undefined, [index, amount])
                },
            afterRender:
                function(isForced) {
                    // if the isForced flag is false then that means a render
                    // occurred due to scrolling
                    if(isForced === false) {
                        setObjectsClickEventForVisibleRows(table);
                    } else {
                        setObjectsClickEventForRows(table, newRowsArray);
                        newRowsArray.length = 0;
                    }
                },
        {% else %}
            contextMenu: getContextMenuArray(table, true, null),
            afterCreateRow:
                function(index, amount) {
                    getCreateRowHandler(tableName).apply(undefined, [index, amount])
                },
        {% endif %}
        afterRemoveRow: getRemoveRowHandler(tableName),
        rowHeaders: true,
        outsideClickDeselects: true,
        height: {% if height %}{{height}}{% else %}450{% endif %},
        beforeChange: getBeforeChangeFunction(table),
        afterChange: getCellChangeFunction(handsOnTableID, tableName {%if navigation_control%}, {{navigation_control}}{%endif%}),
        isEmptyRow: getIsEmptyRowFunction(table),
        colHeaders: function (col) {
            if(col === 0 && descriptor) {
                return (columnHeaderNames[col] + "(" + descriptor + ")");
            } else {
                return columnHeaderNames[col]
            }
        },
        columns: columnsSettings
    });

    {% if is_bulk_add_objects %}
        appendObjectsColumn(table);
        appendLinkColumn(table);
    {% endif %}

    {% for field in formdict %}
        {% if field.initial %}
            setColumnValue(table, "{{field.label}}", "{{field.initial}}")
        {% endif %}
    {% endfor %}

    // Remove the "modified" class from the row because default values might
    // have  set the "modified" class even though the user never touched the row
    for(var row = 0; row < table.handsontable("countRows"); row++) {
        removeClass(table.handsontable('getCellMeta', row, 0), "modified")
    }

    $("#update-" + defaultTableName + "-table").button("option", "disabled", true);
    $("#validate-" + defaultTableName + "-table").button("option", "disabled", true);
}
