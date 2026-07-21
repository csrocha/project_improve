from odoo import models


class ReportProjectImproveCapacityReportHtml(models.AbstractModel):
    _name = 'report.project_improve.report_capacity_report_html'
    _description = 'Reporte HTML de capacidad agregada por skill'

    def _get_report_values(self, docids, data=None):
        docs = self.env['knowledge.asset'].browse(docids)
        return {
            'docs': docs,
            'reports': [self._build_report_context(asset) for asset in docs],
        }

    @staticmethod
    def _build_report_context(asset):
        version = asset.latest_version()
        payload = (version.payload or {}) if version else {}
        rows = [{
            'skill': item.get('skill') or '',
            'committed_hours': item.get('committed_hours', 0.0),
            'available_hours': item.get('available_hours', 0.0),
            'gap_hours': item.get('gap_hours', 0.0),
        } for item in (payload.get('items') or [])]
        return {
            'asset': asset,
            'generated_at': payload.get('generated_at') or '',
            'horizon_weeks': payload.get('horizon_weeks') or 0,
            'rows': rows,
        }
