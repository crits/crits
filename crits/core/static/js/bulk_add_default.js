var StatusEnum = {
  FAILURE: 0,
  SUCCESS: 1,
  DUPLICATE: 2
};

var LINK_COLUMN_NAME = '<span class="ui-icon ui-icon-tag center-icon"/>';

function appendColumns(table, newColumnsSettings, newColumnHeaders) {
    var columnHeaderNames = table.handsontable('getColHeader');
    var columnsSettings = table.handsontable('getSettings').columns;

    columnHeaderNames.push.apply(columnHeaderNames, newColumnHeaders);
    columnsSettings.push.apply(columnsSettings, newColumnsSettings);

    table.handsontable('updateSettings',
        {
            keepCellSettings: true,
            columns: columnsSettings,
            colHeaders: function (col) {
                return columnHeaderNames[col];
            }
        }
    );
}

function updateSetting(table, settingName, settingValue) {
    newSettings = {};
    newSettings[settingName] = settingValue;

    table.handsontable('updateSettings', newSettings);
}

function appendLinkColumn(table) {

    var linkColumnIndex = getColumnIndexFromName(table, LINK_COLUMN_NAME);

    if(linkColumnIndex === -1) {
        appendColumns(table, [{type: 'text', width: '30', renderer: getLinkRenderer() }], [LINK_COLUMN_NAME]);
    }

    return linkColumnIndex;
}

function appendSummary(result, isValidateOnly, messages, detailedMessages, progress) {
    if (messages.length > 0) {
        for(var counter = 0; counter < result.messages.length; counter++) {
            messages.prepend("<li>" + result.messages[counter] + "</li>");
        }
    } else if(detailedMessages.length > 0) {
        if(isValidateOnly === false) {
            if(result.failedRows.length === 0 && result.successfulRows.length > 0) {
                detailedMessages.prepend("<p>All " + result.successfulRows.length + " rows successfully uploaded.</p>");
            }
            else {
                detailedMessages.prepend("<p>Successfully uploaded " + result.successfulRows.length + " rows.</p>");
            }
        }
        else {
            if(result.failedRows.length === 0 && result.successfulRows.length > 0) {
                detailedMessages.prepend("<p>All " + result.successfulRows.length + " rows successfully validated.</p>");
            }
            else {
                detailedMessages.prepend("<p>" + result.successfulRows.length + " rows successfully passed validation.</p>");
            }
        }
    }
}

function addClass(cellMeta, clazz) {
    if(typeof cellMeta.classes === 'undefined') {
        cellMeta.classes = [clazz];
    } else {
        var index = cellMeta.classes.indexOf(clazz);

        if(index === -1 ) {
            cellMeta.classes.push(clazz);
        }
    }
}

function clearTableFormatting(table, progress, errors, totalRows) {
    errors.empty();
    progress.find('#initial').empty();
    progress.find('#status').empty();
    progress.find('.status_tabs div').empty();

    resetLinkColumn(table);

    progress.find('#status').attr('data-processed', 0);
    progress.find('#initial').html("Processing a total of " + totalRows + " rows. <img style='width: 20px', src=\"/images/waiting.gif\"/>");

    var rows = table.handsontable('countRows');
    var cols = table.handsontable('countCols');

    for(var row = 0; row < rows; row++) {
        for(var col = 0; col < cols; col++) {
            var cellMeta = table.handsontable('getCellMeta', row, col);
            removeClass(cellMeta, "htInvalid");
            removeClass(cellMeta, "htSuccess");
            removeClass(cellMeta, "htPending");
            removeClass(cellMeta, "htDuplicate");
            removeClass(cellMeta, "htLDuplicate");
            cellMeta.title = "";
        }
    }

    setClickMessageToRow(table, progress.find('#errors'));
    setClickMessageToRow(table, progress.find('#duplicates'));
    setClickMessageToRow(table, progress.find('#local_duplicates'));
    setClickMessageToRow(table, progress.find('#messages'));

    updateResultsCounts(progress);
}

