import warnings
from cache_tagging.utils import Undef


class IDependency(object):

    def evaluate(self, cache, transaction_start_time, version):
        """
        :type cache: cache_tagging.interfaces.ICache
        :type transaction_start_time: float
        :type version: int or None
        """
        raise NotImplementedError

    def validate(self, cache, version):
        """
        :type cache: cache_tagging.interfaces.ICache
        :type version: int or None
        :rtype: cache_tagging.interfaces.IDeferred
        """
        raise NotImplementedError

    def invalidate(self, cache, version):
        """
        :type cache: cache_tagging.interfaces.ICache
        :type version: int or None
        """
        raise NotImplementedError

    def acquire(self, cache, delay, version):
        """
        :type cache: cache_tagging.interfaces.ICache
        :type delay: int
        :type version: int or None
        """
        raise NotImplementedError

    def release(self, cache, delay, version):
        """
        :type cache: cache_tagging.interfaces.ICache
        :type delay: int
        :type version: int or None
        """
        raise NotImplementedError

    def extend(self, other):
        """
        :type other: cache_tagging.interfaces.IDependency
        :rtype: bool
        """
        raise NotImplementedError

    def __copy__(self):
        """
        :rtype: cache_tagging.interfaces.IDependency
        """
        raise NotImplementedError


class IDeferred(object):  # Queue?
    """
    :type queue: list[collections.Callable, tuple, dict]
    :type aggregation_criterion: tuple
    """
    queue = None
    aggregation_criterion = None

    def add_callback(self, callback, *args, **kwargs):  # put? apply?
        """
        :type callback: collections.Callable
        :rtype: cache_tagging.interfaces.IDeferred
        """
        raise NotImplementedError

    def get(self):  # recv?
        raise NotImplementedError

    @property
    def parent(self):
        raise NotImplementedError

    @parent.setter
    def parent(self, parent):
        raise NotImplementedError

    @parent.deleter
    def parent(self):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError


class ICacheNode(object):

    def parent(self):
        """
        :rtype: cache_tagging.interfaces.ICacheNode
        """
        raise NotImplementedError

    def key(self):
        """
        :rtype: str
        """
        raise NotImplementedError

    def add_dependency(self, dependency, version=None):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        raise NotImplementedError

    def get_dependency(self, version=None):
        """
        :type version: int or None
        :rtype dependency: cache_tagging.interfaces.IDependency
        """
        raise NotImplementedError


class IRelationManager(object):

    def get(self, key):
        """
        :type key: str
        :rtype: cache_tagging.interfaces.ICacheNode
        """
        raise NotImplementedError

    def pop(self, key):
        """
        :type key: str
        :rtype: cache_tagging.interfaces.ICacheNode
        """
        raise NotImplementedError

    def current(self, key_or_node=Undef):
        """
        :type key_or_node: str or cache_tagging.interfaces.ICacheNode
        :rtype: cache_tagging.interfaces.ICacheNode
        """
        raise NotImplementedError

    def clear(self):
        raise NotImplementedError


