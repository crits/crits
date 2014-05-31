
/*
 * jquery.ui.dialog-lazy:
 * Extend jquery.ui.dialog to provide a delayed loading or "lazy loading" functionality

 * https://github.com/bdowling/jquery-ui-extras
 *
 * Copyright (c) 2013 Brian J. Dowling
 * Licensed under the MIT, Apache-2.0 licenses.
 */


(function($){

    // var delayedOptions = {title: true,
    //                       width: true,
    //                       appendTo: true, // XXXX Caveats?
    //                       height: true};
    
    
    $.widget('ui.dialog', $.ui.dialog, {
        version: "0.2",
        options: {
            href: "",
            dialogLoaded: "",
            loadingTitle: "",
            loadingDialog: '<div style="text-align:center;"><strong>Fetching widgets ...</strong><br>' +
	                   '<br><img src="/images/chasingloader.gif"></div>',
        },
        _init: function() {
            //      if (this.options.href !== "") {
            //          this.options.autoOpen = false;
            //      }
            
            return this._super();
         }, 
        _create:  function() {
              if (this.options.href === ""  ||      // Nothing to load
                  this._wasCreated === true) {     // or it was loaded
                  //  XXXX Commented for now, but need to review the logic here when it is a non-lazy dialog ... this._wasCreated = true;  // Feels like this belongs in _create, should we have a _wasLoaded ?
                  return this._super();
              } else {
                  return true;
              }
        }, 

        // Next few methods are just to protect from calling parent before instantiation
        // There are a host of other methods in ui.dialog that are unsafe, but these
        // are just a few common ones
        _delayedSetOptions: {},
        _setOptions: function (options) {
                if (this.options.href !== "") {
                    if (!this._wasCreated) {
                        return;
                    }
                }
                
                return this._super(options);
            },
        _setOption: function (key, val) {
                // log("lazy _setOption: " + key + " = ");
                // log(val);
                if (key === "href" && val) {
                    this._wasCreated = false;
                }
                
                if (this.options.href !== "") {
                    if (!this._wasCreated) { //  && key in delayedOptions) {
                        if (this._delayedSetOptions[key] === null) {
                            this._delayedSetOptions[key] = val;
                        }
                        return;
                    }
                }
                return this._super(key,val);
        },
        refresh: function(e) {
            if (this.options.href && this._wasCreated) {
                // This was here for mostly for persona, but is better
                // done there when switching personas
                // XXXX If we find we need to turn this on again, need to strip href
                // as it will now void the _wasCreated
                // this._setOptions(this.options); // Bit Overkill, Could this backfire?
                // Alternatively have an array of keys that should be refreshed
                // log("Create Buttons");
                // this._createButtons();
            }
            //      return this._super(e);
        },
        // _createButtons: function () { // Unsafe until loaded
        //     if (this._wasCreated) {
        //      return this._super();
        //     }
        // },
        // button: function () { // Unsafe until loaded
        //     if (this._wasCreated) {
        //      return this._super();
        //     }
        // },

        open: function(e) {
            if (this.options.href === ""  ||      // Nothing to load
                this._wasCreated === true) {     // or it was loaded
                if (this._delayedSetOptions.length) {
                    this._setOptions(this._delayedSetOptions);
                    // objlog(this._delayedSetOptions);
                    this._delayedSetOptions = {};
                }

                return this._superApply(arguments);
            } else {
                this._openNext = true;
                return this.loadDialog(e);
            }
        },
        reload: function(e) {
            this._wasCreated = false;
            this._openNext = true;
            if (e) {
                 this.refresh(e);
            }
            return this.loadDialog(e);
        },
        loadDialog: function(e) {
            if (this._loader) {
                return;
            }
            if (this._openNext && !this._isOpen) {
                this._loader = $(this.options.loadingDialog);
                this._loader.attr('title', this.options.loadingTitle || 
                                  this.options.title ? 
                                  (this.options.title + " (loading)") : "Loading ...");
                this._loader.appendTo("body").hide().dialog({autoOpen: true, modal:true});
            }
            this._lastEvent = e;

            $.ajax({
                    url: this.options.href,
                        method: 'GET'
                        })
                .then($.proxy(this._loadDialog, this)); 
            
            return true;
        },
        _loadDialog: function(data, textStatus, jqXHR) {
            var e = this._lastEvent;

            var element = this.element[0];
            var div;
            if (typeof data === "object" && data.html) { // JSON is possible
                div = $(data.html);
            } else {                                    // otherwise assumed to be HTML
                div = $(data);
            }

            $(element).hide().html($(div).html()); 
            $.each(["class", "title", "name", "id"], function (i,a) {
                    $(element).attr(a, $(div).attr(a));
                });
            
            if (this._loader) {
                this._loader.remove();
                delete this._loader;
            }

            this._wasCreated = true;  // Feels like this belongs in _create, should we have a _wasLoaded ?
            this._create();

            this._trigger('loaded', null, {'dialog': this});
            if (this._openNext) {
                this._openNext = false;
                return this.open(e); 
            } else {
                return this;
            }
        },

        // Temporary work around for this widget not being able to
        // tell the widget was already in the dom at initialization.
        // This doesn't fix the cached after initialization issue.
        sideLoaded: function() {
            this._wasCreated = true; 
            this._create();
        },
        _openSuper: function() {
            return $.ui.dialog.prototype.open.call( this );                 
        },
    });
})(jQuery);