function completeUpload(table, tableName, progress, totalRows, isValidateOnly, linkData) {
    var errors = progress.find('#errors');
    var duplicates = progress.find('#duplicates');
    //var localDuplicates = progress.find('#local_duplicates');

    if(typeof linkData !== "undefined") {
        table.handsontable("setDataAtCell", linkData, "ignore");
    }

    if(isValidateOnly === true) {
        progress.find('#initial').html("Finished validating all rows.");
        progress.find('#summary').prepend("<li>" + getDateString() + ": Finished validating all rows.</li>");
    } else {
        progress.find('#initial').html("Finished uploading all rows.");
        progress.find('#summary').prepend("<li>" + getDateString() + ": Finished uploading all rows.</li>");
    }

    if(errors.find('> li').length > 0) {
        var removeErrorsLink = $('<a/>').attr('href', '#').addClass('remove-errors').text('Remove Rows With Errors');
        removeErrorsLink.button();
        removeErrorsLink.css("color", 'red');

        removeErrorsLink.on('click', function() {
            var isConfirm = window.confirm("Are you sure you want to remove ALL rows with errors?");
            if (isConfirm === true)
            {
                errors.empty();
                removeRowsErrorsAll(table);
            }
        });

        errors.prepend(removeErrorsLink);
    } else if(isValidateOnly && table.handsontable("countEmptyRows") < table.handsontable("countRows")) {
        $("#update-" + tableName + "-table").button({disabled: false});
    }

    if(duplicates.find('> li').length > 0) {
        var removeDuplicatesLink = $('<a/>').attr('href', '#').addClass('remove-duplicates').text('Remove Duplicate Rows');
        removeDuplicatesLink.button();
        removeDuplicatesLink.css("color", 'red');

        removeDuplicatesLink.on('click', function() {
            var isConfirm = window.confirm("Are you sure you want to remove ALL rows that are detected to already be in CRITs?");
            if (isConfirm === true)
            {
                duplicates.empty();
                removeRowsServerDuplicateAll(table);
            }
        });

        duplicates.prepend(removeDuplicatesLink);
    }

    /*if(localDuplicates.find('> li').length > 0) {
        var removeDuplicatesLink = $('<a/>').attr('href', '#').addClass('remove-duplicates').text('Remove Local Duplicate Rows');
        removeDuplicatesLink.button();
        removeDuplicatesLink.css("color", 'red');

        removeDuplicatesLink.on('click', function() { removeRowsLocalDuplicateAll(table); });

        localDuplicates.prepend(removeDuplicatesLink);
    }*/

    updateResultsCounts(progress);

    $("#validate-" + tableName + "-table").button({disabled: true});
}

function compressTableHeight(table) {
    var tableHeight = table.find(".htCore").height();
    table.find(".wtHider").height(tableHeight);
}

function copyHandsOnTableCol(table, sourceColIndex, targetColIndex) {

    var totalRows = table.handsontable('countRows');
    var sourceData = table.handsontable('getData', 0, sourceColIndex, totalRows - 1, sourceColIndex);
    var targetData = [];

    for(var rowCounter = 0; rowCounter < totalRows; rowCounter++) {
        targetData.push([rowCounter, targetColIndex, sourceData[rowCounter][0]]) ;
    }

    table.handsontable('setDataAtCell', targetData);
}

function createLiStatusElement(prependTo, message, row, col, isShowIcons) {
    var li = $("<li/>").html(message);

    if(typeof row === "number" && typeof row === "number") {
        $(li).attr('data-row', row);
        $(li).attr('data-col', col);
    }

    if(isShowIcons === true ) {
        $(li).append("<a class=\"ui-icon ui-icon-left ui-icon-circle-close\"/>");
    }

    $(li).prependTo(prependTo);
}

function createUploadAjaxQuery(table, url, isValidateOnly, data, offset, progress, errors, isShowIcons, linkData) {
    var ajaxData = null;

    if(url) {
        ajaxData = {
            type: "POST",
            async: false,
            url: url,
            timeout: 90000,
            success: function(result) {
                parseResults(result, table, progress, errors, isValidateOnly, offset, isShowIcons, linkData);

                if((isValidateOnly === false) && (typeof result.html !== 'undefined')) {
                    post_add_patchup($(document.documentElement), result);
                }
            },
            error: function(data, textStatus, errorThrown) {
                processAjaxError(data, textStatus, errorThrown, progress, errors, offset);
            },
            data: {'data': JSON.stringify(data), 'offset': offset, 'isValidateOnly': isValidateOnly}
        };
    }
    else {
        ajaxData = {
            type: "POST",
            async: true,
            timeout: 90000,
            success: function(result) {
                parseResults(result, table, progress, errors, isValidateOnly, offset, isShowIcons, linkData);

                if((isValidateOnly === false) && (typeof result.html !== 'undefined')) {
                    post_add_patchup($(document.documentElement), result);
                }
            },
            error: function(data, textStatus, errorThrown) {
                processAjaxError(data, textStatus, errorThrown, progress, errors, offset);
            },
            data: {'data': JSON.stringify(data), 'offset': offset, 'isValidateOnly': isValidateOnly}
        };
    }

    return ajaxData;
}

function getArrayIndexOfSubstring(array, searchTarget) {
    var isFound = false;
    var counter = 0;
    var returnValue = -1;

    while(isFound === false && counter < array.length) {
        if(array[counter].indexOf(searchTarget) !== -1) {
            isFound = true;
            returnValue = counter;
        }

        counter++;
    }

    return returnValue;
}

function getBeforeChangeFunction(table) {
    return function beforeChange(changes, source) {
        for(var counter = 0; counter < changes.length; counter++) {
            // use 0 for the row because the latest row might not have been rendered yet
            var cell = table.handsontable('getCell', 0, changes[counter][1]);

            // if this is a checkbox column
            if($(cell).find('[type=\'checkbox\']').length > 0)
            {
                var value = changes[counter][3];
                // we need to normalize strings for checkbox values
                if(typeof value === 'string') {
                    if(value.toLowerCase() === 'true') {
                        changes[counter][3] = true;
                    }
                    else {
                        changes[counter][3] = false;
                    }
                }
            }

            addClass(table.handsontable("getCellMeta", changes[counter][0], changes[counter][1]), "modified");
            addClass(table.handsontable("getCellMeta", changes[counter][0], 0), "modified");
        }
    };
}

