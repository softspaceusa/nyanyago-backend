from typing import Dict
import datetime
from enum import Enum
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.linecharts import HorizontalLineChart

from tortoise.models import Model


from common.logger import logger


class ReportMaker:

    report = None
    _table_columns = ["date"]

    def __init__(self, model: Model):
        self.model = model

    def _sum_by_day(self, data, sum_field):
        sums_by_day = {}
        for row in data:
            date = row["datetime_create"].date()
            if date in sums_by_day:
                sums_by_day[date] += row[sum_field]
            else:
                sums_by_day[date] = row[sum_field]
        return sums_by_day

    async def create_report_by_period(self, start_date: datetime.date, end_date: datetime.date) -> Dict:
        payment_by_period = await self.model.filter(
            datetime_create__range=[str(start_date) + " 00:00:00", str(end_date) + " 23:59:59"]
        ).all().values()
        logger.debug(f"Next data from DB by period from {start_date} to {end_date}: {payment_by_period}")
        self.report = self._sum_by_day(payment_by_period, "amount")
        logger.debug(f"Data will be return: {self.report}")
        self._table_columns.append("salary") #TODO need refactor it
        return self.report

    async def save_report_to_pdf(self, title="report"):
        file_name = f"{title}_{str(datetime.datetime.now())}.pdf"
        table_data = []
        table_data.append(self._table_columns)

        for key in self.report:
            table_data.append([key, self.report[key]])

        logger.debug(f"Data has been converted: {table_data}")

        doc = SimpleDocTemplate(file_name, pagesize=letter)
        # container for the 'Flowable' objects
        elements = []

        t = Table(table_data)
        t.setStyle(TableStyle([
                               ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                               ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
                               ]))
        elements.append(t)

        drawing = Drawing(400, 200)

        data = []
        row_data = []
        dates = []
        for row in table_data[1::]:
            dates.append(str(row[0]))
            row_data.append(int(row[1]))
        data.append(row_data)

        logger.debug(f"{data} and {dates}")

        lc = HorizontalLineChart()
        lc.x = 50
        lc.y = 50
        lc.height = 125
        lc.width = 300
        lc.data = data
        lc.categoryAxis.categoryNames = dates
        lc.categoryAxis.labels.boxAnchor = 'n'
        lc.valueAxis.valueMin = 0
        lc.valueAxis.valueMax = max(data[0])
        lc.valueAxis.valueStep = max(data[0])/10
        lc.lines[0].strokeWidth = 2
        drawing.add(lc)
        elements.append(drawing)
        # write the document to disk
        doc.build(elements)
        return file_name

