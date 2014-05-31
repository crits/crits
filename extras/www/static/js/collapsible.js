/**
 * @author Dan G. Switzer II
 */
(function ($){
    /* declare defaults */
    jQuery.browser={};(function(){jQuery.browser.msie=false;
    jQuery.browser.version=0;if(navigator.userAgent.match(/MSIE ([0-9]+)\./)){
    jQuery.browser.msie=true;jQuery.browser.version=RegExp.$1;}})();
    var defaults = {
        selector: "td.collapsible"        // the default selector to use
        , toggleAllSelector: ""           // the selector to use to attach the collapsibleToggle() function
        , classChildRow: "expand-child"   // define the "child row" css class
        , classCollapse: "collapsed"      // define the "collapsed" css class
        , classExpand: "expanded"         // define the "expanded" css class
        , showCollapsed: false            // specifies if the default css state should show collapsed (use this if you want to collapse the rows using CSS by default)
        , collapse: true                  // if true will force rows to collapse via JS (use this if you want JS to force the rows collapsed)
        , fx: {hide:"hide",show:"show"}   // the fx to use for showing/hiding elements (fx do not work correctly in IE6)
        , addAnchor: "append"             // how should we add the anchor? append, wrapInner, etc
        , textExpand: "Expand All"        // the text to show when expand all
        , textCollapse: "Collapse All"    // the text to show when collase all
    }, bHideParentRow = ($.browser.msie && ($.browser.version <= 7));

    $.fn.collapsible = function (sel, options){
        var self = this, bIsElOpt = (sel && sel.constructor == Object),
            settings = $.extend({}, defaults, bIsElOpt ? sel : options);

        if( !bIsElOpt ) settings.selector = sel;
        // make sure that if we're forcing to collapse, that we show the collapsed css state
        if( settings.collapse ) settings.showCollapsed = true;

        return this.each(function (e) {
            var $td = $(settings.selector, this),
                // look for existing anchors
                $a = $td.find("a");

                // if a "toggle all" selector has been specified, find and attach the behavior
                if( settings.toggleAllSelector.length > 0 ) {
                    $(settings.toggleAllSelector).collapsibleToggle(this, settings);
                }

                // if no anchors, create them
                if( $a.length == 0 ) $a = $td[settings.addAnchor]('<a href="#" class="' + settings[settings.showCollapsed ? "classCollapse" : "classExpand"] + '"></a>').find("a");

                $a.unbind('click').bind("click", function (e){
                    var $self = $(this),
                        $tr = $self.parent().parent(),
                        $trc = $tr.next(),
                        bIsCollapsed = $self.hasClass(settings.classExpand);
                    // change the css class
                    $self[bIsCollapsed ? "removeClass" : "addClass"](settings.classExpand)[!bIsCollapsed ? "removeClass" : "addClass"](settings.classCollapse);
                    while( $trc.hasClass(settings.classChildRow) ){
                        if( bHideParentRow ){
                            // get the tablesorter options
                            var ts_config = $.data(self[0], "tablesorter");
                            // hide/show the row
                            $trc[bIsCollapsed ? settings.fx.hide : settings.fx.show]();

                            // if we have the ts settings, we need to up zebra stripping if active
                            if( !bIsCollapsed && ts_config ){
                                if( $tr.hasClass(ts_config.widgetZebra.css[0]) ) $trc.addClass(ts_config.widgetZebra.css[0]).removeClass(ts_config.widgetZebra.css[1]);
                                else if( $tr.hasClass(ts_config.widgetZebra.css[1]) ) $trc.addClass(ts_config.widgetZebra.css[1]).removeClass(ts_config.widgetZebra.css[0]);
                            }
                        }
                        // show all the table cells
                        $("td", $trc)[bIsCollapsed ? settings.fx.hide : settings.fx.show]();
                        // get the next row
                        $trc = $trc.next();
                    }
                    return false;
                });

            // if not IE and we're automatically collapsing rows, collapse them now
            if( settings.collapse && !bHideParentRow ){
                $td
                    // get the tr element
                    .parent()
                    .each(function (){
                        var $tr = $(this).next();
                        while( $tr.hasClass(settings.classChildRow) ){
                            // hide each table cell
                            $tr = $tr.find("td").hide().end().next();
                        }
                    });
        }

            // if using IE, we need to hide the table rows
            if( settings.showCollapsed && bHideParentRow ){
                $td
                    // get the tr element
                    .parent()
                    .each(function (){
                        var $tr = $(this).next();
                        while( $tr.hasClass(settings.classChildRow) ){
                            $tr = $tr.hide().next();
                        }
                    });
            }
        });
    }

    $.fn.collapsibleToggle = function(table, options){
        var settings = $.extend({}, defaults, options), $table = $(table);

        // attach the expand behavior to all options
        this.toggle(
            // expand all entries
            function (){
                var $el = $(this);
                $el.addClass(settings.classExpand).removeClass(settings.classCollapse);
                if( !$el.is("td,th") )
                    $el[$el.is(":input") ? "val" : "html"](settings.textCollapse);
                $(settings.selector + " a", $table).removeClass(settings.classExpand).click();
            }
            // collapse all entries
            , function (){
                var $el = $(this);
                $el.addClass(settings.classCollapse).removeClass(settings.classExpand);
                if( !$el.is("td,th") )
                    $el[$el.is(":input") ? "val" : "html"](settings.textExpand);
                $(settings.selector + " a", $table).addClass(settings.classExpand).click();
            }
        );

        // update text
        if( !this.is("td,th") ) this[this.is(":input") ? "val" : "html"](settings.textExpand);

        return this.addClass(settings.classCollapse).removeClass(settings.classExpand);
  }

})(jQuery);
