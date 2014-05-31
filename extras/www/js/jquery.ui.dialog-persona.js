
/*
 * jquery.ui.dialog-persona:
 * Extend ui.dialog with personalities.
 * Also passes the calling event so the personality can be changed based 
 * on the currentTarget.attr('persona');

 * https://github.com/bdowling/jquery-ui-extras
 *
 * Copyright (c) 2013 Brian J. Dowling
 * Licensed under the MIT, Apache-2.0 licenses.
 */

(function($){
$.widget( "ui.dialog", $.ui.dialog, {
        version: "0.2",
        options: {
            'personas': {},
            'defaultPersona': ""
                },

        // Save and make available the last event that activated this dialog
        _activatedBy: null,
        activatedBy: function() {
            return this._activatedBy;
        },

        _persona: false,

        // _hasPersonas: false,
        // _setOption: function(key,val) {
        //     if (key === "personas") {
        //      this._hasPersonas = (val !== null);
        //     }

        //  XXX FEATURE: Could watch if href changes and invalidate
        //  _wasLoaded if it is set?

        //     this._super();
        // },

        // _init: function() {
        //      if (this._hasPersonas() && ! this._persona) {
        //       this._persona = this.options.defaultPersona;
        //     }
            
        //     return this._super();
        // },
        _hasPersonas: function() {
            if (this.options && this.options.personas) {
                return Object.getOwnPropertyNames(this.options.personas).length > 0;
            } else {
                return;
            }
        },
        open: function(e) { 
            if (e && e.currentTarget) {
                if (e.target === e.currentTarget) { // Save first in bubble stack!
                    this._activatedBy = $(e.currentTarget);
                }
            }

            if (this._hasPersonas()) { 
                this._setPersona(e);
            }
            this._superApply(arguments); // Open Dialog
        },
        refresh: function(e) {
            if (e) {
                this._setPersona(e);
            }

            // _super does not handle the case where superclass does not contain
            // the method we're calling.  Not sure how best to handle this, for now
            // capture the exception
            //            if ($.ui.dialog.prototype.hasOwnProperty("refresh")) {
            try {
                return this._super(e);
            } catch (error) {
                return; 
            }
        },
        _setPersona: function(e) {
            if (e) {
                if (e.currentTarget) {
                    this.persona($(e.currentTarget).attr("persona"));
                } else {
                    this.persona(e);
                }
            } else {
                if (this) {
                    this.persona();
                }
            }
        },
        _defaultPersona: function() {
            if (this._hasPersonas()) {
                if (!this.options.defaultPersona || 
                    !this.options.personas[this.options.defaultPersona]) {

                    this.options.defaultPersona = Object.keys(this.options.personas)[0];
                }
                return this.options.defaultPersona;
            }
        },
        persona: function(persona) {
            if (!this._hasPersonas()) {
                return;
            }

            var that = this;
            if (this._persona && 
		(persona === undefined || persona === null || persona === "")) {
		// Nothing to do, just return current persona at function exit
            } else if (persona !== this._persona || !this._persona) {
                //log("Persona: " + persona + " OLD: " + this._persona);
                var oldpersona = this._persona;
                this._persona = persona;

                if (this.options.personas[this._persona] === undefined) {
                    this._persona = this._defaultPersona();
                }

                // One persona could have attributes the other does
                // not, so we'll clear the old one just to be safe.
                // Another option might to store the "clean" state and
                // reset options based of that merge.
                if (oldpersona && this.options.personas[oldpersona]) {
                    // XXXX This isn't always going to work right, it
                    // would be better to have same keys in personas.
                    // e.g. if the one had specfic height/width and
                    // the other did not have them, the dialog would
                    // not go back to auto. Fix for this one option below.
                    
                    $.each(this.options.personas[oldpersona], 
                           function(k,v) {
                               // should this also call _setOptions to nullify?
                               delete that.options[k];
                           });
                }

                // width and height auto seem ok to impart on the
                // dialog if not overridden

                // Trying something new here, instead of extending our
                // options it may be a better bet to call
                // _setOptions() with the persona, in that way if the
                // dialog is instantiated it will force the parents to
                // do their refresh actions.

                $.extend(this.options, 
                         {width:"auto", height:"auto"},
                         this.options.personas[this._persona]);
                // If the widget is already open, also call setOptions so it can
                // handle any dynamic changes.
                this._setOptions(this.options.personas[this._persona]);
                
                // Update any features that depend on changed options
                // Note: This just calls the parent refresh() without an e.
                this.refresh(); 

                this._trigger('persona', null, {'dialog': this,
                                                    'oldpersona': oldpersona, 
                                                    'persona': this._persona});
            }

            return this._persona;
        }
            
    });
})(jQuery);
