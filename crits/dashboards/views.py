import json

from django.contrib.auth.decorators import user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from crits.core.user_tools import user_can_view_data
from crits.core.handlers import generate_global_search
from crits.dashboards.dashboard import Dashboard
from crits.dashboards.handlers import (
    toggleTableVisibility,
    get_saved_searches_list,get_dashboard,
    clear_dashboard,
    save_data,
    get_table_data,
    generate_search_for_saved_table,
    delete_table,
    getRecordsForDefaultDashboardTable,
    switch_existing_search_to_dashboard,
    add_existing_search_to_dashboard,
    renameDashboard,
    changeTheme,
    deleteDashboard,
    getDashboardsForUser,
    createNewDashboard,
    setDefaultDashboard,
    cloneDashboard,
    setPublic,
    updateChildren
)

@user_passes_test(user_can_view_data)
def saved_searches_list(request):
    """
    Renders the saved_searches_list html
    """
    args = get_saved_searches_list(request.user)
    return render('saved_searches_list.html',  args, request)

@user_passes_test(user_can_view_data)
def dashboard(request, dashId=None):
    """
    renders the dasboard
    """
    args = get_dashboard(request.user,dashId)
    if not args["success"]:
        return respondWithError(args['message'], request=request)
    return render('dashboard.html',  args, request)

@user_passes_test(user_can_view_data)
def new_save_search(request):
    """
    Renders the initial search results on save_search.html.
    Called only from crits core
    """
    args = generate_global_search(request)
    if 'Result' in args and args['Result'] == "ERROR":
        return respondWithError(args['Message'], request=request)
    args['dashboards'] = getDashboardsForUser(request.user)
    return render("save_search.html", args, request)

@user_passes_test(user_can_view_data)
def edit_save_search(request, id):
    """
    Called when editing a saved table on the dashboard.
    Renders the saved_search.html with the customized table
    """
    args = generate_search_for_saved_table(user=request.user, id=id, request=request)
    if 'Result' in args and args['Result'] == "ERROR":
        return respondWithError(args['Message'], request=request)

    args['dashboards'] = getDashboardsForUser(request.user)

    return render("save_search.html", args, request)

@user_passes_test(user_can_view_data)
def delete_save_search(request):
    """
    Called via ajax to delete a table. Only called from the saved_search.html
    """
    id = request.GET.get("id", None)
    if not id:
        return respondWithError("Saved search cannot be found."\
                                " Please refresh and try again", True)
    response = delete_table(request.user.id, id)

    return httpResponse(response)

@user_passes_test(user_can_view_data)
def load_data(request, obj):
    """
    Ajax call to load the data for the table.
    """
    sortBy = request.GET.get("sortBy", 'null')
    pageNumber = request.GET.get("pageNumber", 1)
    maxRows = request.GET.get("maxRows", 25)
    if sortBy == 'null':
        sortBy = {}
    else:
        sortBy = json.loads(sortBy)
    return get_table_data(request, obj, sort=sortBy, pageNumber=pageNumber, maxRows=maxRows)

@user_passes_test(user_can_view_data)
def save_search(request):
    """
    Ajax call to save the table. Only called from the saved_search.html
    """
    dashId = request.GET.get('dashId', None)
    newDashName = request.GET.get('newDashName', None)
    tableId = request.GET.get("tableId", None)
    errorMessage = None
    clone = False
    try:
        if newDashName:
            newDash = createNewDashboard(request.user.id, newDashName)
            if not newDash:
                raise(Exception, "Dashboard already exists")
            dashboard = newDash
        elif dashId:
            dashboard = Dashboard.objects(id=dashId).first()
            if dashboard.isPublic and dashboard.analystId != request.user.id:
                newDash = cloneDashboard(request.user.id, dashboard, cloneSearches = True, skip=tableId)
                dashboard = newDash
                clone = True
                newDashName = newDash.name
            elif dashboard.isPublic:
                updateChildren(dashboard.id)
        else:
            errorMessage = "Error finding dashboard. Please refresh and try again."
    except Exception as e:
        print e
        errorMessage = "You already have a dashboard with that name."
    if errorMessage:
        return respondWithError(errorMessage, True)
    userId = request.GET.get('userId', None)
    tableName = request.GET.get('tableName', None)
    searchTerm = request.GET.get('query', None)
    objType = request.GET.get('object_type', None)
    columns = json.loads(request.GET.get("columns", ""))
    sortBy = request.GET.get("sortBy", None)
    isDefault = request.GET.get("isDefaultOnDashboard", "False")
    sizex = request.GET.get("sizex", None)
    maxRows = request.GET.get("maxRows", None)
    if isDefault.lower() == "true":
        isDefault = True
    else:
        isDefault = False
    if sortBy:
        sortBy = json.loads(sortBy)
    response = save_data(userId, columns, tableName, searchTerm, objType, sortBy,
                         tableId, sizex=sizex, isDefaultOnDashboard=isDefault,
                         maxRows=maxRows,
                         dashboard=dashboard, clone=clone)
    if newDashName:
        response["newDashId"] = str(newDash.id)
        response["newDashName"] = newDash.name
        response["isClone"] = clone
        response["newDashUrl"] = reverse("crits.dashboards.views.dashboard",
                                          kwargs={"dashId":newDash.id})
    return httpResponse(response)

