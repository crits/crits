/*
 * 
    All the javascript on this page is pertaining to form submission and error placement.
    For javascript involving the sidebar and the way the content is shown, look in config.html
*
*/
//objects used in adding error class and isChanged asterick(*) in the system tab
var generalObject = {
		nodeId:"#node_generalTab",
		contentId:"#generalTab"
};
var CRITsObject = {
             		nodeId:"#node_CRITsTab",
             		contentId:"#CRITsTab",
               		isChanged:false
             };
var LDAPObject = {
             		nodeId:"#node_LDAP",
             		contentId:"#LDAP",
               		isChanged:false
             };
var securityObject = {
             		nodeId:"#node_securityTab",
             		contentId:"#securityTab",
               		isChanged:false
             };
var downloadingObject = {
             		nodeId:"#node_downloadTab",
             		contentId:"#downloadTab",
               		isChanged:false
             };
var servicesTabObject = {
             		nodeId:"#node_servicesTab",
             		contentId:"#servicesTab",
               		isChanged:false
             };
var loggingObject = {
               		nodeId:"#node_loggingTab",
               		contentId:"#loggingTab",
               		isChanged:false
               };
//array of objects referring to the inner System nodes
var objectArray = [generalObject,
                   CRITsObject,
                   LDAPObject,
                   securityObject,
                   servicesTabObject,
                   loggingObject,
                   downloadingObject
                   ];
//get the node in the sidebar corresponding to the element in the form
function getNodeFromElement(element) {
	var object;	
	for (index in objectArray) {
		if($(objectArray[index].contentId).find(element).length) {
			object = objectArray[index];
			break;
		}
	}
	return object;
}
//add or remove the error class to the node of the element
function toggleErrorOnNode(element, turnOn) {
	var object = getNodeFromElement(element);
	if(object != undefined && turnOn)
		$(object.nodeId).addClass("error");
	else if(object != undefined && $(object.contentId).find(".error").length == 0) 
		$(object.nodeId).removeClass("error");
}
//add astrick(*) to the node once changes have been made in its corresponing tab
function addChangedSymbol(element) {
	var object = getNodeFromElement(element);
	if(object != undefined && !object.isChanged) {
		$(object.nodeId+" .w2ui-node-caption").append("<span class='isChanged'>*</span>");
		object.isChanged = true;
	}
}
//remove the isChanged astrick(*) from all nodes and reset their object's isChanged value
function resetNodesAndTheirObject() {
	$(".isChanged").remove();
	for (index in objectArray) 
		objectArray[index].isChanged = false;
}
$(document).ready(function() {				//document.ready
	//submit action of system form
	$('#config_form_submit').off().click(function(e) {
        e.preventDefault();
        $('#config_form').submit();
    });
	//remove error class on keypress
    $(document).on("keyup", ".error", function(){
    	$(this).removeClass("error"); 
    	toggleErrorOnNode($(this), false);
    });
    //add isChanged asterick(*) to the outer node
    $(document).on("keyup", ".box input,.box textarea", function(){
    	addChangedSymbol($(this));
    });
  //add isChanged asterick(*) to the outer node
    $(document).on("change", ".box select,.box input:checkbox", function(){
    	addChangedSymbol($(this));
    });
    //ajax submit of system form
    $('#config_form').off().submit(function(e) {
        e.preventDefault();
        $.ajax({
            type:"POST",
            url: $('#config_form').attr('action'),
            data: $(this).serialize(),
            datatype: 'json',
            success: function(data) {
                $("#config_results").text(data.message);
                if(data.errors.length > 0)
                	for(index in data.errors) {
                		var elementWithError = $("#id_"+data.errors[index]);
                		elementWithError.addClass("error");
                		toggleErrorOnNode(elementWithError, true);
                	}
        		else {
        			$(".error").removeClass("error");
        			resetNodesAndTheirObject();
        		}
            },
        });
    });
  //resets the systems form to its original values
	$("#reset_button").click(function() {
		$("#config_form")[0].reset();
		$(".error").removeClass("error");
		$("#config_results").empty();
		resetNodesAndTheirObject();
	});
}); //document.ready
