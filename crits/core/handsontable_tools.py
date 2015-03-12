import json

from django import forms
from crits.core import form_consts
from crits.core.data_tools import convert_string_to_bool, remove_html_tags
from crits.core.widgets import ExtendedChoiceField

def convert_handsontable_to_rows(request):
    """
    Converts a bulk add request represented in a 2D matrix containing
    handsontable data into an array of dictionaries.

    Each array element represents a row and each row has a dictionary
    with the column name as the key and column value as the value pair.

    Cleaning is performed to remove extraneous information that is not
    needed to process the request. For example, column headers will have their
    HTML/XML tags stripped. The HTML tags were likely used in formatted
    displaying of the column headers to the user. E.g.: <b>Required Field</b>

    Args:
        request: The Django context which contains information about the
            session and the 2D data array for the handsontable bulk add request

    Returns:
        Each array element represents a row and each row has a dictionary
        with the column name as the key and column value as the value pair.
    """

    myDict = dict(request.POST.iterlists())
    dataElement = myDict['data'][0]
    rowsData = json.loads(dataElement)
    cleanedRowsData = [];

    for rowData in rowsData:
        cleanedRowData = {};

        # If the row data is null that means we should skip processing for this row
        if rowData != None:
            for columnKey, columnValue in rowData.items():
                cleanedRowData[remove_html_tags(columnKey)] = columnValue

            cleanedRowsData.append(cleanedRowData)
        else:
            cleanedRowsData.append(None)

    return cleanedRowsData

def form_to_dict(form):
    """
    Create a dictionary from the input form. The dictionary can be used with
    handsontable to populate column/row headers and other configuration data.

    Args:
        form: The Django form objects to convert to a dictionary

    Returns:
        Returns an array of dictionaries from the input form. Includes the
        following keys in the dictionary:

            classes: The classes that will be in the Django widget's "class"
                attribute. These classes values will show up in the form's
                HTML input elements
            choices: An array of choices for fields that have a set
                list of choices
            initial: The initial value of the field, if specified
            isRequired: A boolean indicating if the field is required
                by the form
            label: The human readable displayed string identifying the field
            name: The name of the member variable for the field in the form
            position: The relative position of the field compared to other
                fields in the same form
            type: The type of the field (e.g. choice, text, checkbox)
            value: The value of the field, if specified
    """

    dict = []

    # need an offset to account for skipped fields
    offset = 0;

    for position, field in enumerate(form):
        newItem = {'name': field.name,
                   'position': position + offset,
                   'label': field.label,
                   'value': field.value,
                   'initial': field.field.initial}
        newItem['isRequired'] = field.field.required

        classes = field.field.widget.attrs.get('class')
        if classes != None:
            if "bulkskip" not in classes:
                newItem['classes'] = classes.split()

                if "bulknoinitial" in newItem['classes']:
                    newItem['initial'] = None;
            else:
                offset -= 1
                continue;

        if isinstance(field.field, ExtendedChoiceField):
            newItem['type'] = 'choice'
            newItem['choices'] = []
            for key,value,attr in field.field.choices:
                newItem['choices'].append({"key": key, "attr": attr})
        elif isinstance(field.field, forms.ChoiceField):
            newItem['type'] = 'choice'
            newItem['choices'] = []
            for key,value in field.field.choices:
                newItem['choices'].append(key)
        elif isinstance(field.field, forms.CharField):
            newItem['type'] = 'text'
        elif isinstance(field.field, forms.BooleanField):
            newItem['type'] = 'checkbox'
        elif isinstance(field.field, forms.DateTimeField):
            #newItem['type'] = 'date'
            newItem['type'] = 'text'
        elif isinstance(field.field, forms.GenericIPAddressField):
            newItem['type'] = 'text'
        else:
            newItem['type'] = 'text'

        dict.append(newItem)

    return dict

def get_field_from_label(name, formdict):
    """
    Returns the field from the form dictionary based upon the input field name

    Args:
        name: The name of the field
        formdict: the input form dictionary to parse

    Returns:
        The field from the form dictionary. Returns None if not found
    """

    for field in formdict:
        if field['name'] == name:
            return field

    return None

