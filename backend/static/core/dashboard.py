from admin_tools.dashboard import modules, Dashboard, AppIndexDashboard
from admin_tools.utils import get_admin_site_name

class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for admin_tools.
    """
    def __init__(self, **kwargs):
        Dashboard.__init__(self, **kwargs)
        
        # Quick links module
        self.children.append(modules.LinkList(
            'Quick Links',
            layout='inline',
            draggable=True,
            deletable=False,
            collapsible=False,
            children=[
                ['Add Client', '/admin/clients/client/add/'],
                ['Add Project', '/admin/projects/project/add/'],
                ['Add Payment', '/admin/payments/payment/add/'],
                ['Generate Report', '/admin/reports/'],
            ]
        ))
        
        # Recent actions module
        self.children.append(modules.RecentActions('Recent Actions', 10))
        
        # Statistics modules
        self.children.append(modules.Group(
            title='Statistics',
            display='tabs',
            children=[
                modules.AppList(
                    'Applications',
                    exclude=('django.contrib.*',),
                ),
                modules.ModelList(
                    'Administration',
                    models=('django.contrib.*',),
                ),
            ]
        ))
        
        # Custom chart module
        self.children.append(modules.LinkList(
            'System Status',
            children=[
                ['View System Health', '/admin/health/'],
                ['View Logs', '/admin/logs/'],
                ['View Reports', '/admin/reports/'],
            ]
        ))