/** @odoo-module **/

// Disable no-alert rule for the lines where confirm is used
/* eslint-disable no-alert */
import {FormController} from "@web/views/form/form_controller";
import {ListController} from "@web/views/list/list_controller";
import {ViewButton} from "@web/views/view_button/view_button";
import {useRef} from "@odoo/owl";
import {useSetupView} from "@web/views/view_hook";
const oldSetup = FormController.prototype.setup;
const oldonPagerUpdated = FormController.prototype.onPagerUpdate;

const Formsetup = function () {
    this.rootRef = useRef("root");
    useSetupView({
        beforeLeave: () => {
            if (this.model.root.dirty) {
                if (confirm("Do you want to save changes Automatically?")) {
                    return this.model.root.save({
                        reload: false,
                        onError: this.onSaveError.bind(this),
                    });
                }
                this.model.root.discard();
                return true;
            }
        },
    });
    const result = oldSetup.apply(this, arguments);
    return result;
};
FormController.prototype.setup = Formsetup;

const onPagerUpdate = async function () {
    const dirty = await this.model.root.isDirty();
    if (dirty) {
        if (confirm("Do you want to save changes Automatically?")) {
            return oldonPagerUpdated.apply(this, arguments);
        }
        this.model.root.discard();
    }
    return oldonPagerUpdated.apply(this, arguments);
};

// Assign setup to FormController

FormController.prototype.onPagerUpdate = onPagerUpdate;

const oldCreate = FormController.prototype.create;
// On new record creation raise popup of save/confirm #T8269
FormController.prototype.create = function () {
    if (this.model.root.dirty) {
        if (confirm("Do you want to save changes Automatically?")) {
            return this.model.root
                .save({noReload: true, stayInEdition: true})
                .then(() => {
                    return oldCreate.apply(this, arguments);
                });
        }
        this.model.root.discard();
    }
    return oldCreate.apply(this, arguments);
};

const oldshouldExecuteAction = FormController.prototype.shouldExecuteAction;
// On clicking Action Buttons raise popup of save/confirm #T8269
FormController.prototype.shouldExecuteAction = function () {
    if (this.model.root.dirty) {
        if (confirm("Do you want to save changes Automatically?")) {
            return this.model.root
                .save({noReload: true, stayInEdition: true})
                .then(() => {
                    return oldshouldExecuteAction.apply(this, arguments);
                });
        }
        this.model.root.discard();
    }
    return oldshouldExecuteAction.apply(this, arguments);
};

const ListSuper = ListController.prototype.setup;
const Listsetup = function () {
    useSetupView({
        rootRef: this.rootRef,
        beforeLeave: () => {
            const list = this.model.root;
            const editedRecord = list.editedRecord;
            if (editedRecord && editedRecord.isDirty) {
                if (confirm("Do you want to save changes Automatically?")) {
                    if (!list.leaveEditMode()) {
                        throw new Error("View can't be saved");
                    }
                } else {
                    this.onClickDiscard();
                    return true;
                }
            }
        },
    });
    const result = ListSuper.apply(this, arguments);
    return result;
};
ListController.prototype.setup = Listsetup;

const oldonClick = ViewButton.prototype.onClick;
// On clicking viewButtons(Headers or smart button) raise popup
// of save/confirm #T8269
ViewButton.prototype.onClick = function () {
    if (this.props.record.dirty) {
        if (confirm("Do you want to save changes Automatically?")) {
            return this.props.record
                .save({noReload: true, stayInEdition: true})
                .then(() => {
                    return oldonClick.apply(this, arguments);
                });
        }
        this.props.record.discard();
    }
    return oldonClick.apply(this, arguments);
};