function getCellChangeFunction(handsOnTableID, tableName, enable_navigation_control) {
    return function cellChange(changedCells, source) {
        if (!changedCells || source === "ignore") {
            return;
        }

        var table = $('#' + handsOnTableID);

        $.each(changedCells, function (index, changedCell) {
            var row = changedCell[0];
            var col = changedCell[1];
            var oldCellValue = changedCell[2];
            var newCellValue = changedCell[3];
            var cellMeta = table.handsontable("getCellMeta", row, col);

            var columnName = table.handsontable('getColHeader', col);

            addClass(cellMeta, "modified");

            // Special processing for "Object Type" columns
            if(oldCellValue !== newCellValue) {
                if(typeof columnName !== 'undefined' && columnName.indexOf("Object Type") !== -1) {
                    processObjectTypeCellChange(table, row, newCellValue);
                }
            }

            if(cellMeta.classes.indexOf("htInvalid") !== -1 ||
                    cellMeta.classes.indexOf("htDuplicate") !== -1) {
                removeClass(cellMeta, "htInvalid");
                addClass(cellMeta, "htPending");
            }
        });

        if(tableName === defaultTableName) {
            $("#update-" + tableName + "-table").button({disabled: true});
            $("#validate-" + tableName + "-table").button({disabled: false});
        } else {
            $("#update-" + tableName + "-inline-table").button({disabled: false});
            $("#validate-" + tableName + "-inline-table").button({disabled: false});
        }

        if(enable_navigation_control !== false && window.onbeforeunload === null) {
            window.onbeforeunload =
                function() {
                    if(table.handsontable("countRows") !== table.handsontable("countEmptyRows")) {
                        return "You have modifications.";
                }
            };
        }

        table.handsontable('render');
    };
}

function getCleaned2DArray(table, array) {
    var returnArray = [];

    $.each(array, function(i,row) {
        if(table.handsontable('isEmptyRow', i) === true) {
            return true; // continue
        }

        $.each(row, function(j,column) {
           if (column !== null && column !== "") {
              returnArray.push(array[i]);
              return false;  // false causes each to stop looping over columns
           }
        });
    });

    return returnArray;
}

function getCleanedData(table, appendDict) {
    var returnArray = [];
    var dataArray = table.handsontable('getData');
    var colHeaderArray = [];
    var totalColumns = table.handsontable('countCols');

    for(var i = 0; i < totalColumns; i++) {
        colHeaderArray.push(table.handsontable('getColHeader', i).replace(/<(?:.|\n)*?>/gm, ''));
    }

    $.each(dataArray, function(i,row) {
        /*if (! table.find("tr:eq(" + (i+ 1) + ") td").hasClass("modified")) {
            returnArray[i] = null;
            return true; // continue
        }*/

        if(table.handsontable('isEmptyRow', i) === false) {
            returnArray[i] = {};

            $.each(row, function(j,column) {
                if(dataArray[i][j] !== null && dataArray[i][j] !== "") {
                    returnArray[i][colHeaderArray[j]] = dataArray[i][j];
                }
            });

            if(appendDict !== null) {
                for(key in appendDict) {
                    returnArray[i][key] = appendDict[key];
                }
            }
        }
    });

    return returnArray;
}

function getClickLiSelectFunction(table) {

    return function() {
        var row = $(this).data('row');
        var col = $(this).data('col');

        if(col >= 0) {
            table.handsontable("selectCell", row, col);
        } else {
            var endCol = table.handsontable("countCols") - 1;
            table.handsontable("selectCell", row, 0, row, endCol);
        }
    };
}

function getColumnIndexFromName(table, targetColumnName) {
    return getArrayIndexOfSubstring(table.handsontable('getColHeader'), targetColumnName);
}

