odoo.define('hr_attendance.my_attendances', function (require) {
"use strict";

var core = require('web.core');
var Model = require('web.Model');
var Widget = require('web.Widget');

var QWeb = core.qweb;
var _t = core._t;

//외근
var outing = Widget.extend({
    events: {
        "click .o_hr_attendance_outing_icon": function() {
            this.$('.o_hr_attendance_outing_icon').attr("disabled", "disabled");
            this.get_geolocation();
        },
    },

    start: function () {
        var self = this;
        var hr_employee = new Model('hr.employee');
        hr_employee.query(['outing_state', 'name'])
            .filter([['user_id', '=', self.session.uid]])
            .all()
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.$el.html(QWeb.render("outingMenu", {widget: self}));
            });

        return this._super.apply(this, arguments);
    },

    update_attendance: function (my_location) {
        var self = this;
        //사유와 목적지를가져온다.
        var destination = $('#destination').val();
        var reason = $('#reason').val();
        var date_to = $('#date_to').val();
        var date_from = $('#date_from').val(); 
        console.log('start')
        var hr_employee = new Model('hr.employee');
        hr_employee.call('write_outing_list',[self.employee.id,destination,reason,date_to,date_from,my_location])
            .then(function(result) {
                location.reload();
                if (result.action) {
                    self.do_action(result.action);
                
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },

    get_geolocation: function () {
        var startPos;
        var result;
        var self = this;
        var hr_employee = new Model('hr.employee');
        var geoOptions = {
            timeout: 10 * 1000,
            enableHighAccuracy: true
        }

        var geoSuccess = function(position) {
            startPos = position;
            alert("확인되었습니다.");
            var lat = startPos.coords.latitude;
            var lng = startPos.coords.longitude;
            console.log(lat + ',' + lng);
            result = [lat, lng];

            hr_employee.call('naver_geocode', [[], result])
                .then(function(result) {
                    self.update_attendance(result);
                    console.log(result);
                });
        };
        var geoError = function(error) {
            alert(error.message)
        };

        navigator.geolocation.getCurrentPosition(geoSuccess, geoError, geoOptions)
    },

});

//출장
var MyAttendances = Widget.extend({
    events: {
        "click .o_hr_attendance_sign_in_out_icon": function() {
            this.$('.o_hr_attendance_sign_in_out_icon').attr("disabled", "disabled");
            this.get_geolocation();
        },
    },

    start: function () {
        var self = this;

        var hr_employee = new Model('hr.employee');
        hr_employee.query(['attendance_state', 'name'])
            .filter([['user_id', '=', self.session.uid]])
            .all()
            .then(function (res) {
                if (_.isEmpty(res) ) {
                    self.$('.o_hr_attendance_employee').append(_t("Error : Could not find employee linked to user"));
                    return;
                }
                self.employee = res[0];
                self.$el.html(QWeb.render("HrAttendanceMyMainMenu", {widget: self}));
            });

        return this._super.apply(this, arguments);
    },

    update_attendance: function (my_location) {
        var self = this;
        var hr_employee = new Model('hr.employee');
        hr_employee.call('attendance_manual', [[self.employee.id], 'hr_attendance.hr_attendance_action_my_attendances', my_location])
            .then(function(result) {
                if (result.action) {
                    self.do_action(result.action);
                } else if (result.warning) {
                    self.do_warn(result.warning);
                }
            });
    },

    get_geolocation: function () {
        var startPos;
        var result;
        var self = this;
        var hr_employee = new Model('hr.employee');
        var geoOptions = {
            timeout: 10 * 1000,
            enableHighAccuracy: true
        }

        var geoSuccess = function(position) {
            startPos = position;
            alert("확인되었습니다.");
            var lat = startPos.coords.latitude;
            var lng = startPos.coords.longitude;
            console.log(lat + ',' + lng);
            result = [lat, lng];

            hr_employee.call('naver_geocode', [[], result])
                .then(function(result) {
                    self.update_attendance(result);
                    console.log(result);
                });
        };
        var geoError = function(error) {
            alert(error.message)
        };

        navigator.geolocation.getCurrentPosition(geoSuccess, geoError, geoOptions)
    },
});

core.action_registry.add('hr_attendance_my_attendances', MyAttendances)
                    .add('hr_attendance_outing', outing);

return MyAttendances,outing;

});
