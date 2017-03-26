__version__ = '0.3.0'


try:
    from fabdeb.master_tasks import prepare_server
except ImportError:
    pass
