function copyDomainSourcesToIP{{prefix}}(handsOnTableID, tableName) {
    var table = $('#' + handsOnTableID);
    colHeaderArray = table.handsontable('getColHeader');

    domainSourceColIndex = getArrayIndexOfSubstring(colHeaderArray, "Source")
    domainMethodColIndex = getArrayIndexOfSubstring(colHeaderArray, "Source Method")
    domainReferenceColIndex = getArrayIndexOfSubstring(colHeaderArray, "Source Reference")

    ipSourceColIndex = getArrayIndexOfSubstring(colHeaderArray, "IP Source")
    ipMethodColIndex = getArrayIndexOfSubstring(colHeaderArray, "IP Source Method")
    ipReferenceColIndex = getArrayIndexOfSubstring(colHeaderArray, "IP Source Reference")

    if(domainSourceColIndex !== -1 && ipSourceColIndex !== -1) {
        copyHandsOnTableCol(table, domainSourceColIndex, ipSourceColIndex);
    }

    if(domainMethodColIndex !== -1 && ipMethodColIndex !== -1) {
        copyHandsOnTableCol(table, domainMethodColIndex, ipMethodColIndex);
    }

    if(domainReferenceColIndex !== -1 && ipReferenceColIndex !== -1) {
        copyHandsOnTableCol(table, domainReferenceColIndex, ipReferenceColIndex);
    }
}

// this version of initializeHandsOnTable() is specific to filtering
// out the IP columns. We could probably optimize this by passing in 2 function
// parameters that can be called to filter out 1) column headers and
// 2) the column settings
function initializeHandsOnTable{{prefix}}(handsOnTableID, tableName) {
    var table = $('#' + handsOnTableID);
    var columnsSettingsWithoutIP = [

    {% for field in formdict %}
        {% if not field.classes or 'togglewithip' not in field.classes and 'bulkhide' not in field.classes %}
            {% if field.type == "choice" %}
                {% if field.choices %}
                    {type: {renderer: myAutocompleteRenderer, editor: Handsontable.AutocompleteEditor},
                    source: [
                    {% for key in field.choices %}"{{ key|escape }}"{% if not forloop.last %}, {% endif %} {% endfor %} ],
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
        {% endif %}
    {% endfor %}
    ]

    var columnHeaderNamesWithoutIP = [{% for field in formdict %} {% if not field.classes or 'togglewithip' not in field.classes and 'bulkhide' not in field.classes %} {% if field.isRequired or 'bulkrequired' in field.classes %}"<b>{{ field.label|escape }}<b>"{% else %} "{{ field.label|escape }}" {% endif %}{% if not forloop.last %}, {% endif %}{% endif %}{% endfor %}];

    var invalidEntries = [];
    var newRowsArray = []

    table.handsontable({
        minRows: 4,
        minSpareRows: 1,
        {% if is_bulk_add_objects %}
            contextMenu: getContextMenuArray(table, false, addObjectsHandler),
            afterInit:
                function() {
                    setObjectsClickEventAllCols(table)
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
        outsideClickDeselects: true,
        rowHeaders: true,
        colHeaders: function (col) {
            return columnHeaderNamesWithoutIP[col];
        },
        columns: columnsSettingsWithoutIP,
        height: {% if height %}{{height}}{% else %}450{% endif %},
        beforeChange: getBeforeChangeFunction(table),
        afterChange: getCellChangeFunction(handsOnTableID, tableName),
        isEmptyRow: getIsEmptyRowFunction(table),
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

function showIPs{{prefix}}(handsOnTableID, tableName) {
    var table = $('#' + handsOnTableID);

    function myAutocompleteRenderer(instance, td, row, col, prop, value, cellProperties) {
        Handsontable.AutocompleteCell.renderer.apply(this, arguments);
        td.style.fontStyle = 'italic';
    }

    var columnsSettings = [

    {% for field in formdict %}
        {% if 'togglewithip' in field.classes %}
            {% if field.type == "choice" %}
                {% if field.choices %}
                    {type: {renderer: myAutocompleteRenderer, editor: Handsontable.AutocompleteEditor},
                    source: [
                    {% for key in field.choices %}"{{ key|escape }}"{% if not forloop.last %}, {% endif %} {% endfor %} ],
                    strict: false},
                {% else %}
                    {type: 'numeric'},
                {% endif %}
            {% elif field.type == "checkbox" %}
                {type: '{{field.type}}'},
            {% else %}
                {type: '{{field.type}}'},
            {% endif %}
        {% endif %}
    {% endfor %}
    ]

    var columnHeaderNames = [{% for field in formdict %} {% if 'togglewithip' in field.classes %} {% if field.isRequired or 'bulkrequired' in field.classes %}"<b>{{ field.label|escape }}<b>"{% else %} "{{ field.label|escape }}" {% endif %}{% if not forloop.last %}, {% endif %}{% endif %}{% endfor %}];
    var isModifiedArray = [];

    // save off the 'modified' class for each row
    table.find('tr').each(function(){
        isModifiedArray.push($(this).hasClass('modified'));
    });

    appendColumns(table, columnsSettings, columnHeaderNames)

    {% for field in formdict %}
        {% if 'togglewithip' in field.classes %}
            {% if field.initial %}
                setColumnValue(table, "{{field.label}}", "{{field.initial}}")
            {% endif %}
        {% endif %}
    {% endfor %}

    // restore the 'modified' class for each row
    table.find('tr').each(function(counter){
        if(isModifiedArray[counter] === true) {
            $(this).addClass('modified')
        } else {
            $(this).removeClass('modified')
        }
    });
}

$('#custom_buttons').append('<button id="add-ips">Add IPs</button>' +
        '<button id="copy-domain-source" style="display:none">IPs Use Same Source As Domain</button>' +
        '<br><br><span id="datetimepickerarea" style="display:none">Date/Time Selector: <input id="datetimepicker" type="text"></span>')

$('#datetimepicker').datetimepicker({
    showSecond: true,
    timeFormat: 'hh:mm:ss',
    dateFormat: 'yy-mm-dd',
})

$('#add-ips').button()
$('#copy-domain-source').button()

$(document).ready(function() {

    $("#add-ips").click(function() {

        $(this).button({disabled: true});

        showIPs('handsontable_{{ table_name }}', '{{ table_name }}');

        $("#copy-domain-source").click(function() {
            copyDomainSourcesToIP('handsontable_{{ table_name }}', '{{ table_name }}');
        });

        $('#copy-domain-source').show();
        $('#datetimepickerarea').show();
    });
});

