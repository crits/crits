{% comment %}
TODO: Move dynamically generated javascript to static files for performance
{% endcomment %}

var objectsColumnName = "Objects Data"

function addObjectsHandler(table, selectedArray, isRefreshWhileDialogOpen) {
    if(typeof isRefreshWhileDialogOpen === 'undefined') {
        isRefreshWhileDialogOpen = true;
    }

    var startRow = selectedArray[0];
    var endRow = selectedArray[2];
    var tableName = "object_inline";
    var objectRowName = 'object_row';

    if(startRow > endRow) {
        var tmp = startRow;
        startRow = endRow;
        endRow = tmp;
    }

    var titleText = "";

    if(startRow === endRow) {
        titleText = "Bulk add objects for row: " + (parseInt(startRow) + 1);
    } else {
        titleText = "Bulk add objects for rows: " + (parseInt(startRow) + 1) + " - " + (parseInt(endRow) + 1);
    }

    var tableList;
    var recreateObjectsDialogFunction = function() {
        tableList = $('#handsontable_' + tableName + '_list');

        removeInlineObjectTables(tableList, objectRowName);

        createInlineObjectTables(table, tableList, startRow, endRow, objectRowName);
    };

    // check if the dialog has already been initialized
    if($('#handsontable_object').hasClass('ui-dialog-content')) {
        // the dialog has already been initialized
        $('#handsontable_object').off('dialogopen');

        $('#handsontable_object').on('dialogopen', function(event, ui) {
            recreateObjectsDialogFunction();
        });

        $('#validate-' + tableName + '-inline-table').off('click');

        // these button events need to be here because the load() function
        // is asynchronous outside of this "open" event and the buttons need to exist first
        $('#validate-' + tableName + '-inline-table').click(function() {
            for(var rowCounter = startRow; rowCounter <= endRow; rowCounter++) {
                rowTableName = objectRowName + rowCounter;
                uploadTable(rowTableName, null, true, {}, "{% url 'crits.objects.views.bulk_add_object_inline' %}");
            }
        });
    }
    else {
        // the dialog has not been initialized yet
        appendObjectsColumn(table);

        $('#handsontable_object').dialog({
            autoOpen: false,
            height: 400,
            width: 600
        });

        $('#handsontable_object').on('dialogopen', function(event, ui) {
            $(this).load("{% url 'crits.objects.views.bulk_add_object_inline' %}?" + $.param({'isPreventInitialTable': true}),
                function() {
                    var objectsColumnIndex = getColumnIndexFromName(table, objectsColumnName);

                    $('#handsontable_object_inline').prepend('<div id="handsontable_' + tableName + '_list"></div>');
                    tableList = $('#handsontable_' + tableName + '_list');

                    createInlineObjectTables(table, tableList, startRow, endRow, objectRowName);

                    $('#update-' + tableName + '-inline-table span').text('Add Objects');

                    // these button events need to be here because the load() function
                    // is asynchronous outside of this "open" event and the buttons need to exist first
                    $('#update-' + tableName + '-inline-table').click(function() {
                        var objectsDataArray = [];

                        $(tableList).find('div[id^=handsontable_' + objectRowName + "]").each(function( index, rowTable ) {
                            var rowID = $(rowTable).attr('id');
                            var rowNumber = rowID.replace('handsontable_' + objectRowName, '');
                            //var cleanedData = getCleanedData($(this));
                            var totalRows = $(this).handsontable('countRows');
                            var totalCols = $(this).handsontable('countCols');

                            var rawArrayData = $(this).handsontable('getData', 0, 0, totalRows - 1, totalCols - 1);
                            var cleanedArrayData = getCleaned2DArray($(this), rawArrayData);

                            if(objectsColumnIndex > 0 && cleanedArrayData.length > 0) {
                                objectsDataArray.push([rowNumber, objectsColumnIndex, JSON.stringify(cleanedArrayData)]);
                            }
                        });

                        table.handsontable('setDataAtCell', objectsDataArray);
                        $('#handsontable_object').dialog('close');
                    });

                    $('#validate-' + tableName + '-inline-table').off('click');

                    // these button events need to be here because the load() function
                    // is asynchronous outside of this "open" event and the buttons need to exist first
                    $('#validate-' + tableName + '-inline-table').click(function() {
                        for(var rowCounter = startRow; rowCounter <= endRow; rowCounter++) {
                            rowTableName = objectRowName + rowCounter;
                            uploadTable(rowTableName, null, true, {}, "{% url 'crits.objects.views.bulk_add_object_inline' %}");
                        }
                    });
                }
            );
        });
    }

    var isDialogOpen = $('#handsontable_object').dialog('isOpen');

    // only refresh the dialog if requested -- or, it not requested
    // then only refresh if the dialog is not already open
    if(isRefreshWhileDialogOpen === true || (isRefreshWhileDialogOpen === false && isDialogOpen === false)) {
        $('#handsontable_object').dialog('option', 'title', titleText);

        if(isDialogOpen === true) {
            recreateObjectsDialogFunction();
        } else {
            $('#handsontable_object').dialog('open');
        }
    }
}

