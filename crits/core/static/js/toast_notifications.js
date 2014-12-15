$.noty.themes.crits = {
    name    : 'crits',
    helpers : {},
    modal   : {
        css: {
            position       : 'fixed',
            width          : '100%',
            height         : '100%',
            backgroundColor: '#000',
            zIndex         : 10000,
            opacity        : 0.6,
            display        : 'none',
            left           : 0,
            top            : 0
        }
    },
    style   : function() {

        this.$bar.css({
            overflow    : 'hidden',
            margin      : '4px 0',
            borderRadius: '2px'
        });

        this.$message.css({
            fontSize  : '14px',
            lineHeight: '16px',
            textAlign : 'center',
            padding   : '10px',
            width     : 'auto',
            position  : 'relative'
        });

        this.$closeButton.css({
            position  : 'absolute',
            top       : 4, right: 4,
            width     : 10, height: 10,
            background: "url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAQAAAAnOwc2AAAAxUlEQVR4AR3MPUoDURSA0e++uSkkOxC3IAOWNtaCIDaChfgXBMEZbQRByxCwk+BasgQRZLSYoLgDQbARxry8nyumPcVRKDfd0Aa8AsgDv1zp6pYd5jWOwhvebRTbzNNEw5BSsIpsj/kurQBnmk7sIFcCF5yyZPDRG6trQhujXYosaFoc+2f1MJ89uc76IND6F9BvlXUdpb6xwD2+4q3me3bysiHvtLYrUJto7PD/ve7LNHxSg/woN2kSz4txasBdhyiz3ugPGetTjm3XRokAAAAASUVORK5CYII=)",
            display   : 'none',
            cursor    : 'pointer'
        });

        this.$buttons.css({
            padding        : 5,
            textAlign      : 'right',
            borderTop      : '1px solid #ccc',
            backgroundColor: '#464646'
        });

        this.$buttons.find('button').css({
            marginLeft: 5
        });

        this.$buttons.find('button:first').css({
            marginLeft: 0
        });

        this.$bar.on({
            mouseenter: function() {
                $(this).find('.noty_close').stop().fadeTo('normal', 1);
            },
            mouseleave: function() {
                $(this).find('.noty_close').stop().fadeTo('normal', 0);
            }
        });

        switch(this.options.layout.name) {
            case 'top':
                this.$bar.css({
                    borderBottom: '2px solid #eee',
                    borderLeft  : '2px solid #eee',
                    borderRight : '2px solid #eee',
                    borderTop   : '2px solid #eee',
                    boxShadow   : "0 2px 4px rgba(0, 0, 0, 0.1)"
                });
                break;
            case 'topCenter':
            case 'center':
            case 'bottomCenter':
            case 'inline':
                this.$bar.css({
                    border   : '1px solid #eee',
                    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)"
                });
                this.$message.css({fontSize: '13px', textAlign: 'center'});
                break;
            case 'topLeft':
            case 'topRight':
            case 'bottomLeft':
            case 'bottomRight':
            case 'centerLeft':
            case 'centerRight':
                this.$bar.css({
                    border   : '1px solid #eee',
                    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)"
                });
                this.$message.css({fontSize: '13px', textAlign: 'left'});
                break;
            case 'bottom':
                this.$bar.css({
                    borderTop   : '2px solid #eee',
                    borderLeft  : '2px solid #eee',
                    borderRight : '2px solid #eee',
                    borderBottom: '2px solid #eee',
                    boxShadow   : "0 -2px 4px rgba(0, 0, 0, 0.1)"
                });
                break;
            default:
                this.$bar.css({
                    border   : '2px solid #eee',
                    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)"
                });
                break;
        }

        switch(this.options.type) {
            case 'alert':
            case 'notification':
                this.$bar.css({backgroundColor: '#D8D8D8', borderColor: '#000', color: '#000'});
                this.$bar.find('a').css({textDecoration: 'underline', color: '#000'});
                break;
            case 'warning':
                this.$bar.css({backgroundColor: '#FFEAA8', borderColor: '#FFC237', color: '#826200'});
                this.$buttons.css({borderTop: '1px solid #FFC237'});
                break;
            case 'error':
                this.$bar.css({backgroundColor: '#FF8181', borderColor: '#e25353', color: '#FFF'});
                this.$message.css({fontWeight: 'bold'});
                this.$buttons.css({borderTop: '1px solid darkred'});
                break;
            case 'information':
                this.$bar.css({backgroundColor: '#78C5E7', borderColor: '#3badd6', color: '#FFF'});
                this.$buttons.css({borderTop: '1px solid #0B90C4'});
                break;
            case 'success':
                this.$bar.css({backgroundColor: '#BCF5BC', borderColor: '#7cdd77', color: 'darkgreen'});
                this.$buttons.css({borderTop: '1px solid #50C24E'});
                break;
            default:
                this.$bar.css({backgroundColor: '#FFF', borderColor: '#CCC', color: '#444'});
                break;
        }
    },
    callback: {
        onShow : function() {

        },
        onClose: function() {

        }
    }
};