function getContextMenuArray(table, isDisableAddObjects, addObjectsCallback)
{
    return {
        callback: function (key, options) {
            if (key === 'add_object') {
                if(addObjectsCallback) {
                    addObjectsCallback(table, table.handsontable('getSelected'));
                }
            }
            else if (key === 'duplicate_rows_local') {

            }
            else if (key === 'fill_all') {
                var row = table.handsontable('getSelected')[0];
                var col = table.handsontable('getSelected')[1];
                var colHeader = table.handsontable('getColHeader', col);
                var value = table.handsontable('getDataAtCell', row, col);

                setColumnValue(table, colHeader, value);
            }
            else if (key === 'fill_down') {
                var row = table.handsontable('getSelected')[0];
                var col = table.handsontable('getSelected')[1];
                var colHeader = table.handsontable('getColHeader', col);
                var value = table.handsontable('getDataAtCell', row, col);

                setColumnValue(table, colHeader, value, row);
            }
            else if (key === 'remove_duplicates') {

            }
            else if (key === 'remove_errors_all') {
                removeRowsErrorsAll(table);
            }
            else if (key === 'remove_errors_col') {
                removeRowsSelectedCol(table);
            }
            else if (key === 'set_height') {
                var newHeight = prompt("Enter the new height, in pixels", table.handsontable('getSettings').height);

                if (newHeight !== null) {
                    newHeight = parseInt(newHeight);

                    if (isNan(newHeight) === false) {
                        if (newHeight > 0 && newHeight < 100) {
                            newHeight = 100;
                        } else if (newHeight < 0) {
                            newHeight = 0;
                        }

                        updateSetting(table, 'height', newHeight);
                    }
                }
            }
        },
        items: {
            "row_above": {},
            "row_below": {},
            "hsep1": "---------",
            "remove_row": {
                name: 'Remove selected rows'
            },
            "hsep2": "---------",
            "fill_all": {
                name: "Fill Entire Column With Selected Cell",
                disabled: function() {
                    return (table.handsontable('getSelected')[0] !== table.handsontable('getSelected')[2]
                            || table.handsontable('getSelected')[1] !== table.handsontable('getSelected')[3]);
                }
            },
            "fill_down": {
                name: "Fill Down Column With Selected Cell",
                disabled: function() {
                    return (table.handsontable('getSelected')[0] !== table.handsontable('getSelected')[2]
                            || table.handsontable('getSelected')[1] !== table.handsontable('getSelected')[3]);
                }
            },
            "hsep3": "---------",
            "add_object": {
                name: "Add Objects For Selected Rows",
                disabled: function() {
                    return isDisableAddObjects;
                }
            },
            "hsep4": "---------",
            "set_height": {
                name: "Set Maximum Table Height"
            }
        }
    };
}

function getDateString() {
    var d = new Date();

    return ("" + d.getFullYear() + "-" + slice2(d.getMonth() + 1) +
            "-" + slice2(d.getDate()) + " " + slice2(d.getHours()) + ":" +
            slice2(d.getMinutes()) + ":" + slice2(d.getSeconds()));
}

function getDetectDuplicatesFunction() {
    return function(cleanedDataArray, targetColumns) {
        var duplicates = {};

        for(var colCounter = 0; colCounter < targetColumns.length; colCounter++) {
            var targetColumn = targetColumns[colCounter];

            var localCacheData = {};

            // First pass through
            if(colCounter === 0) {

                // Compose the list of duplicates
                for(var i = 0; i < cleanedDataArray.length; i++) {
                    var row = cleanedDataArray[i];
                    if(typeof row !== "undefined") {
                        var data = row[targetColumn];

                        if(typeof data === 'string') {
                            data = data.toLowerCase();
                        }

                        if(data in localCacheData) {
                            localCacheData[data].push(i);
                        } else if(typeof data !== "undefined") {
                            localCacheData[data] = [i];
                        }
                    }
                }

                // Convert the duplicates into one-to-many map, looks like
                // alot of work but helps with processing the resulting data.
                for(var key in localCacheData) {
                    var duplicatedRows = localCacheData[key];

                    for(var counter = 0; counter < duplicatedRows.length; counter++) {
                        var currentRow = duplicatedRows[counter];
                        duplicates[currentRow] = [[], targetColumn + "=" + key];
                        for(var counter2 = 0; counter2 < duplicatedRows.length; counter2++) {
                            if(counter !== counter2) {
                                duplicates[currentRow][0].push(duplicatedRows[counter2]);
                            }
                        }

                        // If there are no duplicates with the row then just delete
                        // the row from the map since it is not considered a
                        // duplicate with anything else.
                        if(duplicates[currentRow][0].length === 0) {
                            delete duplicates[currentRow];
                        }
                    }
                }
            } else {
                var thisSetOfDuplicates = {};

                // Parse the existing duplicate list and do a comparison
                // of data of the row versus all the other potential duplicate rows.
                for(var currentRowNumber in duplicates) {
                    var currentDuplicatedRows = duplicates[currentRowNumber][0];
                    var data = cleanedDataArray[currentRowNumber][targetColumn];

                    thisSetOfDuplicates[currentRowNumber] = [[], duplicates[currentRowNumber][1] + "; " + targetColumn + "=" + data];

                    // compare current versus other potential duplicate date
                    for(var counter = 0; counter < currentDuplicatedRows.length; counter++) {
                        var otherRowNumber = currentDuplicatedRows[counter];

                        // if there's a match.. then add the duplicate row
                        if (data === cleanedDataArray[otherRowNumber][targetColumn]) {
                            thisSetOfDuplicates[currentRowNumber][0].push(otherRowNumber);
                        }
                    }

                    // If there are no duplicates with the row then just delete
                    // the row from the map since it is not considered a
                    // duplicate with anything else.
                    if(thisSetOfDuplicates[currentRowNumber][0].length === 0) {
                        delete thisSetOfDuplicates[currentRowNumber];
                    }
                }

                duplicates = thisSetOfDuplicates;
            }
        }

        // sort the tuples, the reason for this is because normally the
        // numbering on the items are normally updated when rows are removed
        // or added but this is complex for this type of duplicate detection
        // because you could have a 1 to many relationship that you need
        // to parse. e.g. Remove 1 row might end up modifying multiple messages.
        // To make things easier, the messages displayed do not reference
        // other row numbers but instead we group the duplicates in the same
        // location so that it is easier for the user to know which
        // rows have those duplicates.
        var tuples = [];
        for (var key in duplicates) tuples.push([key, duplicates[key]]);

        tuples.sort(function(a, b) {
            rowA = parseInt(a[0]);
            valueA = a[1][1];
            rowB = parseInt(b[0]);
            valueB = b[1][1];

            // sort in reverse order
            if(valueA < valueB) {
                return 1;
            }
            else if(valueA > valueB) {
                return -1;
            } else {
                if(rowA < rowB) {
                    return 1;
                } else if(rowA > rowB) {
                    return -1;
                }

                return 0;
            }
        });

        return tuples;
    };
}

