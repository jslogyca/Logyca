# Changelog

## 17.0.6.0.11

Ensure sufficient formio.js versions (GitHub tags) are downloaded and registered.\
In future versions this will be more configurable.

## 17.0.6.0.10

Possibility to override the form submit (input) value, by slurping from the input (DOM) element value.\
This is especially useful for external JavaScript (scripts) that modify DOM input elements.

## 17.0.6.0.9

Fix Form (action button) Send Invitation Mail, which is `formio.form` model method `action_send_invitation_mail`.

## 17.0.6.0.8

Form Builder improvements:
- Field active
- Add search filter: Archived
- Remove search filters: Not Portal, Not Public

## 17.0.6.0.7

Fix `formio.form` method `_process_api_components` with `res.partner` creation.\
Add DEPRECATION warning: `_process_api_components: partner creation will be removed from Odoo 18`

## 17.0.6.0.6

Add Form Builder (server) action: Reset formio.js version to Dummy

## 17.0.6.0.5

Improve the installation (`post_init_hook`) to auto install the latest stable formio.js (library) version from the GitHub tags API.
Instead of relying (using) the system parameter (`ir.config_parameter`) `formio.default_version`, which isn't reliable due to the GitHub tags API (30 limit) results and leaves no installed formio.js (library) version.

## 17.0.6.0.4

Fix for error in a public wizard form:\
`TypeError: document.querySelector(...) is null`

PR: https://github.com/novacode-nl/odoo-formio/pull/286

## 17.0.6.0.3

Fixes for public form (formio.form record) rendering.

## 17.0.6.0.2

This fixes some issues introduced by version 17.0.6.0.0
- Revert the MRO inheritance of controllers classes back to only `http.Controller`.
  The MRO caused unpredictable and unsolvable exceptions when using some additional modules.
- This required a refactoring of the error/excpetion handler while loading or submitting a form.
  Added the `FormioException` class which does the actual rendering of the error message and traceback.

## 17.0.6.0.1

Improvements:
- In Form Builder, add smartbutton Server Actions.
- Rename Form Builder computed count fields method to `_compute_count_fields`.

## 17.0.6.0.0

Improve error handling while loading or submitting a form:
- This concerns the (backend, portal, public) endpoints: `/config`, `/submission`, `/submit`.
- An error message is displayed above the form.
- If debug mode is enabled for an internal user, the traceback is also displayed.

Implement hooks to execute Server Action after: submit, save draft.
- Add model `ir.actions.server` field `formio_form_execute_after_action`.
- `formio.form` model: Methods `after_submit` and `after_save_draft` execute the linked server action(s).

**UPDATE WARNING**

Possible **Internal server error** (not on Odoo.sh).\
Solve by updating the `formio` module from the `odoo-bin` (CLI), e.g:

Run with the odoo OS user:
`odoo-bin -u formio -c <config> -d <database> --stop-after-init`

## 17.0.5.0.2

Improve the reset of installed formio.js versions (download and reinstall of formio.js assets).\
This doesn't delete the formio.version record anymore, but replaces the formio.js assets.\
Also, the default CSS assets (e.g. bootstrap CSS) are no longer deleted, so manual addition/repair is no longer necessary.

## 17.0.5.0.1

Add Forms License Renewal Reminders by Activities:
- Configure the Renewal Reminder weeks and assign the internal users to be notified.
- Renewal Reminder Activities can be generated and regenerated after configuration (weeks, users).
- Activities are created and notified, also by a scheduled action (cron) when these activities have passed.

## 17.0.5.0.0

Fix random and unexplainable "ReverseProxy read errors" on webservers other than Nginx (e.g. Caddy, Traefik).\
This only required to change `/config` and `/submission` endpoints from HTTP POST to GET request methods.

## 17.0.4.0.4

Improve Form form-view layout. Move submission fields to the right (group).

## 17.0.4.0.3

In Form (model, views) add field Submission Commercial Entity related to the Submission Partner.

## 17.0.4.0.2

New feature to allow specific Form URL (query string) params from the form it's iframe src.\
This is currently usable for the Scroll Into View feature.\
We can provide the param `scroll_into_view_selector`, eg to scroll (up) in an embedded wizard form when navigating pages.