def parse_bulk_upload(request, parse_row_function, add_new_function, formdict, cache={}):
    """Bulk adds data by parsing an input 2D array serially adding each row.

    Args:
        request: The Django context which contains information about the
            session and the 2D data array for the handsontable bulk add request
        parse_row_function: A callback function that will handle parsing
            of each row's fields and values and then return the Django
            form representation.
        add_new_function: A callback function that will handle bulk adding
            a single row.
        formdict: The dictionary representation of the form

    Returns:
        Returns an array of dictionaries from the input form. Includes the
        following keys in the dictionary:

            failedRows: An array with a dictionary of key/value pairs with
                information about which rows and why the failure occurred.
                The following are the dictionary keys:

                    row: The row of the failure
                    col: The column of the failure. If the value is -1
                        then that means the column where the error occurred
                        is not determined.
                    label: The label of the column, if available
                    message: The reason for the failure

            messages: Helpful messages about the bulk add operations
            success: A boolean indicating if the bulk add operations were successful
            successfulRows: An array with a dictionary of key/value pairs with
                information about which rows were successfully bulk added.
                The following are the dictionary keys:

                    row: The row that was successful
            secondary: An array of information that can be passed from the
                add_new_function() function call back to the caller of this
                function. There are no restrictions on the data that can be
                passed back. Usually this is used for post processing
                analysis of the entire bulk add operation as a whole.
    """

    failedRows = []
    successfulRows = []
    messages = []
    secondaryData = []
    isFailureDetected = False
    is_validate_only = convert_string_to_bool(request.POST['isValidateOnly'])
    offset = int(request.POST.get('offset', 0));

    if cache.get("cleaned_rows_data"):
        cleanedRowsData = cache.get("cleaned_rows_data");
    else:
        cleanedRowsData = convert_handsontable_to_rows(request);

    rowCounter = offset;
    processedRows = 0;

    for rowData in cleanedRowsData:
        rowCounter = rowCounter + 1

        # Make sure that the rowData has content, otherwise the client side
        # might have done some filtering to ignore rows that have no data.
        if(rowData == None):
            continue;

        try:
            bound_form = parse_row_function(request, rowData, cache);

            # If bound form passes validation checks then continue adding the item
            if bound_form.is_valid():
                data = bound_form.cleaned_data
                errors = []
                retVal = {}
                message = ""

                (result, errors, retVal) = add_new_function(data, rowData, request, errors, is_validate_only, cache)

                processedRows += 1;

                #if retVal.get('message'):
                #    messages.append("At row " + str(rowCounter) + ": " + retVal.get('message'))
                if retVal.get('secondary'):
                    secondaryData.append(retVal.get('secondary'))

                # Check to make sure there were no errors
                for error in errors:
                    message += error + '; '
                else:
                    message = message[0:-2] # Remove '; ' from last

                if errors:
                    # If there was an error then use a "col" value of -1, this is needed because
                    # there is no easy way to indicate the specific column that caused the error.
                    # The "col": -1 will just indicate to the client side to highlight the entire row.
                    failedRows.append({'row': rowCounter,
                                       'col': -1,
                                       'message': "At row " + str(rowCounter) + ": " + message});
                else:
                    status = retVal.get(form_consts.Status.STATUS_FIELD, form_consts.Status.SUCCESS);
                    data = {'row': rowCounter, 's': status};

                    if retVal.get('warning'):
                        data['message'] = "At row " + str(rowCounter) + ": " + retVal.get('warning');
                    elif retVal.get('message'):
                        data['message'] = "At row " + str(rowCounter) + ": " + retVal.get('message');

                    successfulRows.append(data);

            # ... otherwise validation of the bound form failed and we need to
            # populate the response with error information
            else:
                processedRows += 1;

                for name, errorMessages in bound_form.errors.items():
                    entry = get_field_from_label(name, formdict)
                    if entry == None:
                        continue
                    for message in errorMessages:
                        failedRows.append({'row': rowCounter,
                                           'col': entry['position'],
                                           'label': entry['label'],
                                           'message': "At (" + str(rowCounter) + ", " + entry['label'] + "): " + message});

        except Exception,e:
            import traceback
            traceback.print_exc()

    # Populate the response to send back to the client
    response = {}
    response['success'] = (not isFailureDetected)
    response['messages'] = messages
    response['failedRows'] = failedRows
    response['successfulRows'] = successfulRows
    response['secondary'] = secondaryData
    response['processed'] = processedRows

    return response