function appendObjectsColumn(table) {

    var objectsColumnIndex = getColumnIndexFromName(table, objectsColumnName);

    if(objectsColumnIndex === -1) {
        appendColumns(table, [{type: 'text'}], [objectsColumnName]);
        setObjectsClickEventAllCols(table);
    }

    return objectsColumnIndex;
}

function createInlineObjectTables(table, createObjectsInElem, startRow, endRow, tablePrefix) {

    var objectsColumnIndex = getColumnIndexFromName(table, objectsColumnName);

    for(var rowCounter = startRow; rowCounter <= endRow; rowCounter++) {
        var rowTableName = tablePrefix + rowCounter;
        var firstColumnName = $(table).handsontable('getColHeader', 0);
        var newFullTableName = 'handsontable_' + rowTableName;

        var firstColumnValue = table.handsontable('getDataAtCell', rowCounter, 0);

        if(firstColumnValue === null) {
            firstColumnValue = "";
        }

        $(createObjectsInElem).append('<p class="row_title">Row ' + (parseInt(rowCounter) + 1) + ' [' + firstColumnName + ": " + firstColumnValue + ']</p>');
        $(createObjectsInElem).append('<div class="handsontable" id="handsontable_' + rowTableName + '"></div>');
        $(createObjectsInElem).append('<div id="' + rowTableName + '_errors"></div>');
        $(createObjectsInElem).append('<hr>');

        initializeHandsOnTableInline(newFullTableName, rowTableName);

        // try and load array data from the main table
        var existentData = table.handsontable('getDataAtCell', rowCounter, objectsColumnIndex);

        if(typeof existentData === 'string' && $.trim(existentData)) {
            try {
                var data = JSON.parse(existentData);
                //$('#' + newFullTableName).handsontable('loadData', JSON.parse(existentData))
                // Use the populateFromArray instead of loadData to force
                // the change events to fire off.
                $('#' + newFullTableName).handsontable('populateFromArray', 0, 0, data);
            } catch(ex) {
                alert("Error parsing object string data: " + existentData);
            }
        }
    }
}

function getObjectsTDFromRow(table, row) {
    var objectsColumnIndex = getColumnIndexFromName(table, objectsColumnName);
    var returnValue = null;

    if(objectsColumnIndex > 0) {
        returnValue = $(table).find("tr:eq(" + (row + 1) + ") td[data-column=" + objectsColumnIndex + "]");
    }

    return returnValue;
}

function setObjectsClickEvent(table, td) {
    $(td).on('dblclick', function(event, ui) {
        var row = td.attr('data-row');
        var col = td.attr('data-col');
        addObjectsHandler(table, [row,col,row,col], false);
    });
}

function setObjectsClickEventAllCols(table) {
    var totalRows = table.handsontable('countRows');
    var objectsColumnIndex = getColumnIndexFromName(table, objectsColumnName);

    // set the objects click event only if the objects column exists
    if(objectsColumnIndex > 0) {
        for(var row = 0; row < totalRows; row++) {
            setObjectsClickEventForRow(table, row);
        }
    }
}

function setObjectsClickEventForVisibleRows(table) {
    var totalVisibleRows = table.handsontable('countVisibleRows');

    for(var i = 0; i < totalVisibleRows; i++) {
        setObjectsClickEventForRow(table, i);
    }
}

function setObjectsClickEventForRow(table, row) {
    var td = getObjectsTDFromRow(table, row);
    if((td !== null) && (typeof td !== 'undefined')) {
        setObjectsClickEvent(table, td);
    }
}

function setObjectsClickEventForRows(table, rows) {
    for(var row = 0; row < rows.length; row++) {
        setObjectsClickEventForRow(table, rows[row]);
    }
}

function removeInlineObjectTables(table, tablePrefix) {

    $(table).find('div[id^=handsontable_' + tablePrefix + "]").remove();
    $(table).find('p.row_title').remove();
    $(table).find('div[id^=' + tablePrefix + "]").remove();
    $(table).find('hr').remove();
}