$(document).ready(function() {
    var notyIDToNotyDict = {};
    var isShowToastNotifications = true;
    var notificationQueue = [];
    var isUnloadQueue = true;

    if(initial_notifications_display === 'hide') {
        isShowToastNotifications = false;
    }

    // this variable is used to calculate the time shift between the server
    // and client times
    var serverToLocalDateDelta = null;

    var timeparts = [
        {name: 'year', div: 31536000000, mod: 10000},
        {name: 'day', div: 86400000, mod: 365},
        {name: 'hour', div: 3600000, mod: 24},
        {name: 'min', div: 60000, mod: 60},
        {name: 'sec', div: 1000, mod: 60}
    ];

    function timeAgoFuzzy(currentDate, comparisonDate) {
        var
            i = 0,
            l = timeparts.length,
            calc,
            result = null,
            interval = currentDate.getTime() - comparisonDate.getTime();
        while (i < l && result === null) {
            calc = Math.floor(interval / timeparts[i].div) % timeparts[i].mod;
            if (calc) {
                if(timeparts[i].name === 'sec' && calc < 5) {
                    result = 'just now';
                }
                else {
                    result = calc + ' ' + timeparts[i].name + (calc !== 1 ? 's' : '') + ' ago';
                }
            }
            i += 1;
        }

        if(result === null) {
            result = 'just now';
        }

        return result;
    }

    function showNotificationsCount(container, type, message, timeout, id) {
        var $closeNotifications = $("#notifications_count");

        if($closeNotifications.length === 0) {
            $("#notifications").append('<div id="notifications_count" class="noty_message"></div>');
            $("#notifications_count").click(function() {
                isShowToastNotifications = true;
                if(isUnloadQueue === true) {
                    isUnloadQueue = false;

                    while(notificationQueue.length > 0) {
                        var args = notificationQueue.shift();

                        generateContainerNoty.apply(this, args);
                    }
                }

                $("#notifications_count").remove();
            });
        }

        notificationQueue.push([container, type, message, timeout, id]);
        $('#notifications_count').text("New Notifications(" + notificationQueue.length + ")");
    }

    function generateContainerNoty(container, type, message, timeout, id) {
        if(isShowToastNotifications === false) {
            showNotificationsCount(container, type, message, timeout, id);

            return;
        }

        var n = $(container).noty({
            text        : message,
            type        : type,
            dismissQueue: true,
            layout      : 'topCenter',
            timeout     : timeout,
            theme       : 'crits',
            maxVisible  : max_visible_notifications,
            closeWith   : ['button'],
            callback: {
                onShow: function() {

                    if(newer_notifications_location === 'top') {
                        // This line of code will reverse the ordering so that the
                        // newest notifications are on the top of the <ul> element
                        $('#notifications > ul').prepend($('#' + this.options.id).parent());
                    }

                    if(notification_anchor_location === "bottom_right") {
                        $("#notifications").css({
                            top: "auto",
                            bottom: "30px"
                        });
                    } else if(notification_anchor_location === "top_right") {
                        $("#notifications").css({
                            top: "30px",
                            bottom: "auto"
                        });
                    }

                    var $closeNotifications = $("#close_notifications");

                    if($closeNotifications.length === 0) {
                        var closeNotificationsElem = '<div id="close_notifications" class="noty_message">[Close All]</div>';

                        if(notification_anchor_location === "bottom_right") {
                            $("#notifications").append(closeNotificationsElem);
                        } else if(notification_anchor_location === "top_right") {
                            $("#notifications").prepend(closeNotificationsElem);
                        }

                        $("#close_notifications").click(function() {
                            $("#notifications").find(".noty_bar").each(function() {
                                // could do $.noty.closeAll() but it doesn't
                                // display any of the hidden notifications
                                // due to maxVisible limit.
                                $.noty.close($(this).attr("id"));
                            });
                            $("#close_notifications").hide();

                            updateQueueSize($.noty.queue.length - $("#notifications").find(".noty_bar").length);
                        });

                    } else {
                        // move the close notifications to the bottom, because
                        // it will reset to the top after all the notifications
                        // have been closed.
                        if(notification_anchor_location === "bottom_right") {
                            $closeNotifications.parent().append($closeNotifications);
                        } else if(notification_anchor_location === "top_right") {
                            $closeNotifications.parent().prepend($closeNotifications);
                        }

                        $("#close_notifications").show();
                    }

                    // Update the times after showing a new notification
                    // otherwise the notification might not even be
                    // displaying a time
                    if(serverToLocalDateDelta !== null) {
                        var currentDate = new Date();
                        var shiftedCurrentDate = new Date(currentDate - serverToLocalDateDelta);
                        updateNotificationTimes(shiftedCurrentDate);
                    }
                },
                onClose: function(self) {
                    var notifications_li = $("#notifications > ul > li");

                    if(notifications_li.length === 1) {
                        // this means that all the notifications have been
                        // closed, so hide the close notifications box.
                        $("#close_notifications").hide();
                    }

                    if(n.options.id in notyIDToNotyDict) {
                        var notyToDelete = notyIDToNotyDict[n.options.id];
                        var idToDelete = notyToDelete['mongoID'];

                        $.ajax({
                            url: notifications_ack_url,
                            dataType: "json",
                            type: "POST",
                            data: {id: idToDelete}
                        });

                        delete notyIDToNotyDict[n.options.id];
                    }

                    updateQueueSize($.noty.queue.length - 1);
                }
            }
        });

        updateQueueSize($.noty.queue.length);

        notyIDToNotyDict[n.options.id] = {'noty': n, 'mongoID': id};
    }

    function updateQueueSize(queueLength) {
        if(queueLength > 0) {
            var closeBarMessage = "[Close All]<br>(" + queueLength + " hidden notifications)";
            $("#close_notifications").html(closeBarMessage);
        } else {
            $("#close_notifications").text("[Close All]");
        }
    }

    function updateNotificationTimes(currentDate) {
        $("span.noty_modified").each(function() {
            var modifiedDate = new Date($(this).data("modified"));
            var dateDifference = timeAgoFuzzy(currentDate, modifiedDate);

            $(this).text(dateDifference);
        });
    }

    if(typeof notifications_url !== "undefined") {
        var numPollFailures = 0;

        (function poll(date_param) {
            var newer_than = null;

            if(typeof date_param !== "undefined" && date_param !== "") {
                newer_than = date_param;
            }

            // the default timeout to throttle polling attempts.
            var poll_timeout = 3000;

            // keep polling only if we haven't encountered x consecutive failures.
            if(numPollFailures < 5) {
                $.ajax({
                    url: notifications_url,
                    timeout: 120000,
                    dataType: "json",
                    type: "POST",
                    data: {newer_than: newer_than},
                    success: function (data) {
                        numPollFailures = 0;
                        var notifications = data['notifications'];
                        var newest_notification = data['newest_notification'];
                        var serverTime = data['server_time'];
                        var dialogTimeout = data['timeout'];

                        if(newest_notification !== null) {
                            newer_than = newest_notification;
                        }

                        for(var counter = notifications.length - 1; counter >= 0 ; counter--) {
                            var message = "";

                            var notification = notifications[counter];
                            var id = notification['id'];
                            var modifiedBy = notification['modified_by'];
                            var dateModified = notification['date_modified'];
                            var notificationType = notification['type'];

                            if(typeof notificationType === 'undefined') {
                                notificationType = 'alert';
                            }


                            if("message" in notification) {
                                var formattedMessage = "";
                                var messageSegments = null;

                                if(notification['message'] !== null) {
                                    messageSegments = notification['message'].split('\n');
                                }

                                for(var i in messageSegments) {
                                    if(messageSegments[i].indexOf("updated the following attributes:") === -1) {

                                        formattedMessage += messageSegments[i];

                                        if(i < messageSegments.length - 1) {
                                            formattedMessage += "<br>";
                                        }
                                    }
                                }

                                if(formattedMessage === "" && notification['message'] !== null) {
                                    formattedMessage = messageSegments;
                                }

                                if(notification['link'] !== null) {
                                    message = "<a href='" + notification['link'] + "' target='_blank'>" + notification['header'] + "</a>";
                                } else {
                                    message = notification['header'];
                                }

                                message += " (by <b>" + modifiedBy + "</b> <span class='noty_modified' data-modified='" +
                                        dateModified + "'></span>)<br/>" + formattedMessage;

                                generateContainerNoty('div#notifications', notificationType, message, dialogTimeout, id);
                            }
                        }

                        var currentDate = new Date();

                        if(serverToLocalDateDelta === null) {
                            var serverDate = new Date(serverTime);

                            // calculate the difference between the server
                            // time and client time.
                            serverToLocalDateDelta = currentDate - serverDate;
                        }

                        var shiftedCurrentDate = new Date(currentDate - serverToLocalDateDelta);

                        // update the notification times after receiving
                        // new notifications
                        updateNotificationTimes(shiftedCurrentDate);
                    },
                    error: function(data) {
                        // if an error occurred then give the server much more time
                        // to try and recover from the error before reattempting.
                        poll_timeout = 60000;
                        numPollFailures++;
                    },
                    complete: function() {
                        // throttle a little bit before polling again
                        setTimeout(poll, poll_timeout, newer_than);
                    }
                });
            } else {

                // still update the notification times, even after giving up
                // trying to poll for new notifications.
                if(serverToLocalDateDelta !== null) {
                    var currentDate = new Date();
                    var shiftedCurrentDate = new Date(currentDate - serverToLocalDateDelta);
                    updateNotificationTimes(shiftedCurrentDate);
                }

                setTimeout(poll, poll_timeout, newer_than);
            }
        })(); // this function is executed here
    }
}); //document.ready
