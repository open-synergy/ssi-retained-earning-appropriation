# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class RetainedEarningAppropriation(models.Model):
    _name = "retained_earning_appropriation_type"
    _inherit = ["mixin.master_data"]
    _description = "Retained Earning Appropriation"

    name = fields.Char(
        string="Penalty Type",
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        required=True,
        ondelete="restrict",
    )
    retained_earning_account_id = fields.Many2one(
        string="Retained Earning Account Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    appropriation_account_id = fields.Many2one(
        string="Appropriation Account",
        comodel_name="account.account",
        required=True,
        ondelete="restrict",
    )
    distribute = fields.Boolean(
        string="Distribute Amoong Partner",
    )
    partner_selection_method = fields.Selection(
        string="Partner Selection Method",
        selection=[
            ("domain", "Domain"),
            ("python", "Python Code"),
        ],
        required=True,
        default="domain",
    )
    partner_selection_domain = fields.Char(
        string="Domain",
        copy=True,
    )
    partner_selection_python = fields.Text(
        string="Python Code for Computing Partner Selection",
        default="""# Available variables:
#  - env: Odoo Environment on which the action is triggered.
#  - document: Recordset of move lines.
#  - result: Return result.
result = 0.0""",
        copy=True,
    )

    amount_to_appropriate_python = fields.Text(
        string="Python Code for Computing Appropriation Amount",
        default="""# Available variables:
#  - env: Odoo Environment on which the action is triggered.
#  - document: Recordset of move lines.
#  - result: Return result.
result = document.amount_unappropriate""",
        copy=True,
    )
    amount_distribute_python = fields.Text(
        string="Python Code for Computing Appropriation Amount Distribution Among Partner",
        default="""# Available variables:
#  - env: Odoo Environment on which the action is triggered.
#  - document: Recordset of move lines.
#  - result: Return result.
result = document.amount_unappropriate / float(document.num_distribution)""",
        copy=True,
    )

    # def _get_policy_localdict(self, move_line):
    #     self.ensure_one()
    #     return {
    #         "env": self.env,
    #         "document": move_line,
    #     }

    # def _evaluate_python(self, move_line, python_code):
    #     self.ensure_one()
    #     res = False
    #     localdict = self._get_policy_localdict(move_line)
    #     try:
    #         safe_eval(python_code, localdict, mode="exec", nocopy=True)
    #         res = localdict["result"]
    #     except Exception as error:
    #         raise UserError(_("Error evaluating conditions.\n %s") % error)
    #     return res
