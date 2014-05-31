//
// This module setup up a top horizontal menu bar using superfish
//

(function($) {
    $(document).ready(function() {
	// Because we're cloning the ul and not nav we don't need to remove the id=
	var hmenu = $(".main-nav").clone();

	// Move any 'add' buttons to the first item of the sub-menu
	$(hmenu).find(".add").each(function() {
		$(this).prepend($(this).attr("title"));
		var ul = $(this).next("ul");
		if ( ul.length > 0) {
		    $(this).wrap("<li/>").parent().prependTo(ul.first());
		} else {
		    $(this).wrap("<ul/>").wrap("<li/>");
		}
	    });

	// These are tricky to position right in menus, and also redundant with words
	$(hmenu).find(".ui-icon").removeClass("ui-icon ui-icon-plusthick add");

	// Regroup some elements into submenus based on assigned classes
	var menu = $("<li><a href class='noclick'>Items</a><ul class='sub-mmenu'></ul></li>")
	    .insertBefore($(hmenu).find(".nav_objects").first());
	$(hmenu).find(".nav_objects").appendTo(menu.find("ul"));

	menu = $("<li><a href>Admin</a><ul class='sub-mmenu'></ul></li>")
	    .insertBefore($(hmenu).find(".nav_admin").first());
	menu.find("a").attr('href', $("#control_panel").attr('href'));
	$(hmenu).find(".nav_admin").appendTo(menu.find("ul"));

	menu = $("<li><a href>CRITs</a><ul class='sub-mmenu'></ul></li>")
	    .insertBefore($(hmenu).find(".nav_main").first());
	menu.find("a").attr('href', $("#dashboard").attr('href'));
	$(hmenu).find(".nav_main").appendTo(menu.find("ul"));

	menu = $("<li><a href>Help</a><ul class='sub-mmenu'></ul></li>")
	    .insertBefore($(hmenu).find(".nav_help").first());
	menu.find("a").attr('href', $("#help").attr('href'));
	$(hmenu).find(".nav_help").appendTo(menu.find("ul"));


	if ($.fn.superfish) {
	    $(hmenu).find(".main-nav .mmenu_item").addClass("menu-item-sm").removeClass("mmenu_item");
	    $(hmenu).addClass("sf sf-menu")
		.removeClass("mmenu")
		.show()
		.prependTo( $(".content") )
		.superfish({speed: 50, speedOut: 50, delay: 800, 
			    animation: { height:'show' },});
    
	    // Inserting superfish in top bar
	    $(".sf").wrap("<div id='sf-nav-div' class='top_item no-border' />")
		.parent().insertBefore($(".top_item")[1]);

	    $("ul.sf-menu li").addClass("ui-state-default");
	    $("ul.sf-menu > li").addClass("sf-firstrow");
	    $("ul.sf-menu li").hover(function () { $(this).addClass('ui-state-hover'); },
				     function () { $(this).removeClass('ui-state-hover'); });

	    $(".top").addClass("responsive");
	    //	    $("#show_username").addClass("showabove920");

	    $(".sf-menu > li > a").addClass("sf-level0");
	    $("<div id='show_exit' class='top_item'><a href='#'>" + 
	      "<span class='ui-icon ui-icon-extlink'/></a></div>")
		.appendTo(".top");

	    $("#show_exit > a").attr("href", $("#logout").attr("href"));
	    $("#show_username a").replaceWith( $("#show_username a").html() );
	    var info = $('#show_username').html();
	    $("#show_exit").qtip({
		            position: {my: "top left", at: "bottom center"},
			    adjust: { x: -5, y: 30 },
			    content: "Click to Logout<br/><br/> Your User Info: " + info,
			    style: {
			      classes: 'ui-tooltip-dark ui-tooltip-rounded ui-tooltip-shadow',
			    }
			});

	    //$("#sf-nav-div").position({my: "center", at: "center", of: ".top"});
	    //	    $("#sf-nav-div").css({"margin-left": "15%"});
	    $("#show_exit").css({positon: "relative", float: "left"});
	    $("#show_exit a span").css({"margin-top": "4px"});
	    $("#clipboard_container").css({position: "relative", float: "left"});

	    $("#show_username").remove();
	    $("#show_nav_menu").remove();

	    $(".sf-menu .nav_standards > a:first").html("Standards");
    
	    // $(".top_item > .main-nav > li").css({"height": "23px"});
	    $(".top_item > .main-nav > li").css({"height": "25px"});
	    $(".top_item > .main-nav > li").css({"border": "0px"});
	}
    });
})( jQuery );