Example:
```
<t t-call="formio.form_iframe">
   <t t-set="formio_builder" t-value="formio_builder_object"/>
   <t t-set="src" t-value="'/formio/portal/form/' + str(form.uuid)"/>
   <t t-set="params" t-value="'scroll_into_view_selector=.progress-wizard'"/>
</t>
```

## 17.0.4.0.1

In the Form Builder form view, add (alert) info if the schema is empty.\
The (alert) info text: Start building a form by clicking the button (fa-rocket) Form Builder

## 17.0.4.0.0

Technical/API change for the `formio.form` methods `_after_create` and `_after_write`:
- Removed the `vals` argument because the respective caller methods `create` and `write` raised a Singleton Error upon `copy`.\
  This also simplifies the `create` and `write` methods.
- Call the `_process_api_components` method per record iteration.

## 17.0.3.4.0

- Add Form Builder setting (boolean field) to display a Form in "full width" 100% or 75%.
- Changed the default width of a Form to 75%.

## 17.0.3.3.0

Add descriptions with recommended modules in the `formio.builder.js.options` data.

## 17.0.3.2.0

Improve the Form Builder and Form button styling (colors).

## 17.0.3.1.0

Improvements for the `formio.builder.js.options`:
- Add a wizard to merge other `formio.builder.js.options` record field `value`.
- Add default and tracking for `formio.builder.js.options` field `value`.

Add a utils function `json_loads()`:\
Refactored the `try/except` with `json.loads()` and `ast.literal_eval()` calls, to use the utils `json_loads()` function.

## 17.0.3.0.0

Improvements and migration for the `formio.builder.js.options`:
- Add `editForm` components and options in `formio_builder_js_options_default`.
- Change `formio_builder_js_options_default` storage from Python Dict to JSON notation/syntax.
- Migrate `formio.builder` records (field) `formio_js_options` to merge the updated `formio_builder_js_options_default`.
- Migrate `formio.builder.js.options.default` records to merge the updated `formio_builder_js_options_default`.
- Improve the "Form Builder formio.js Options" form view (`view_formio_builder_js_options_form`): Add `widget='ace'` (`mode: js`).

## 17.0.2.0.1

- Fix migration scipts to support big jumps/leaps without crashing due to non-existent fields.
- Form Builder: Add badge "Locked Disabled".

## 17.0.2.0.0

Rename and migrate Form Builder field `public_uuid` to `current_uuid`.\
The `current_uuid` is a more meaningful name.

## 17.0.1.8.0

In Form Builder views (list, form, search) add:
- Field Public UUID (`public_uuid`)
- Public Current URL (`public_current_url`)

This is in addition to version 17.0.1.5.

## 17.0.1.7.0

Migrate the Form Builder (`formio.builder`) field `submission_url_add_query_params_from` to endpoint specific fields:
- `portal_submission_url_add_query_params_from`
- `portal_submission_url_add_query_params_from`
- `backend_submission_url_add_query_params_from`

This makes it possible to distinguish the setting per endpoint.

## 17.0.1.6.0

Minor form builder view migration fix (column_invisible).

## 17.0.1.5.0

### Allow (support) versioning for publicly published forms (form builders)

Add endpoint `/formio/public/form/new/current/<string:builder_public_uuid>` that allows to update the form builders (versioning) and keep them published when the state is "Current".\
This required to add the `formio.builder` model field `public_uuid`, that is identical to all `formio.builder` records with the same name.

## 17.0.1.4.0

In the Form Builder, show a "Locked" badge in case it is locked.

## 17.0.1.3.0

Add new group "Forms: Allow updating form submission data".\
Users in this group are allowed to edit and update the (raw, JSON) submission data in the `formio.form` form view.

## 17.0.1.2.0

- Fix formioScrollIntoView event handler.
- Default value for form builder fields: `portal_scroll_into_view`, `public_scroll_into_view`

## 17.0.1.1.0

Improve the formio.js library registration (downloader, importer) with a new setting to allow only registered versions.\
This adds a new system parameter `ir.config_parameter` which currently defaults to 'v4' and can be modified in the configuration window.\
The allowed setting is a comma separated string (list) of formio.js versions to register. Examples:
- v4,v5
- v4.17,v4.18

## 17.0.1.0.0

Initial release.