@user_passes_test(user_can_view_data)
def save_new_dashboard(request):
    """
    Ajax call to save the dashboard and the positioning and width of the
    tables on it. Called from the dashboard.html
    """
    data = json.loads(request.POST.get('data', ''))
    userId = request.POST.get('userId', None)
    dashId = request.POST.get('dashId', None)
    user = request.user
    clone = False
    if not dashId:
        return respondWithError("Error finding dashboard. Please refresh and try again.", True)
    else:
        dashboard = Dashboard.objects(id=dashId).first()
        if dashboard.isPublic and dashboard.analystId != user.id:
            dashboard = cloneDashboard(userId, dashboard)
            if not dashboard:
                return respondWithError("You already have a dashboard with that name.", True)
            clone = True
            if not user.defaultDashboard:
                setDefaultDashboard(user, dashboard.id)
        elif dashboard.isPublic:
            updateChildren(dashboard.id)
    for table in data:
        isDefault = False
        if table['isDefault'].lower() == "true":
            isDefault = True
        sortBy = None
        if 'sortDirection' in table and 'sortField' in table:
            sortBy = {'field':table['sortField'],'direction':table['sortDirection']}
        response = save_data(userId, table['columns'], table['tableName'],
                             tableId=table['id'], isDefaultOnDashboard=isDefault,
                             sortBy=sortBy, dashboard=dashboard,
                             clone=clone, row=table['row'], grid_col=table['col'],
                             sizex=table['sizex'], sizey=table['sizey'])
        if not response['success']:
            return httpResponse(response)
    return httpResponse({"success":True,
                         "clone":clone,
                         "dashId": str(dashboard.id),
                         "message":"Dashboard saved successfully!"})

@user_passes_test(user_can_view_data)
def get_dashboard_table_data(request, tableName):
    """
    Ajax call to get the records for a default dashboard table.
    Only called from the saved_search.html when editing the table
    """
    response  = getRecordsForDefaultDashboardTable(request.user.username, tableName)
    return httpResponse(response)

@user_passes_test(user_can_view_data)
def destroy_dashboard(request):
    """
    Ajax call to clear all tables positions. called from dashbaord.html
    """
    dashId = request.GET.get('dashId', None)
    response = clear_dashboard(dashId)
    return httpResponse(response)

@user_passes_test(user_can_view_data)
def toggle_table_visibility(request):
    """
    Ajax call to toggle tables visibilty to either pinned or hidden.
    Called from saved_searches_list.html
    """
    id = request.GET.get('tableId', None)
    isVisible = request.GET.get('isVisible', True)
    if isVisible == "True":
        isVisible = False
    else:
        isVisible = True
    response = toggleTableVisibility(id, isVisible)
    return httpResponse(response)

@user_passes_test(user_can_view_data)
def set_default_dashboard(request):
    """
    Ajax call to set the users default dashboard. Called from saved_searches_list.html
    """
    id = request.GET.get('id', None)
    dashName = setDefaultDashboard(request.user, id)
    if not dashName:
        respondWithError("An error occurred while updating dashboard. Please try again later.", True)
    return respondWithSuccess(dashName + " is now your default dashboard.")

