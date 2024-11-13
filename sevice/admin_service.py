from typing import Dict, List
import datetime
import traceback
from enum import Enum
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Table, TableStyle, Frame, PageTemplate, FrameBreak, PageBreak
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.linecharts import HorizontalLineChart

from tortoise.models import Model

from config import settings
from common.logger import logger


class ReportType(Enum):
    COUNT = "count"
    SUM = "sum"


class ReportMaker:

    report_name: str
    report = None
    type_report: ReportType = None
    _save_path: str = settings.report_file_path if settings.report_file_path[-1] != "/" \
        else settings.report_file_path[:-1]

    def __init__(self,
                 model: Model,
                 report_name: str,
                 report_type: ReportType):
        self.model = model
        self.report_name = report_name
        self.type_report = report_type

    def _sum_by_day(self, data, sum_field):
        sums_by_day = {}
        for row in data:
            date = row["datetime_create"].date()
            if date in sums_by_day:
                sums_by_day[date] += row[sum_field]
            else:
                sums_by_day[date] = row[sum_field]
        return sums_by_day

    def _count_by_day(self, data):
        counts_by_day = {}
        for row in data:
            date = row["datetime_create"].date()
            if date in counts_by_day:
                counts_by_day[date] += 1
            else:
                counts_by_day[date] = 1
        return counts_by_day

    def _get_list_date(self, start_date, end_date):
        data_list = []
        current_date = start_date
        while current_date <= end_date:
            data_list.append(current_date)
            current_date += datetime.timedelta(days=1)
        return data_list

    def _full_report_empty_fields(self, date_list):
        for date in date_list:
            if date not in self.report:
                self.report[date] = 0
        sorted_report = dict(sorted(self.report.items()))
        self.report = sorted_report

    async def create_report_by_period(self, start_date: datetime.date, end_date: datetime.date) -> Dict:
        payment_by_period = await self.model.filter(
            datetime_create__range=[str(start_date) + " 00:00:00", str(end_date) + " 23:59:59"]
        ).all().values()
        date_list = self._get_list_date(start_date, end_date)
        logger.debug(f"Next data from DB by period from {start_date} to {end_date}: {payment_by_period}")
        if self.type_report == ReportType.SUM.value:
            self.report = self._sum_by_day(payment_by_period, "amount")
        if self.type_report == ReportType.COUNT.value:
            self.report = self._count_by_day(payment_by_period)
        logger.debug(f"Next data will be filled spaces: {self.report}")
        self._full_report_empty_fields(date_list)
        logger.debug(f"Data will be return: {self.report}")

        return self.report

    async def save_report_to_pdf(self, title="report"):
        file_name = f"{self._save_path}/{title}_{str(datetime.datetime.now())}.pdf"
        logger.debug(f"Will convert a report {self.report} to pdf")
        pdf_maker = self.PdfReportMaker(file_name, self.report, self.report_name)
        try:
            pdf_maker.create_pdf()
        except Exception as exp:
            logger.error(f"Can't to create pdf doc. The error occures: {exp}")
            logger.error(traceback.format_exc())
        else:
            logger.debug(f"A file was be created: {file_name}")
            return file_name

    class PdfReportMaker:
        filename: str
        _data_tables: List = []
        _table_columns: List[int] = ["date"]
        _max_value: int
        _min_value: int
        report_title: str

        def __init__(self, file_name, data, report_name):
            self._table_columns.append(report_name)
            self.file_name = file_name
            self.report_title = report_name
            try:
                self._data_tables, self._max_value, self._min_value = self._convert_to_tables(data)
            except Exception as exp:
                logger.error(f"Data can be converted to table: {data}. Error: {exp}")
            logger.info(f"Data has been converted to table: {self._data_tables}")

        def _convert_to_tables(self, data):
            logger.debug(f"Next data will be converted to tables: {data}")
            data_tables = []
            current_month = next(iter(data)).month
            current_table = []
            max_value = 0
            min_value = 0
            for key in data:
                if key.month == current_month:
                    current_table.append([key, data[key]])
                else:
                    data_tables.append(current_table)
                    current_table = []
                    current_month = key.month
                    current_table.append([key, data[key]])
                if data[key] > max_value:
                    max_value = data[key]
                if data[key] < min_value:
                    min_value = data[key]
            data_tables.append(current_table)
            return data_tables, max_value, min_value

        def _convert_date_to_string(self, table):
            converted_table = []
            for row in table:
                converted_table.append([str(row[0]), row[1]])
            return converted_table
        def _create_table(self, table):
            add_table=self._convert_date_to_string(table)
            logger.debug(f"Conver table to pdf {add_table}")
            pdf_table = Table(add_table)
            pdf_table.setStyle(TableStyle([
                ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ]))
            logger.debug(f"Return pdf")
            return pdf_table

        def _convert_table_to_graphic(self, table):
            drawing = Drawing(800, 350)

            data = []
            row_data = []
            dates = []

            drawing.add(String(60, 120,
                            f"{self.report_title} graphic for {table[0][0].strftime("%Y-%B")}",
                            fontName='Times-Roman',
                            fontSize=36))

            for row in table:
                dates.append(str(row[0].day))
                row_data.append(int(row[1]))
            data.append(row_data)

            logger.debug(f"Graphic includes {data} and {dates}")

            lc = HorizontalLineChart()
            lc.x = 50
            lc.y = -120
            lc.height = 200
            lc.width = 550
            lc.data = data
            lc.categoryAxis.categoryNames = dates
            lc.categoryAxis.labels.boxAnchor = 'n'
            lc.valueAxis.valueMin = self._min_value
            lc.valueAxis.valueMax = self._max_value
            lc.valueAxis.valueStep = self._max_value/10 if self._max_value>10 else 1
            lc.lines[0].strokeWidth = 2
            drawing.add(lc)
            return drawing


        def create_pdf(self):
            #Create a pdf template for report file

            doc = BaseDocTemplate(
                self.file_name,
                showBoundary=1,
                pagesize=landscape(A4),
                topMargin=0*inch,
                bottomMargin=0*inch,
                leftMargin=0*inch,
                rightMargin=0*inch
            )

            frameCount = 2
            frameWidth = doc.width / frameCount
            frameHeight = doc.height - 0 * inch

            frame_list = [
                Frame(
                    x1=doc.leftMargin,
                    y1=doc.bottomMargin,
                    width=frameWidth/2,
                    height=frameHeight),
                Frame(
                    x1=doc.leftMargin + frameWidth/2,
                    y1=doc.bottomMargin,
                    width=frameWidth*2,
                    height=frameHeight),
            ]

            doc.addPageTemplates([PageTemplate(id='frames', frames=frame_list), ])

            # container for the 'Flowable' objects
            elements = []
            for table in self._data_tables:
                logger.debug(f"Next table convert to PDF{table}")
                pdf_table = self._create_table(table)
                elements.append(pdf_table)
                elements.append(FrameBreak())
                logger.debug("Create graphic")
                graphic = self._convert_table_to_graphic(table)
                elements.append(graphic)
                logger.debug("Page break")
                elements.append(PageBreak())
            # write the document to disk
            logger.debug("Will write pdf file")
            doc.build(elements)
