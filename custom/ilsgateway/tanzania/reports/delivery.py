from dateutil import rrule
from django.db.models.aggregates import Avg
from corehq.apps.locations.models import SQLLocation
from corehq.apps.reports.datatables import DataTablesHeader, DataTablesColumn
from custom.ilsgateway.filters import ProductByProgramFilter, MSDZoneFilter, MonthAndQuarterFilter
from custom.ilsgateway.tanzania import ILSData, DetailsReport
from custom.ilsgateway.tanzania.reports.facility_details import FacilityDetailsReport, InventoryHistoryData, \
    RegistrationData, RandRHistory
from custom.ilsgateway.models import OrganizationSummary, DeliveryGroups, SupplyPointStatusTypes
from custom.ilsgateway.tanzania.reports.mixins import DeliverySubmissionData
from custom.ilsgateway.tanzania.reports.utils import make_url, link_format, latest_status_or_none,\
    get_this_lead_time, get_avg_lead_time
from dimagi.utils.decorators.memoized import memoized
from corehq.apps.reports.filters.fixtures import AsyncLocationFilter
from corehq.apps.reports.filters.select import YearFilter
from django.utils.translation import ugettext as _


class LeadTimeHistory(ILSData):
    show_table = True
    title = "Lead Time History"
    slug = "lead_time_history"
    show_chart = False

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn(_('Name')),
            DataTablesColumn(_('Average Lead Time In Days'))
        )

    @property
    def rows(self):
        locations = SQLLocation.objects.filter(parent__location_id=self.config['location_id'],
                                               site_code__icontains=self.config['msd_code'])
        rows = []
        for loc in locations:
            try:
                org_summary = OrganizationSummary.objects.filter(supply_point=loc.location_id,
                                                                 date__range=(self.config['startdate'],
                                                                              self.config['enddate']))\
                    .aggregate(average_lead_time_in_days=Avg('average_lead_time_in_days'))
            except OrganizationSummary.DoesNotExist:
                continue

            avg_lead_time = org_summary['average_lead_time_in_days']

            if avg_lead_time:
                avg_lead_time = "%.1f" % avg_lead_time
            else:
                avg_lead_time = "None"

            args = (loc.location_id, self.config['month'],
                    self.config['year'], self.config['program'], self.config['prd_part_url'])
            url = make_url(DeliveryReport, self.config['domain'],
                           '?location_id=%s&month=%s&year=%s&filter_by_program=%s%s', args)

            rows.append([link_format(loc.name, url), avg_lead_time])
        return rows


class DeliveryStatus(ILSData):
    show_table = True
    slug = "delivery_status"
    show_chart = False

    def __init__(self, config=None, css_class='row_chart'):
        super(DeliveryStatus, self).__init__(config, css_class)
        self.config = config or {}
        self.css_class = css_class
        month = self.config.get('month')
        if month:
            self.title = "Delivery Status: Group " + DeliveryGroups(int(month)).current_delivering_group()
        else:
            self.title = "Delivery Status"

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn(_('Code')),
            DataTablesColumn(_('Facility Name')),
            DataTablesColumn(_('Delivery Status')),
            DataTablesColumn(_('Delivery Date')),
            DataTablesColumn(_('This Cycle Lead Time')),
            DataTablesColumn(_('Average Lead Time In Days'))
        )

    @property
    def rows(self):
        rows = []
        locations = SQLLocation.objects.filter(parent__location_id=self.config['location_id'],
                                               site_code__icontains=self.config['msd_code'])
        dg = []
        for date in list(rrule.rrule(rrule.MONTHLY, dtstart=self.config['startdate'],
                                     until=self.config['enddate'])):
            dg.extend(DeliveryGroups().delivering(locations, date.month))

        for child in dg:
            latest = latest_status_or_none(
                child.location_id,
                SupplyPointStatusTypes.DELIVERY_FACILITY,
                self.config['startdate'],
                self.config['enddate']
            )
            status_name = latest.name if latest else ""
            status_date = latest.status_date.strftime("%d-%m-%Y") if latest else "None"

            url = make_url(FacilityDetailsReport, self.config['domain'],
                           '?location_id=%s&filter_by_program=%s%s',
                           (child.location_id, self.config['program'], self.config['prd_part_url']))

            cycle_lead_time = get_this_lead_time(
                child.location_id,
                self.config['startdate'],
                self.config['enddate']
            )
            avg_lead_time = get_avg_lead_time(child.location_id, self.config['startdate'],
                                              self.config['enddate'])
            rows.append(
                [
                    child.site_code,
                    link_format(child.name, url),
                    status_name,
                    status_date,
                    cycle_lead_time,
                    avg_lead_time
                ]
            )
        return rows


class DeliveryData(ILSData):
    show_table = True
    show_chart = False
    slug = 'delivery_data'
    title = 'Delivery Data'

    @property
    def headers(self):
        return DataTablesHeader(
            DataTablesColumn(_('Category'), sort_direction="desc"),
            DataTablesColumn(_('# Facilities')),
            DataTablesColumn(_('% of total')),
        )

    @property
    def rows(self):
        data = DeliverySubmissionData(config=self.config, css_class='row_chart_all').rows

        if data:
            dg = data[0]
            percent_format = lambda x, y: x * 100 / y

            return [
                [_('Didn\'t Respond'), dg.not_responding, '%.2f%%' % percent_format(dg.not_responding, dg.total)],
                [_('Not Received'), dg.not_received, '%.2f%%' % percent_format(dg.not_received, dg.total)],
                [_('Received'), dg.received, '%.2f%%' % percent_format(dg.received, dg.total)],
                [_('Total'), dg.total, '100%'],
            ]


class DeliveryReport(DetailsReport):
    slug = "delivery_report"
    name = 'Delivery'
    use_datatables = True

    @property
    def title(self):
        title = _('Delivery Report')
        if self.location and self.location.location_type.name.upper() == 'FACILITY':
            title = _('Facility Details')
        return title

    @property
    def fields(self):
        fields = [AsyncLocationFilter, MonthAndQuarterFilter, YearFilter, ProductByProgramFilter, MSDZoneFilter]
        if self.location and self.location.location_type.name.upper() == 'FACILITY':
            fields = [AsyncLocationFilter, ProductByProgramFilter]
        return fields

    @property
    @memoized
    def data_providers(self):
        data_providers = [
            DeliverySubmissionData(config=self.report_config, css_class='row_chart_all'),
        ]
        config = self.report_config
        if config['location_id']:
            location = SQLLocation.objects.get(location_id=config['location_id'])
            if location.location_type.name.upper() in ['REGION', 'MOHSW']:
                data_providers.append(DeliveryData(config=config, css_class='row_chart_all'))
                data_providers.append(LeadTimeHistory(config=config, css_class='row_chart_all'))
            elif location.location_type.name.upper() == 'FACILITY':
                return [
                    InventoryHistoryData(config=config),
                    RandRHistory(config=config),
                    RegistrationData(config=dict(loc_type='FACILITY', **config), css_class='row_chart_all'),
                    RegistrationData(config=dict(loc_type='DISTRICT', **config), css_class='row_chart_all'),
                    RegistrationData(config=dict(loc_type='REGION', **config), css_class='row_chart_all')
                ]
            else:
                data_providers.append(DeliveryStatus(config=config, css_class='row_chart_all'))
        return data_providers

    @property
    def report_context(self):
        ret = super(DeliveryReport, self).report_context
        ret['view_mode'] = 'delivery'
        return ret
