# Copyright Nova Code (https://www.novacode.nl)
# See LICENSE file for full licensing details.

import json
import logging

from odoo import http, fields, _
from odoo.http import request

from ..models.formio_form import (
    STATE_DRAFT as FORM_STATE_DRAFT,
    STATE_COMPLETE as FORM_STATE_COMPLETE,
)

from .exceptions import FormioException

from .utils import (
    generate_uuid4,
    log_form_submisssion,
    update_dict_allowed_keys,
    validate_csrf,
)

_logger = logging.getLogger(__name__)


class FormioController(http.Controller):

    ##############
    # Form Builder
    ##############

    @http.route('/formio/builder/<int:builder_id>', type='http', auth='user', website=True)
    def builder_root(self, builder_id, **kwargs):
        if not request.env.user.has_group('formio.group_formio_admin'):
            # TODO Render template with message?
            return request.redirect("/")

        # TODO REMOVE (still needed or obsolete legacy?)
        # Needed to update language
        context = request.env.context.copy()
        context.update({'lang': request.env.user.lang})
        request.env.context = context

        builder = request.env['formio.builder'].browse(builder_id)
        languages = builder.languages
        lang_en = request.env.ref('base.lang_en')

        if lang_en.active and builder.language_en_enable and 'en_US' not in languages.mapped('code'):
            languages |= request.env.ref('base.lang_en')

        values = {
            'builder': builder,
            # 'languages' already injected in rendering somehow
            'builder_languages': languages,
            'formio_css_assets': builder.formio_css_assets,
            'formio_js_assets': builder.formio_js_assets,
            # uuid is used to disable assets (js, css) caching by hrefs
            'uuid': generate_uuid4()
        }
        return request.render('formio.formio_builder_embed', values)

    @http.route('/formio/builder/<int:builder_id>/config', type='http', auth='user', methods=['GET'], csrf=False)
    def builder_config(self, builder_id):
        if not request.env.user.has_group('formio.group_formio_admin'):
            return
        builder = request.env['formio.builder'].browse(builder_id)
        res = {'schema': {}, 'options': {}}

        if builder:
            if builder.schema:
                res['schema'] = json.loads(builder.schema)
            res['options'] = builder._get_js_options()
            res['params'] = builder._get_js_params()
            res['locales'] = builder._get_form_js_locales()
            res['csrf_token'] = request.csrf_token()
        return request.make_json_response(res)

    @http.route('/formio/builder/<model("formio.builder"):builder>/save', type='http', auth="user", methods=['POST'], csrf=False, website=True)
    def builder_save(self, builder):
        self.validate_csrf()
        if not request.env.user.has_group('formio.group_formio_admin'):
            return

        post = request.get_json_data()
        if 'builder_id' not in post or int(post['builder_id']) != builder.id:
            return

        schema = json.dumps(post['schema'])
        builder.write({'schema': schema})

    #######################
    # Form - backend - uuid
    #######################

    @http.route('/formio/form/<string:uuid>', type='http', auth='user', website=True)
    def form_root(self, uuid):
        form = self._get_form(uuid, 'read')
        if not form:
            msg = 'Form UUID %s' % uuid
            return request.not_found(msg)

        # TODO REMOVE (still needed or obsolete legacy?)
        # Needed to update language
        context = request.env.context.copy()
        context.update({'lang': request.env.user.lang})
        request.env.context = context

        languages = form.builder_id.languages
        lang_en = request.env.ref('base.lang_en')

        if lang_en.active and form.builder_id.language_en_enable and 'en_US' not in languages.mapped('code'):
            languages |= request.env.ref('base.lang_en')

        values = {
            'form': form,
            # 'languages' already injected in rendering somehow
            'form_languages': languages.sorted('name'),
            'formio_css_assets': form.builder_id.formio_css_assets,
            'formio_js_assets': form.builder_id.formio_js_assets,
            # uuid is used to disable assets (js, css) caching by hrefs
            'uuid': generate_uuid4()
        }
        return request.render('formio.formio_form_embed', values)

    @http.route('/formio/form/<string:form_uuid>/config', type='http', auth='user', methods=['GET'], csrf=False, website=True)
    def form_config(self, form_uuid):
        form = self._get_form(form_uuid, 'read')
        # TODO remove config (key)
        res = {'schema': {}, 'options': {}, 'config': {}, 'params': {}}

        if form and form.builder_id.schema:
            res['schema'] = json.loads(form.builder_id.schema)
            res['options'] = self._get_form_js_options(form)
            res['params'] = self._get_form_js_params(form)
            res['locales'] = self._get_form_js_locales(form)
            res['csrf_token'] = request.csrf_token()
        return request.make_json_response(res)

    @http.route('/formio/form/<string:uuid>/submission', type='http', auth='user', methods=['GET'], csrf=False, website=True)
    def form_submission(self, uuid):
        form = self._get_form(uuid, 'read')

        # Submission data
        if form and form.submission_data:
            submission_data = {'submission': json.loads(form.submission_data)}
        else:
            submission_data = {'submission': {}}

        # ETL Odoo data
        if form:
            try:
                etl_odoo_data = form.sudo()._etl_odoo_data()
                submission_data['submission'].update(etl_odoo_data)
            except Exception as e:
                formio_exception = FormioException(e, form=form)
                error_message, error_traceback = formio_exception.render_exception_load()
                submission_data['error_message'] = error_message
                if request.session.debug and request.env.user.has_group('base.group_user'):
                    submission_data['error_traceback'] = error_traceback

        return request.make_json_response(submission_data)

    @http.route('/formio/form/<string:uuid>/submit', type='http', auth="user", methods=['POST'], csrf=False, website=True)
    def form_submit(self, uuid):
        """ POST with ID instead of uuid, to get the model object right away """
        res = {
            'form_uuid': uuid
        }
        self.validate_csrf()

        form = self._get_form(uuid, 'write')
        if not form:
            res['error_message'] = _('The form was not found.')
            return request.make_json_response(res)
        if form.state == FORM_STATE_COMPLETE:
            res['error_message'] = _('The form has already been submitted.')
            res['options'] = {'readOnly': True}
            return request.make_json_response(res)

        post = request.get_json_data()
        vals = {
            'submission_data': json.dumps(post['data']),
            'submission_user_id': request.env.user.id,
            'submission_date': fields.Datetime.now(),
        }
        if post.get('saveDraft') or (
            post['data'].get('saveDraft') and not post['data'].get('submit')
        ):
            vals['state'] = FORM_STATE_DRAFT
        else:
            vals['state'] = FORM_STATE_COMPLETE

        try:
            form.write(vals)
            if vals.get('state') == FORM_STATE_COMPLETE:
                form.after_submit()
            elif vals.get('state') == FORM_STATE_DRAFT:
                form.after_save_draft()
            log_form_submisssion(form)
            res['submission_data'] = form.submission_data
        except Exception as e:
            formio_exception = FormioException(e, form=form)
            error_message, error_traceback = formio_exception.render_exception_submit()
            res['error_message'] = error_message
            if request.session.debug and request.env.user.has_group('base.group_user'):
                res['error_traceback'] = error_traceback
            form.write({'state': 'ERROR'})
        return request.make_json_response(res)

    #########
    # Helpers
    #########

    def _get_form_js_options(self, form):
        options = form._get_js_options()

        # language
        Lang = request.env['res.lang']
        if request.env.user.lang in form.languages.mapped('code'):
            language = Lang._formio_ietf_code(request.env.user.lang)
        else:
            language = Lang._formio_ietf_code(request.env.context['lang'])
        options['language'] = language
        return options

    def _get_form_js_locales(self, form):
        return form.builder_id._get_form_js_locales()

    def _get_form_js_params(self, form):
        params = form._get_js_params()
        args = request.httprequest.args
        args_dict = args.to_dict()
        if bool(args_dict):
            params = update_dict_allowed_keys(
                params,
                args_dict,
                self._allowed_form_js_params_from_url(form.builder_id),
            )
        return params

    def _get_form(self, uuid, mode):
        return request.env['formio.form'].get_form(uuid, mode)

    def _allowed_form_js_params_from_url(self, builder):
        return builder._allowed_form_js_params_from_url()

    def validate_csrf(self):
        validate_csrf(request)
