/** @odoo-module **/

import { registry } from "@web/core/registry";
import {
    StateSelectionField,
    stateSelectionField,
} from "@web/views/fields/state_selection/state_selection_field";

const STATE_COLORS = {
    draft: "bg-info",
    evaluation: "bg-warning",
    progress: "bg-primary",
    done: "bg-success",
};

export class ProjectPlanningStateSelectionField extends StateSelectionField {
    statusColor(value) {
        return STATE_COLORS[value] || "";
    }
}

export const projectPlanningStateSelectionField = {
    ...stateSelectionField,
    component: ProjectPlanningStateSelectionField,
};

registry.category("fields").add("project_planning_state_selection", projectPlanningStateSelectionField);