function getIsEmptyRowFunction(table) {
    return function(row) {
        /*var classes = table.handsontable('getCellMeta', row, 0).classes;
        if (typeof classes === 'undefined' || classes.indexOf("modified") === -1) {
            return true;
        }*/

        var rowData = table.handsontable('getDataAtRow', row);

        for(var col = 0; col < rowData.length; col++) {
            if(rowData[col] !== null && rowData[col] !== "") {
                return false;
            }
        }

        return true;
    };
}

function getLinkRenderer() {
    return function(instance, td, row, col, prop, value, cellProperties) {
        cellProperties.readOnly = true;
        var escaped = Handsontable.helper.stringify(value);

        if (escaped && escaped.length !== 0) {
            var $img = $('<a style="display:block; margin: 0 auto;" target="_blank" href="' + escaped + '">');
            $img.addClass("ui-icon ui-icon-tag");
            $img.attr('title', escaped);
            $img.on('mousedown', function(event) {
                event.preventDefault(); //prevent selection quirk
            });
            $(td).empty().append($img); //empty is needed because you are rendering to an existing cell
        }
        else {
            Handsontable.TextRenderer.apply(this, arguments); //render as text
        }
        return td;
    };
}

function getOffsetCell(row, col, handsOnTableID) {
    return $('#' + handsOnTableID + " tr:eq(" + (row + 1) + ") td[data-column=" + col + "]");
}

function getRemoveLiSelectFunction(table) {
    return function() {
        var row = $(this).closest('li').data('row');
        table.handsontable('alter', 'remove_row', row);
    };
}

function getRemoveRowHandler(tableName) {
    return function(index, amount) {
        var progress = $('#' + tableName + '_progress');

        removeObsoleteLiRows(progress.find('#errors > li'), index, amount);
        removeObsoleteLiRows(progress.find('#duplicates > li'), index, amount);
        removeObsoleteLiRows(progress.find('#local_duplicates > li'), index, amount);
        removeObsoleteLiRows(progress.find('#messages > li'), index, amount);

        upateLiRowText(progress.find('#errors > li'), index, amount, "remove");
        upateLiRowText(progress.find('#duplicates > li'), index, amount, "remove");
        upateLiRowText(progress.find('#local_duplicates > li'), index, amount, "remove");
        upateLiRowText(progress.find('#messages > li'), index, amount, "remove");

        updateResultsCounts(progress);

        if(tableName === defaultTableName) {
            $("#update-" + tableName + "-table").button({disabled: true});
            $("#validate-" + tableName + "-table").button({disabled: false});
        }
    };
}

function getCreateRowHandler(tableName) {
    return function(index, amount) {
        var progress = $('#' + tableName + '_progress');

        upateLiRowText(progress.find('#errors > li'), index, amount, "insert");
        upateLiRowText(progress.find('#duplicates > li'), index, amount, "insert");
        upateLiRowText(progress.find('#local_duplicates > li'), index, amount, "insert");
        upateLiRowText(progress.find('#messages > li'), index, amount, "insert");

        if(tableName === defaultTableName) {
            $("#update-" + tableName + "-table").button({disabled: true});
            $("#validate-" + tableName + "-table").button({disabled: false});
        }
    };
}

function removeObsoleteLiRows(selector, index, amount) {
    selector.filter(function() {
        var row = $(this).data('row');

        if(row !== 'undefined') {
            return (row >= index) && (row < index + amount);
        }

        return false;
    }).each(function() {
        $(this).remove();
    });
}

