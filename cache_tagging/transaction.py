import time
# import uuid
from functools import wraps

from cache_tagging import dependencies, interfaces, mixins, utils
from cache_tagging.utils import Undef


class AbstractTransaction(interfaces.ITransaction):
    def __init__(self, lock):
        self._lock = lock

    def evaluate(self, tags, version):
        return self._lock.evaluate(tags, self, version)

    @staticmethod
    def _current_time():
        return time.time()


class Transaction(AbstractTransaction):
    def __init__(self, lock):
        """
        :type lock: cache_tagging.interfaces.IDependencyLock
        """
        super(Transaction, self).__init__(lock)
        self._dependencies = dict()
        self._start_time = self._current_time()
        self._id = self._make_id()

    def get_id(self):
        return self._id

    def get_start_time(self):
        return self._start_time

    def parent(self):
        return None

    def add_dependency(self, dependency, version):
        assert isinstance(dependency, interfaces.IDependency)
        if version not in self._dependencies:
            self._dependencies[version] = dependencies.CompositeDependency()
        self._dependencies[version].extend(dependency)
        self._lock.acquire(dependency, self, version)

    def finish(self):
        for version, dependency in self._dependencies.items():
            self._lock.release(dependency, self, version)

    @staticmethod
    def _make_id():
        return utils.get_thread_id()
        # return uuid.uuid4().hex


class SavePoint(Transaction):
    def __init__(self, lock, parent):
        """
        :type lock: cache_tagging.interfaces.IDependencyLock
        :type parent: cache_tagging.transaction.Transaction or cache_tagging.transaction.SavePoint
        """
        super(SavePoint, self).__init__(lock)
        assert isinstance(parent, (SavePoint, Transaction))
        self._parent = parent

    def get_id(self):
        return self.parent().get_id()

    def get_start_time(self):
        return self.parent().get_start_time()

    def parent(self):
        return self._parent

    def add_dependency(self, dependency, version):
        assert isinstance(dependency, interfaces.IDependency)
        super(SavePoint, self).add_dependency(dependency, version)
        self._parent.add_dependency(dependency, version)

    def finish(self):
        pass


class DummyTransaction(AbstractTransaction):

    def get_id(self):
        return utils.get_thread_id()
        # return "DummyTransaction"

    def get_start_time(self):
        return self._current_time()

    def parent(self):
        return None

    def add_dependency(self, dependency, version):
        assert isinstance(dependency, interfaces.IDependency)

    def finish(self):
        pass


class AbstractTransactionManager(interfaces.ITransactionManager):

    def __call__(self, func=None):
        if func is None:
            return self

        @wraps(func)
        def _decorated(*args, **kw):
            with self:
                rv = func(*args, **kw)
            return rv

        return _decorated

    def __enter__(self):
        self.begin()

    def __exit__(self, *args):
        self.finish()
        return False


class TransactionManager(AbstractTransactionManager):

    def __init__(self, lock):
        """
        :type lock: cache_tagging.interfaces.IDependencyLock
        """
        self._lock = lock
        self._current = None

    def current(self, node=Undef):
        if node is Undef:
            return self._current or DummyTransaction(self._lock)
        self._current = node

    def begin(self):
        if self._current is None:
            self.current(Transaction(self._lock))
        else:
            self.current(SavePoint(self._lock, self.current()))
        return self.current()

    def finish(self):
        self.current().finish()
        self.current(self.current().parent())

    def flush(self):
        while self._current:
            self.finish()


class ThreadSafeTransactionManagerDecorator(mixins.ThreadSafeDecoratorMixIn, AbstractTransactionManager):

    def current(self, node=Undef):
        self._validate_thread_sharing()
        return self._delegate.current(node)

    def begin(self):
        self._validate_thread_sharing()
        return self._delegate.begin()

    def finish(self):
        self._validate_thread_sharing()
        return self._delegate.finish()

    def flush(self):
        return self._delegate.flush()
