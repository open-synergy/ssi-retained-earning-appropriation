# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

from odoo.addons.ssi_decorator import ssi_decorator


class RetainedEarningAppropriation(models.Model):
    _name = "retained_earning_appropriation"
    _inherit = [
        "mixin.transaction_confirm",
        "mixin.transaction_done",
        "mixin.transaction_cancel",
        "mixin.company_currency",
        "mixin.date_duration",
    ]
    _description = "Retained Earning Appropriation"

    # Multiple Approval Attribute
    _approval_from_state = "draft"
    _approval_to_state = "done"
    _approval_state = "confirm"
    _after_approved_method = "action_done"

    # Attributes related to add element on view automatically
    _automatically_insert_view_element = True
    _automatically_insert_done_policy_fields = False
    _automatically_insert_done_button = False

    _statusbar_visible_label = "draft,confirm,done"
    _policy_field_order = [
        "confirm_ok",
        "approve_ok",
        "reject_ok",
        "restart_approval_ok",
        "cancel_ok",
        "restart_ok",
        "done_ok",
        "manual_number_ok",
    ]
    _header_button_order = [
        "action_confirm",
        "action_approve_approval",
        "action_reject_approval",
        "%(ssi_transaction_cancel_mixin.base_select_cancel_reason_action)d",
        "action_restart",
    ]

    # Attributes related to add element on search view automatically
    _state_filter_order = [
        "dom_draft",
        "dom_confirm",
        "dom_reject",
        "dom_done",
        "dom_cancel",
    ]

    # Sequence attribute
    _create_sequence_state = "done"

    type_id = fields.Many2one(
        string="Type",
        comodel_name="retained_earning_appropriation_type",
        required=True,
        readonly=True,
        ondelete="restrict",
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    date = fields.Date(
        string="Date",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    date_due = fields.Date(
        string="Date Due",
        required=False,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    amount_unappropriate = fields.Monetary(
        string="Amount Unappropriate",
        currency_field="company_currency_id",
        required=False,
        compute="_compute_amount",
        store=True,
    )
    amount_appropriate = fields.Monetary(
        string="Amount Appropriate",
        currency_field="company_currency_id",
        required=False,
        compute="_compute_amount",
        store=True,
    )
    amount_to_appropriate = fields.Monetary(
        string="Amount To Appropriate",
        currency_field="company_currency_id",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    amount_distribute = fields.Monetary(
        string="Amount Distribute",
        currency_field="company_currency_id",
        required=False,
        compute="_compute_amount_distribute",
        store=True,
    )
    amount_diff = fields.Monetary(
        string="Amount Diff.",
        currency_field="company_currency_id",
        required=False,
        compute="_compute_amount_distribute",
        store=True,
    )
    distribution_ids = fields.One2many(
        string="Distributions",
        comodel_name="retained_earning_appropriation.distribution",
        inverse_name="appropriation_id",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
    )
    num_distribution = fields.Integer(
        string="Num. Of Distribution",
        compute="_compute_amount_distribute",
        store=True,
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        ondelete="restrict",
    )
    retained_earning_account_id = fields.Many2one(
        string="Retained Earning Account Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        ondelete="restrict",
    )
    appropriation_account_id = fields.Many2one(
        string="Appropriation Account",
        comodel_name="account.account",
        required=True,
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        ondelete="restrict",
    )
    analytic_account_id = fields.Many2one(
        string="Analytic Account",
        comodel_name="account.analytic.account",
        readonly=True,
        states={
            "draft": [
                ("readonly", False),
            ],
        },
        ondelete="restrict",
    )
    move_id = fields.Many2one(
        string="# Move",
        comodel_name="account.move",
        readonly=True,
    )
    state = fields.Selection(
        string="State",
        default="draft",
        required=True,
        readonly=True,
        selection=[
            ("draft", "Draft"),
            ("confirm", "Waiting for Approval"),
            ("done", "Done"),
            ("cancel", "Cancelled"),
            ("reject", "Rejected"),
        ],
    )

    @api.model
    def _get_policy_field(self):
        res = super(RetainedEarningAppropriation, self)._get_policy_field()
        policy_field = [
            "confirm_ok",
            "approve_ok",
            "done_ok",
            "cancel_ok",
            "reject_ok",
            "restart_ok",
            "restart_approval_ok",
            "manual_number_ok",
        ]
        res += policy_field
        return res

    @api.depends(
        "date_end",
        "retained_earning_account_id",
        "move_id",
        "date",
    )
    def _compute_amount(self):
        MoveLine = self.env["account.move.line"]
        for record in self:
            unappropriate = appropriate = 0.0
            if record.date_end and record.retained_earning_account_id:
                criteria = [
                    ("account_id", "=", record.retained_earning_account_id.id),
                    ("date", "<=", record.date_end),
                ]
                if MoveLine.search_count(criteria) > 0:
                    compute_result = MoveLine.read_group(
                        criteria,
                        fields=["balance"],
                        groupby=["account_id"],
                        lazy=False,
                    )[0]
                    unappropriate = -1.0 * compute_result["balance"]

            if record.date_end and record.date and record.retained_earning_account_id:
                criteria = [
                    ("account_id", "=", record.retained_earning_account_id.id),
                    ("date", ">=", record.date_end),
                    ("date", "<=", record.date),
                ]
                if record.move_id:
                    criteria += [("move_id.id", "!=", record.move_id.id)]
                if MoveLine.search_count(criteria) > 0:
                    compute_result = MoveLine.read_group(
                        criteria,
                        fields=["debit"],
                        groupby=["account_id"],
                        lazy=False,
                    )[0]
                    appropriate = compute_result["debit"]
            record.amount_unappropriate = unappropriate
            record.amount_appropriate = appropriate

    @api.depends(
        "amount_unappropriate",
        "amount_appropriate",
        "amount_to_appropriate",
        "distribution_ids",
        "distribution_ids.amount_appropriate",
    )
    def _compute_amount_distribute(self):
        for record in self:
            distribute = diff = 0.0
            num_distribution = len(record.distribution_ids)
            for distribution in record.distribution_ids:
                distribute += distribution.amount_appropriate
            diff = record.amount_to_appropriate - distribute
            record.amount_distribute = distribute
            record.amount_diff = diff
            record.num_distribution = num_distribution

    @api.onchange(
        "type_id",
    )
    def onchange_journal_id(self):
        if self.type_id:
            self.journal_id = self.type_id.journal_id.id

    @api.onchange(
        "type_id",
    )
    def onchange_retained_earning_account_id(self):
        if self.type_id:
            self.retained_earning_account_id = (
                self.type_id.retained_earning_account_id.id
            )

    @api.onchange(
        "type_id",
    )
    def onchange_appropriation_account_id(self):
        if self.type_id:
            self.appropriation_account_id = self.type_id.appropriation_account_id.id

    @api.onchange(
        "amount_appropriate",
        "amount_unappropriate",
        "type_id",
        "date_start",
        "date_end",
        "date",
    )
    def onchange_amount_to_appropriate(self):
        self.amount_to_appropriate = 0.0
        if self.type_id:
            localdict = self._get_localdict()
            try:
                safe_eval(
                    self.type_id.amount_to_appropriate_python,
                    localdict,
                    mode="exec",
                    nocopy=True,
                )
                result = localdict["result"]
            except Exception as error:
                raise UserError(_("Error evaluating conditions.\n %s") % error)
            self.amount_to_appropriate = result

    def action_reload_distribution(self):
        for record in self.sudo():
            record._reload_distribution()

    def _reload_distribution(self):
        self.ensure_one()

        Distribution = self.env["retained_earning_appropriation.distribution"]

        if not self.type_id.distribute:
            return True

        for partner in self._compute_partner():
            distribution = Distribution.create(
                {
                    "appropriation_id": self.id,
                    "partner_id": partner.id,
                }
            )

        for distribution in self.distribution_ids:
            distribution.onchange_amount_appropriate()

    def _get_localdict(self):
        self.ensure_one()
        return {
            "env": self.env,
            "document": self,
        }

    def _compute_partner(self):
        self.ensure_one()
        try:
            method_name = "_evaluate_partner_" + self.type_id.partner_selection_method
            result = getattr(self, method_name)()
        except Exception as error:
            msg_err = _("Error evaluating conditions.\n %s") % error
            raise UserError(msg_err)
        return result

    def _evaluate_partner_python(self):
        self.ensure_one()
        res = False
        localdict = self._get_localdict()
        try:
            safe_eval(
                self.type_id.partner_selection_python,
                localdict,
                mode="exec",
                nocopy=True,
            )
            res = localdict["result"]
        except Exception as error:
            raise UserError(_("Error evaluating conditions.\n %s") % error)
        return res

    def _evaluate_partner_domain(self):
        self.ensure_one()
        domain = safe_eval(self.type_id.partner_selection_domain, {})
        return self.search(domain)

    @ssi_decorator.post_done_action()
    def _create_move(self):
        Move = self.env["account.move"]
        ML = self.env["account.move.line"]
        move = Move.with_context(check_move_validity=False).create(
            self._prepare_account_move()
        )
        self.write(
            {
                "move_id": move.id,
            }
        )
        ML.with_context(check_move_validity=False).create(
            self._prepare_header_move_line()
        )

        if not self.company_currency_id.is_zero(self.amount_diff):
            ML.with_context(check_move_validity=False).create(
                self._prepare_diff_move_line()
            )

        for distribution in self.distribution_ids:
            distribution._create_move_line()

        move.action_post()

    def _prepare_account_move(self):
        return {
            "name": self.name,
            "date": self.date,
            "journal_id": self.journal_id.id,
        }

    def _prepare_header_move_line(self):
        name = "Retained earning appropriation %s" % (self.name)
        return {
            "move_id": self.move_id.id,
            "name": name,
            "account_id": self.retained_earning_account_id.id,
            "analytic_account_id": self.analytic_account_id.id,
            "debit": self.amount_to_appropriate,
            "credit": 0.0,
        }

    def _prepare_diff_move_line(self):
        name = "Retained earning appropriation %s" % (self.name)
        return {
            "move_id": self.move_id.id,
            "name": name,
            "account_id": self.retained_earning_account_id.id,
            "analytic_account_id": self.analytic_account_id.id,
            "credit": self.amount_diff,
            "debit": 0.0,
        }

    @ssi_decorator.post_cancel_action()
    def _20_cancel_move(self):
        self.ensure_one()

        if not self.move_id:
            return True

        move = self.move_id
        self.write(
            {
                "move_id": False,
            }
        )

        if move.state == "posted":
            move.button_cancel()

        move.with_context(force_delete=True).unlink()