class IDependencyLock(object):

    def acquire(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        raise NotImplementedError

    def release(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        raise NotImplementedError

    def evaluate(self, dependency, transaction_start_time, version):
        """it's okay delegate it to IDependencyLock,

        because Lock can implement Pessimistic Offline Lock or Mutual Exclusion
        instead of raising TagsLocked exception.

        :type dependency: cache_tagging.interfaces.IDependency
        :type transaction_start_time: float
        :type version: int or None
        """
        raise NotImplementedError

    @staticmethod
    def make(isolation_level, thread_safe_cache_accessor, delay):
        """
        :type isolation_level: str
        :type thread_safe_cache_accessor: collections.Callable
        :type delay: int
        :rtype: cache_tagging.interfaces.IDependencyLock
        """
        raise NotImplementedError
    

class ITransaction(object):

    def parent(self):
        """
        :rtype: cache_tagging.interfaces.ITransaction
        """
        raise NotImplementedError

    def add_dependency(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        raise NotImplementedError

    def evaluate(self, dependency, version):
        """
        :type dependency: cache_tagging.interfaces.IDependency
        :type version: int or None
        """
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError


class ITransactionManager(object):

    def __call__(self, func=None):
        raise NotImplementedError

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self, *args):
        raise NotImplementedError

    def current(self, node=Undef):
        """
        :type node: cache_tagging.interfaces.ITransaction
        :rtype: cache_tagging.interfaces.ITransaction
        """
        raise NotImplementedError

    def begin(self):
        """Handles database transaction begin."""
        raise NotImplementedError

    def finish(self):
        """Handles database transaction commit or rollback.

        In any case (commit or rollback) we need to invalidate tags,
        because caches can be generated for
        current database session (for rollback case) or
        another database session (for commit case).
        So, method is named "finish" (not "commit"
        or "rollback").
        """
        raise NotImplementedError

    def flush(self):
        """Finishes all active transactions."""
        raise NotImplementedError


class ICache(object):
    """Historically used Django API interface."""
    def add(self, key, value, timeout=None, version=None):
        """
        Set a value in the cache if the key does not already exist. If
        timeout is given, that timeout will be used for the key; otherwise
        the default cache timeout will be used.

        Returns True if the value was stored, False otherwise.
        """
        raise NotImplementedError

    def get(self, key, default=None, version=None):
        """
        Fetch a given key from the cache. If the key does not exist, return
        default, which itself defaults to None.
        """
        raise NotImplementedError

    def set(self, key, value, timeout=None, version=None):
        """
        Set a value in the cache. If timeout is given, that timeout will be
        used for the key; otherwise the default cache timeout will be used.
        """
        raise NotImplementedError

    def delete(self, key, version=None):
        """
        Delete a key from the cache, failing silently.
        """
        raise NotImplementedError

    def get_many(self, keys, version=None):
        """
        Fetch a bunch of keys from the cache. For certain backends (memcached,
        pgsql) this can be *much* faster when fetching multiple values.

        Returns a dict mapping each key in keys to its value. If the given
        key is missing, it will be missing from the response dict.
        """
        raise NotImplementedError

    def has_key(self, key, version=None):
        """
        Returns True if the key is in the cache and has not expired.
        """
        raise NotImplementedError

    def incr(self, key, delta=1, version=None):
        """
        Add delta to value in the cache. If the key does not exist, raise a
        ValueError exception.
        """
        raise NotImplementedError

    def decr(self, key, delta=1, version=None):
        """
        Subtract delta from value in the cache. If the key does not exist,
        raise a ValueError exception.
        """
        raise NotImplementedError

    def __contains__(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        # This is a separate method, rather than just a copy of has_key(),
        # so that it always has the same functionality as has_key(), even
        # if a subclass overrides it.
        raise NotImplementedError

    def set_many(self, data, timeout=None, version=None):
        """
        Set a bunch of values in the cache at once from a dict of key/value
        pairs.  For certain backends (memcached), this is much more efficient
        than calling set() multiple times.

        If timeout is given, that timeout will be used for the key; otherwise
        the default cache timeout will be used.
        """
        raise NotImplementedError

    def delete_many(self, keys, version=None):
        """
        Set a bunch of values in the cache at once.  For certain backends
        (memcached), this is much more efficient than calling delete() multiple
        times.
        """
        raise NotImplementedError

    def clear(self):
        """Remove *all* values from the cache at once."""
        raise NotImplementedError

    def incr_version(self, key, delta=1, version=None):
        """Adds delta to the cache version for the supplied key. Returns the
        new version.
        """
        raise NotImplementedError

    def decr_version(self, key, delta=1, version=None):
        """Substracts delta from the cache version for the supplied key.
        Returns the new version.
        """
        raise NotImplementedError

    def close(self, **kwargs):
        """Close the cache connection"""
        raise NotImplementedError


def default_key_func(key, key_prefix, version):
    """
    Default function to generate keys.

    Constructs the key used by all other methods. By default it prepends
    the `key_prefix'. KEY_FUNCTION can be used to specify an alternate
    function with custom key making behavior.
    """
    return '%s:%s:%s' % (key_prefix, version, key)


class BaseCache(ICache):
    """Historically used Django API interface.

    You can make wrapper for any cache system.
    """

    # Memcached does not accept keys longer than this.
    MEMCACHE_MAX_KEY_LENGTH = 250

    key_prefix = ''
    version = 1
    key_func = staticmethod(default_key_func)

    def make_key(self, key, version=None):
        """Constructs the key used by all other methods. By default it
        uses the key_func to generate a key (which, by default,
        prepends the `key_prefix' and 'version'). An different key
        function can be provided at the time of cache construction;
        alternatively, you can subclass the cache backend to provide
        custom key making behavior.
        """
        if version is None:
            version = self.version

        new_key = self.key_func(key, self.key_prefix, version)
        return new_key

    def get_many(self, keys, version=None):
        """
        Fetch a bunch of keys from the cache. For certain backends (memcached,
        pgsql) this can be *much* faster when fetching multiple values.

        Returns a dict mapping each key in keys to its value. If the given
        key is missing, it will be missing from the response dict.
        """
        d = {}
        for k in keys:
            val = self.get(k, version=version)
            if val is not None:
                d[k] = val
        return d

    def has_key(self, key, version=None):
        """
        Returns True if the key is in the cache and has not expired.
        """
        return self.get(key, version=version) is not None

    def incr(self, key, delta=1, version=None):
        """
        Add delta to value in the cache. If the key does not exist, raise a
        ValueError exception.
        """
        value = self.get(key, version=version)
        if value is None:
            raise ValueError("Key '%s' not found" % key)
        new_value = value + delta
        self.set(key, new_value, version=version)
        return new_value

    def decr(self, key, delta=1, version=None):
        """
        Subtract delta from value in the cache. If the key does not exist,
        raise a ValueError exception.
        """
        return self.incr(key, -delta, version=version)

    def __contains__(self, key):
        """
        Returns True if the key is in the cache and has not expired.
        """
        # This is a separate method, rather than just a copy of has_key(),
        # so that it always has the same functionality as has_key(), even
        # if a subclass overrides it.
        return self.has_key(key)

    def set_many(self, data, timeout=None, version=None):
        """
        Set a bunch of values in the cache at once from a dict of key/value
        pairs.  For certain backends (memcached), this is much more efficient
        than calling set() multiple times.

        If timeout is given, that timeout will be used for the key; otherwise
        the default cache timeout will be used.
        """
        for key, value in data.items():
            self.set(key, value, timeout=timeout, version=version)

    def delete_many(self, keys, version=None):
        """
        Set a bunch of values in the cache at once.  For certain backends
        (memcached), this is much more efficient than calling delete() multiple
        times.
        """
        for key in keys:
            self.delete(key, version=version)

    def validate_key(self, key):
        """
        Warn about keys that would not be portable to the memcached
        backend. This encourages (but does not force) writing backend-portable
        cache code.

        """
        if len(key) > self.MEMCACHE_MAX_KEY_LENGTH:
            warnings.warn(
                'Cache key will cause errors if used with memcached: ' +
                '{0} (longer than {1})'.format(key, self.MEMCACHE_MAX_KEY_LENGTH)
            )
        for char in key:
            if ord(char) < 33 or ord(char) == 127:
                warnings.warn(
                    'Cache key contains characters that will cause ' +
                    'errors if used with memcached: {0:!r}'.format(key)
                )

    def incr_version(self, key, delta=1, version=None):
        """Adds delta to the cache version for the supplied key. Returns the
        new version.
        """
        if version is None:
            version = self.version

        value = self.get(key, version=version)
        if value is None:
            raise ValueError("Key '%s' not found" % key)

        self.set(key, value, version=version + delta)
        self.delete(key, version=version)
        return version + delta

    def decr_version(self, key, delta=1, version=None):
        """Substracts delta from the cache version for the supplied key.
        Returns the new version.
        """
        return self.incr_version(key, -delta, version)

    def close(self, **kwargs):
        """Close the cache connection"""
        pass