function parseFailedResults(result, table, errors, isShowIcons)
{
    for(var failedRowCounter = 0; failedRowCounter < result.failedRows.length; failedRowCounter++) {
        var offsetRow = result.failedRows[failedRowCounter].row - 1;
        var col = result.failedRows[failedRowCounter].col;

        if(col >= 0) {
            var offsetCol = getColumnIndexFromName(table, result.failedRows[failedRowCounter].label);
            var cellMeta = table.handsontable('getCellMeta', offsetRow, offsetCol);
            cellMeta.title += result.failedRows[failedRowCounter].message;
            addClass(cellMeta, "htInvalid");
        }
        if(col < 0) {
            // Highlight the entire row due to error
            var totalCols = table.handsontable("countCols");
            for(var colCounter = 0; colCounter < totalCols; colCounter++) {
                var cellMeta = table.handsontable('getCellMeta', offsetRow, colCounter);
                cellMeta.title += result.failedRows[failedRowCounter].message;
                addClass(cellMeta, "htInvalid");
            }
        }

        createLiStatusElement(errors, result.failedRows[failedRowCounter].message, offsetRow, col, isShowIcons);
    }
}

function parseSuccessfulResults(result, table, progress, isShowIcons, linkData, messages) {

    var linkColumnIndex = getColumnIndexFromName(table, LINK_COLUMN_NAME);

    for(var thisRow = 0; thisRow < result.successfulRows.length; thisRow++) {
        var totalCols = table.handsontable("countCols");
        var offsetRow = result.successfulRows[thisRow].row - 1;
        var status = result.successfulRows[thisRow].s;

        if(typeof result.successfulRows[thisRow].message !== "undefined") {
            if(status === StatusEnum.DUPLICATE) {
                createLiStatusElement(progress.find('#duplicates'), result.successfulRows[thisRow].message, offsetRow, -1, isShowIcons);
            } else {
                createLiStatusElement(progress.find('#messages'), result.successfulRows[thisRow].message, offsetRow, -1, false);
                messages.append(result.successfulRows[thisRow].message + '<br>');
            }
        }

        if(linkColumnIndex !== -1 && typeof result.successfulRows[thisRow].message !== "undefined") {
            var escaped = Handsontable.helper.stringify(result.successfulRows[thisRow].message);
            var matched = escaped.match(/href="([^"]*)/);

            if(matched && matched.length > 1) {
                linkData.push([offsetRow, linkColumnIndex, matched[1]]);
            }
        }

        // Highlight the entire row, due to a success
        for(var thisCol = 0; thisCol < totalCols; thisCol++) {
            var cellMeta = table.handsontable('getCellMeta', offsetRow, thisCol);

            removeClass(cellMeta, "htPending");
            removeClass(cellMeta, "htInvalid");

            if(status === StatusEnum.DUPLICATE) {
                addClass(cellMeta, "htDuplicate");
            } else {
                addClass(cellMeta, "htSuccess");
            }

            if(typeof result.successfulRows[thisRow].message !== "undefined") {
                cellMeta.title += result.successfulRows[thisRow].message;
            }
        }
    }
}

function parseResults(result, table, progress, errors, isValidateOnly, offset, isShowIcons, linkData) {

    var newlyProcessedRows = result.processed;
    var status = progress.find('#status');
    var summary = progress.find('#summary');
    var currentProcessed = parseInt(status.attr('data-processed'));
    var totalprocessed = currentProcessed + newlyProcessedRows;

    status.attr('data-processed', totalprocessed);
    summary.prepend("<li>" + getDateString() + ": Processed " + newlyProcessedRows + " rows. [Start row: " + (offset + 1) + "]</li>");

    appendSummary(result, isValidateOnly, progress.find('#messages'), errors, progress);
    parseFailedResults(result, table, errors, isShowIcons);
    parseSuccessfulResults(result, table, progress, isShowIcons, linkData, errors);

    updateResultsCounts(progress);

    table.handsontable('render');
}

function processAjaxError(data, textStatus, errorThrown, progress, errors, offset) {
    var summary = progress.find('#summary');

    summary.prepend("<li>" + getDateString() + ": Error encountered [Start row: " + (offset + 1) + "]</li>");
    summary.prepend("<li>    Status: " + textStatus + "</li>");
    summary.prepend("<li>    ErrorThrown: " + errorThrown + "</li>");
    errors.prepend("<li>" + getDateString() + ": Error encountered [Start row: " + (offset + 1) + "]</li>");
    errors.prepend("<li>    Status: " + textStatus + "</li>");
    errors.prepend("<li>    ErrorThrown: " + errorThrown + "</li>");

    console.log(data);

    updateResultsCounts(progress);
}

function removeClass(cellMeta, clazz) {
    if(typeof cellMeta.classes !== 'undefined') {
        var index = cellMeta.classes.indexOf(clazz);

        if(index !== -1 ) {
            cellMeta.classes.splice(index, 1);
        }
    }
}

function removeRowsWithClass(table, clazz) {
    var removedRows = 0;
    var ht = table.handsontable("getInstance");
    var rows = [];

    for(var row = table.handsontable("countRows") - 1; row >= 0; row--) {
        var cellMeta = ht.getCellMeta(row, 0);

        if (ht.isEmptyRow(row) === false && cellMeta.classes.indexOf(clazz) !== -1) {
            rows.push(row);
            removedRows++;
        }
    }

    if(removedRows > 0) {
        table.handsontable('alter', 'remove_rows', rows);
    }

    return removedRows;
}

