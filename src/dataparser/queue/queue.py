from collections import OrderedDict
from copy import deepcopy


class ParsingQueue(object):
    """This is queue for parsing test data and libraries"""
    def __init__(self):
        self.queue = OrderedDict({})
        self.rf_types = [
            'library',
            'test_suite',
            'resource',
            None,
            'variable_file'
            ]

    def add(self, data, rf_type):
        """Add item to the end of the queue.

        Does not add duplicates in the queue. ``rf_type``
        defines the type of the added item. Possible values are:
        `library`, `test_suite`, `resource` and None. rf_type=None is used
        when it is not know is the file type resource or a test suite.
        """
        if rf_type not in self.rf_types:
            raise ValueError('Invalid rf_type: {0}'.format(rf_type))
        if data not in self.queue:
            self.queue[data] = {
                'scanned': False,
                'type': rf_type}

    def get(self):
        """Get item from start of the queue"""
        try:
            data = self.queue.popitem(last=False)
            tmp = deepcopy(data)
            tmp[1]['scanned'] = 'queued'
            self.queue[tmp[0]] = tmp[1]
            return data
        except KeyError:
            return {}

    def set(self, data):
        """Set status to True and put item as last item in the queue"""
        status = self.queue[data]
        status['scanned'] = True
        self.queue[data] = status
