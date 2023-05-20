# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import Warning as UserError
from odoo.tools.safe_eval import safe_eval


class RetainedEarningAppropriationDistribution(models.Model):
    _name = "retained_earning_appropriation.distribution"
    _description = "Retained Earning Appropriation Distribution"

    appropriation_id = fields.Many2one(
        string="# Appropriation",
        comodel_name="retained_earning_appropriation",
        required=True,
        ondelete="cascade",
    )
    type_id = fields.Many2one(
        string="Type",
        comodel_name="retained_earning_appropriation_type",
        related="appropriation_id.type_id",
        store=True,
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        related="appropriation_id.company_currency_id",
        store=False,
    )
    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        required=True,
    )
    amount_appropriate = fields.Monetary(
        string="Amount Appropriate",
        currency_field="currency_id",
        required=True,
        default=1.0,
    )

    @api.onchange(
        "partner_id",
        "type_id",
    )
    def onchange_amount_appropriate(self):
        self.amount_appropriate = 0.0
        if self.type_id and self.partner_id:
            localdict = self._get_localdict()
            try:
                safe_eval(
                    self.type_id.amount_distribute_python,
                    localdict,
                    mode="exec",
                    nocopy=True,
                )
                result = localdict["result"]
            except Exception as error:
                raise UserError(_("Error evaluating conditions.\n %s") % error)
            self.amount_appropriate = result

    def _get_localdict(self):
        self.ensure_one()
        return {
            "env": self.env,
            "document": self.appropriation_id,
            "distribution": self,
        }

    def _create_move_line(self):
        MoveLine = self.env["account.move.line"]
        MoveLine.with_context(check_move_validity=False).create(
            self._prepare_move_line()
        )

    def _prepare_move_line(self):

        appropriation = self.appropriation_id
        name = "Retained earning appropriation %s" % (appropriation.name)
        return {
            "move_id": appropriation.move_id.id,
            "name": name,
            "account_id": appropriation.retained_earning_account_id.id,
            "analytic_account_id": appropriation.analytic_account_id.id,
            "credit": self.amount_appropriate,
            "debit": 0.0,
            "partner_id": self.partner_id.id,
        }