function removeRowsLocalDuplicateAll(table) {
    var removedRows = removeRowsWithClass(table, 'htLDuplicate');
    alert("Removed " + removedRows + " locally duplicated rows");
}

function removeRowsServerDuplicateAll(table) {
    var removedRows = removeRowsWithClass(table, 'htDuplicate');
    alert("Removed " + removedRows + " duplicated rows");
}

function removeRowsErrorsAll(table) {
    var removedRows = 0;

    for(var col = 0; col < table.handsontable("countCols"); col++) {
        removedRows += removeRowsWithErrorInCol(table, col);
    }

    alert("Removed " + removedRows + " rows");
}

function removeRowsSelectedCol(table) {
    var col = table.handsontable('getSelected')[1];

    var removedRows = removeRowsWithErrorInCol(table, col);

    alert("Removed " + removedRows + " rows");
}

function removeRowsWithErrorInCol(table, col) {
    var removedRows = 0;
    var rows = [];

    for(var row = table.handsontable("countRows"); row >= 0; row--) {
        var cellMeta = table.handsontable('getCellMeta', row, col);

        if (typeof cellMeta.classes !== 'undefined' && cellMeta.classes.indexOf("htInvalid") !== -1) {
            rows.push(row);
            removedRows++;
        }
    }

    if(removedRows > 0) {
        table.handsontable('alter', 'remove_rows', rows);
    }

    return removedRows;
}

function resetLinkColumn(table) {
    var linkColumnIndex = getColumnIndexFromName(table, LINK_COLUMN_NAME);
    if(linkColumnIndex !== -1) {
        var totalRows = table.handsontable('countRows');
        var targetData = [];

        var linkData = table.handsontable('getData', 0, linkColumnIndex, totalRows - 1, linkColumnIndex);
        for(var row = 0; row < totalRows; row++) {
            if(typeof linkData[row][0] !== "undefined" && linkData[row][0] !== null) {
                targetData.push([row, linkColumnIndex, null]) ;
            }
        }

        table.handsontable('setDataAtCell', targetData, "ignore");
    }
}

function setClickMessageToRow(table, selector) {
    selector.off('click');
    selector.on('click', '> li', getClickLiSelectFunction(table));
    selector.on('click', 'a.ui-icon-circle-close', getRemoveLiSelectFunction(table));
}

function setColumnValue(table, targetColumnName, columnValue, startRow) {
    var totalRows = table.handsontable('countRows') - 1;
    var targetColumnIndex = getColumnIndexFromName(table, targetColumnName);
    var data = [];

    if(typeof startRow === "undefined") {
        startRow = 0;
    }

    for(var rowCounter = startRow; rowCounter < totalRows; rowCounter++) {
        data.push([rowCounter, targetColumnIndex, columnValue]);
    }

    table.handsontable('setDataAtCell', data);
}

function slice2(value) {
    return ('0' + value).slice(-2);
}

function startUpload(progress, isValidateOnly) {
    if(isValidateOnly === true) {
        progress.find('#summary').prepend("<li>" + getDateString() + ": Started validating rows.</li>");
    } else {
        progress.find('#summary').prepend("<li>" + getDateString() + ": Started uploading rows.</li>");
    }
}

function updateResultsCounts(progress, target) {
    if(typeof startRow === "undefined") {
        progress.find('.status_tabs ul li a').each(function() {
            var target = $(this).attr('data-target');
            $(this).find('.count').html("(" + ($(this).closest('.status_tabs').find('#' + target + ' li').length) + ")");
        });
    } else {
        progress.find('.status_tabs ul li a' + target).each(function() {
            var target = $(this).attr('data-target');
            $(this).find('.count').html("(" + ($(this).closest('.status_tabs').find('#' + target + ' li').length) + ")");
        });
    }
}