@user_passes_test(user_can_view_data)
def set_dashboard_public(request):
    """
    Ajax call to set the users default dashboard. Called from saved_searches_list.html
    """
    id = request.GET.get('id', None)
    makePublic = request.GET.get('makePublic', "true")
    successMsg = "Dashboard is now "
    if makePublic == "false":
        makePublic = False
        successMsg += "hidden from "
    else:
        makePublic = True
        successMsg += "visible to "
    successMsg += "all users."
    response = setPublic(id, makePublic)
    if type(response) == str:
        return respondWithError(response, True)
    return respondWithSuccess(successMsg)

def ignore_parent(request, id):
    """
    Ajax call to ignore that the parent of the dashboard has been changed.
    Called from dashboard.html
    """
    try:
        Dashboard.objects(id=id).update(set__hasParentChanged=False)
    except:
        return respondWithError("An error occured while updating dashboard. Please try again later.", True)
    return respondWithSuccess("success")

def delete_dashboard(request):
    """
    Ajax call to delete users dashboard. Called from saved_searches_list.html
    """
    id = request.GET.get('id', None)
    try:
        response = deleteDashboard(id)
        if not response:
            raise("Could not find table")
    except Exception as e:
        print e
        return respondWithError("An error occured while deleting dashboard. Please try again later.", True)

    return respondWithSuccess(response+" deleted successfully.")

def rename_dashboard(request):
    """
    Ajax call to rename the dashboard. Called from saved_searches_list.html
    """
    id = request.GET.get('id', None)
    name = request.GET.get('newName', None)
    try:
        response = renameDashboard(id, name, request.user.id)
        if type(response) == str:
            return respondWithError(response, True)
    except Exception as e:
        print e
        return respondWithError("An error occured while renaming dashboard. Please try again later.", True)
    return respondWithSuccess("Dashboard renamed successfully")

def change_theme(request):
    """
    Ajax call to change the dashboards theme. Called from saved_searches_list.html
    """
    theme = request.GET.get('newTheme', None)
    id = request.GET.get('id', None)
    if not id or not theme:
        return respondWithError("An error occured while changing theme. Please try again later. ", True)
    response = changeTheme(id, theme)
    if not response:
        respondWithError("An error occured while changing theme. Please try again later. ", True)
    return respondWithSuccess(response)

def create_blank_dashboard(request):
    """
    """
    name = request.GET.get('name', None)
    if not name:
        respondWithError("The dashboard must have a name.", True)
    if not createNewDashboard(request.user.id, name):
        respondWithError("You already have a dashboard with that name.", True)
    return respondWithSuccess(name + " created successfully.")

@user_passes_test(user_can_view_data)
def add_search(request):
    id = request.GET.get('id', None)
    dashboard = request.GET.get('dashboard', None)
    if not id or not dashboard:
        return respondWithError('An error occurred while adding search. Please refresh and try again', True)
    return httpResponse(add_existing_search_to_dashboard(id, dashboard, request.user))

@user_passes_test(user_can_view_data)
def switch_dashboard(request):
    id = request.GET.get('id', None)
    dashboard = request.GET.get('dashboard', None)
    if not id or not dashboard:
        return respondWithError('An error occurred while switching search. Please refresh and try again', True)
    return httpResponse(switch_existing_search_to_dashboard(id, dashboard))

def respondWithError(message, isAjax=False, request=None):
    """
    responds with the errorMessage. If not isAjax, redirects to error.html
    """
    if isAjax:
        return HttpResponse(json.dumps({'success': False, 'message': message}),
                                    content_type="application/json")
    return render("error.html", {"error": message}, request)

def respondWithSuccess(message):
    """
    ajax response with success message
    """
    return HttpResponse(json.dumps({'success': True, 'message': message}),
                         content_type="application/json")

def render(html, args, request):
    """
    Quicker way to render pages. Not necessary but neater
    """
    return render_to_response(html, args, RequestContext(request))

def httpResponse(response):
    """
    Returns response for ajax calls.
    """
    return HttpResponse(json.dumps(response), content_type="application/json")
