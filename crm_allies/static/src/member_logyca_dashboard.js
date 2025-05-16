/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart,onWillUpdateProps, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
export class Dashboard extends Component {

setup() {
super.setup();
this.orm = useService("orm");
this.state = useState({hierarchy: {}});
onWillStart(this.onWillStart);
 

}

}
Dashboard.template = "MemberLogycaDashboard";
registry.category("actions").add("member_logyca_dashboard", Dashboard);


onWillStart(){
var default_activity_id;
var default_activity_name;
var activity_data = [];
var self=this;
self.orm.call("activity.dashboard", "get_scheduled_activity", [
]).then(function(result){
self.state.hierarchy = result
});
}