function upateLiRowText(selector, index, amount, actionType) {
    selector.filter(function() {
        var row = $(this).data('row');

        if(row !== 'undefined') {
            if(actionType === "insert") {
                return row >= index;
            } else {
                return row > index;
            }
        }

        return false;
    }).each(function() {
        var row = $(this).data('row');
        var offsetAmount = amount;

        if(actionType === "insert") {
            offsetAmount = -amount;
        }

        $(this).data('row', row - offsetAmount);

        var text = $(this).html();
        var rowVariant1 = "At (";
        var rowVariant2 = "At row ";

        if(text.substring(0, rowVariant1.length) === rowVariant1) {
            var numberPattern = /At\ \((\d+)/;
            var replacementText = rowVariant1 + (row - offsetAmount + 1);
            var replacedText = text.replace(numberPattern, replacementText);
            $(this).html(replacedText);
        } else if(text.substring(0, rowVariant2.length) === rowVariant2) {
            var numberPattern = /At\ row\ (\d+)/;
            var replacementText = rowVariant2 + (row - offsetAmount + 1);
            var replacedText = text.replace(numberPattern, replacementText);
            $(this).html(replacedText);

/*            var localDuplicatePattern = /Locally\ duplicate\ rows\ (.*?)\ /;

            var localDuplicateResult = localDuplicatePattern.exec(text)
            if(localDuplicateResult.length > 1) {
                var otherDuplicateRows = JSON.parse(localDuplicateResult[1]);

                if(otherDuplicateRows.length === 1) {

                }
            }

            var replacedText2 = text.replace(localDuplicatePattern, replacementText);*/
        }
    });
}

function uploadTable(tableName, validateLocalColumns, isValidateOnly, appendDict, url) {
    var ht = $('#handsontable_' + tableName).handsontable('getInstance');
    var table = $('#handsontable_' + tableName);
    var progress = $('#' + tableName + '_progress');
    var errors = $('#' + tableName + '_errors');
    var isShowIcons = false;

    if(errors.length === 0) {
        errors = progress.find('#errors');

        // only show icons for main tables, inline tables do not need icons.
        isShowIcons = true;
    }

    var cleanedDataArray = getCleanedData(table, appendDict);
    var totalRows = cleanedDataArray.length;

    var validateDomainFunction = getDetectDuplicatesFunction();

    clearTableFormatting(table, progress, errors, totalRows);

    // do local data validation if validateLocalColumns data is available
    if(typeof validateLocalColumns !== "undefined" && validateLocalColumns !== null) {
        validateLocalData(table, progress, validateDomainFunction, cleanedDataArray, validateLocalColumns);
    }

    startUpload(progress, isValidateOnly);
    var offset = 0;
    var linkData = [];

    // do batch upload of data in chunks
    while(cleanedDataArray.length > 0) {
        requestArray = cleanedDataArray.splice(0, 50);
        ajaxRequest = createUploadAjaxQuery(table, url, isValidateOnly, requestArray, offset, progress, errors, isShowIcons, linkData);
        ajaxManager.addReq(ajaxRequest);

        offset += requestArray.length;
    }

    ht.render();

    ajaxManager.setCompleteCallback(completeUpload, [table, tableName, progress, totalRows, isValidateOnly, linkData]);
    ajaxManager.run();
}

function validateLocalData(table, progress, validationFunction, cleanedDataArray, targetColumns) {
    var duplicates = validationFunction.apply(undefined, [cleanedDataArray, targetColumns]);
    var totalCols = table.handsontable('countCols');

    for(var counter in duplicates) {
        var duplicateRowNumber = duplicates[counter][0];
        var duplicateRow = duplicates[counter][1];
        var offsetRow = parseInt(duplicateRowNumber) + 1;
        var offsetDuplicates = [];

        for(var counter = 0; counter < duplicateRow[0].length; counter++) {
            offsetDuplicates.push(parseInt(duplicateRow[0][counter]) + 1);
        }

        //var message = "At row " + offsetRow + ": Warning: Locally duplicate rows [" + offsetDuplicates + "] compared to columns [" + duplicateRow[1] + "]";
        var message = "At row " + offsetRow + ": Warning: Local duplicate row compared to columns [" + duplicateRow[1] + "]";
        createLiStatusElement(progress.find('#local_duplicates'), message, parseInt(duplicateRowNumber), -1, true);

        for(var col = 0; col < totalCols; col++) {
            var cellMeta = table.handsontable('getCellMeta', duplicateRowNumber, col);
            addClass(cellMeta, "htLDuplicate");
            cellMeta.title += message;
        }
    }
}

var ajaxManager = (function() {
     var requests = [];
     var completeCallback = null;
     var completeCallbackArgs = null;

     return {
        addReq:  function(request) {
            requests.push(request);
        },
        removeReq:  function(request) {
            if( $.inArray(request, requests) > -1 )
                requests.splice($.inArray(request, requests), 1);
        },
        setCompleteCallback: function(callback, args) {
            completeCallback = callback;
            completeCallbackArgs = args;
        },
        run: function() {
            var self = this;

            if( requests.length ) {
                // serialize the ajax requests to call the next
                // ajax request after the current one "completes"
                requests[0].complete = function() {
                     requests.shift();
                     self.run.apply(self, []);
                };
                $.ajax(requests[0]);
            } else if(completeCallback !== null) {
                completeCallback.apply(undefined, completeCallbackArgs);
            }
        },
        stop:  function() {
            requests = [];
        }
     };
}());

$(document).ready(function() {
    $("#update-" + defaultTableName + "-table").off('click');

    $("#update-" + defaultTableName + "-table").click(function() {
    	$(this).button({disabled: true});
        $("#validate-" + defaultTableName + "-table").button({disabled: true});
        uploadTable(defaultTableName, defaultValidateColumns, false);
    });

    $("#validate-" + defaultTableName + "-table").click(function() {
        $(this).button({disabled: true});
        $("#update-" + defaultTableName + "-table").button({disabled: true});
        uploadTable(defaultTableName, defaultValidateColumns, true);
    });

    $('#' + defaultTableName + '_progress .status_tabs').tabs().width("75%");
    $("#update-" + defaultTableName + "-table").button("option", "disabled", true);

}); //$(document).ready

