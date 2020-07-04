import numpy as np
import pandas as pd
from numba import njit
import hashlib

from vectorbt import defaults
from vectorbt.utils import checks, config, decorators

# non-randomized hash function
hash = lambda s: int(hashlib.sha512(s.encode('utf-8')).hexdigest()[:16], 16)


# ############# config.py ############# #

class TestConfig:

    def test_config(self):
        conf = config.Config({'a': 0, 'b': {'c': 1}}, frozen=False)
        conf['b']['d'] = 2

        conf = config.Config({'a': 0, 'b': {'c': 1}}, frozen=True)
        conf['a'] = 2

        try:
            conf['d'] = 2
            raise ValueError
        except:
            pass

        # go deeper
        conf['b']['c'] = 2

        try:
            conf['b']['d'] = 2
            raise ValueError
        except:
            pass

    def test_merge_kwargs(self):
        assert config.merge_kwargs({'a': 1}, {'b': 2}) == {'a': 1, 'b': 2}
        assert config.merge_kwargs({'a': 1}, {'a': 2}) == {'a': 2}
        assert config.merge_kwargs({'a': {'b': 2}}, {'a': {'c': 3}}) == {'a': {'b': 2, 'c': 3}}
        assert config.merge_kwargs({'a': {'b': 2}}, {'a': {'b': 3}}) == {'a': {'b': 3}}


# ############# decorators.py ############# #

class TestDecorators:
    def test_class_or_instancemethod(self):
        class G:
            @decorators.class_or_instancemethod
            def g(self_or_cls):
                if isinstance(self_or_cls, type):
                    return True  # class
                return False  # instance

        assert G.g()
        assert not G().g()

    def test_custom_property(self):
        class G:
            @decorators.custom_property(some='key')
            def cache_me(self): return np.random.uniform()

        assert 'some' in G.cache_me.kwargs
        assert G.cache_me.kwargs['some'] == 'key'

    def test_custom_method(self):
        class G:
            @decorators.custom_method(some='key')
            def cache_me(self): return np.random.uniform()

        assert 'some' in G.cache_me.kwargs
        assert G.cache_me.kwargs['some'] == 'key'

    def test_cached_property(self):
        class G:
            @decorators.cached_property(some='key')
            def cache_me(self): return np.random.uniform()

        assert 'some' in G.cache_me.kwargs
        assert G.cache_me.kwargs['some'] == 'key'

        class G:
            @decorators.cached_property
            def cache_me(self): return np.random.uniform()

        g = G()

        # general caching
        cached_number = g.cache_me
        assert g.cache_me == cached_number

        # clear_cache method
        G.cache_me.clear_cache(g)
        cached_number2 = g.cache_me
        assert cached_number2 != cached_number
        assert g.cache_me == cached_number2

        # disabled locally
        G.cache_me.disabled = True
        cached_number3 = g.cache_me
        assert cached_number3 != cached_number2
        assert g.cache_me != cached_number3
        G.cache_me.disabled = False

        # disabled globally
        defaults.caching = False
        cached_number4 = g.cache_me
        assert cached_number4 != cached_number3
        assert g.cache_me != cached_number4
        defaults.caching = True

    def test_cached_method(self):
        class G:
            @decorators.cached_method(some='key')
            def cache_me(self): return np.random.uniform()

        assert 'some' in G.cache_me.kwargs
        assert G.cache_me.kwargs['some'] == 'key'

        class G:
            @decorators.cached_method
            def cache_me(self, b=10): return np.random.uniform() * 10

        g = G()

        # general caching
        cached_number = g.cache_me()
        assert g.cache_me() == cached_number

        # clear_cache method
        G.cache_me.clear_cache(g)
        cached_number2 = g.cache_me()
        assert cached_number2 != cached_number
        assert g.cache_me() == cached_number2

        # disabled locally
        G.cache_me.disabled = True
        cached_number3 = g.cache_me()
        assert cached_number3 != cached_number2
        assert g.cache_me() != cached_number3
        G.cache_me.disabled = False

        # disabled globally
        defaults.caching = False
        cached_number4 = g.cache_me()
        assert cached_number4 != cached_number3
        assert g.cache_me() != cached_number4
        defaults.caching = True

        # disabled by non-hashable args
        cached_number5 = g.cache_me(b=np.zeros(1))
        assert cached_number5 != cached_number4
        assert g.cache_me(b=np.zeros(1)) != cached_number5

    def test_traverse_attr_kwargs(self):
        class A:
            @decorators.custom_property(some_key=0)
            def a(self): pass

        class B:
            @decorators.cached_property(some_key=0, child_cls=A)
            def a(self): pass

            @decorators.custom_method(some_key=1)
            def b(self): pass

        class C:
            @decorators.cached_method(some_key=0, child_cls=B)
            def b(self): pass

            @decorators.custom_property(some_key=1)
            def c(self): pass

        assert hash(str(decorators.traverse_attr_kwargs(C))) == 16728515581653529580
        assert hash(str(decorators.traverse_attr_kwargs(C, key='some_key'))) == 16728515581653529580
        assert hash(str(decorators.traverse_attr_kwargs(C, key='some_key', value=1))) == 703070484833749378
        assert hash(str(decorators.traverse_attr_kwargs(C, key='some_key', value=(0, 1)))) == 16728515581653529580


# ############# checks.py ############# #

class TestChecks:
    def test_is_pandas(self):
        assert not checks.is_pandas(0)
        assert not checks.is_pandas(np.array([0]))
        assert checks.is_pandas(pd.Series([1, 2, 3]))
        assert checks.is_pandas(pd.DataFrame([1, 2, 3]))

    def test_is_series(self):
        assert not checks.is_series(0)
        assert not checks.is_series(np.array([0]))
        assert checks.is_series(pd.Series([1, 2, 3]))
        assert not checks.is_series(pd.DataFrame([1, 2, 3]))

    def test_is_frame(self):
        assert not checks.is_frame(0)
        assert not checks.is_frame(np.array([0]))
        assert not checks.is_frame(pd.Series([1, 2, 3]))
        assert checks.is_frame(pd.DataFrame([1, 2, 3]))

    def test_is_array(self):
        assert not checks.is_array(0)
        assert checks.is_array(np.array([0]))
        assert checks.is_array(pd.Series([1, 2, 3]))
        assert checks.is_array(pd.DataFrame([1, 2, 3]))

    def test_is_numba_func(self):
        assert not checks.is_numba_func(lambda x: x)
        assert checks.is_numba_func(njit(lambda x: x))

    def test_is_hashable(self):
        assert checks.is_hashable(2)
        assert not checks.is_hashable(np.asarray(2))

    def test_assert_value_in(self):
        checks.assert_value_in(0, (0, 1))
        try:
            checks.assert_value_in(2, (0, 1))
            raise ValueError
        except:
            pass

    def test_assert_numba_func(self):
        checks.assert_numba_func(njit(lambda x: x))
        try:
            checks.assert_numba_func(lambda x: x)
            raise ValueError
        except:
            pass

    def test_assert_not_none(self):
        checks.assert_not_none(0)
        try:
            checks.assert_not_none(None)
            raise ValueError
        except:
            pass

    def test_assert_type(self):
        checks.assert_type(0, int)
        checks.assert_type(np.zeros(1), (np.ndarray, pd.Series))
        checks.assert_type(pd.Series([1, 2, 3]), (np.ndarray, pd.Series))
        try:
            checks.assert_type(pd.DataFrame([1, 2, 3]), (np.ndarray, pd.Series))
            raise ValueError
        except:
            pass

    def test_assert_subclass(self):
        class A:
            pass

        class B(A):
            pass

        class C(B):
            pass

        checks.assert_subclass(B, A)
        checks.assert_subclass(C, B)
        checks.assert_subclass(C, A)
        try:
            checks.assert_subclass(A, B)
            raise ValueError
        except:
            pass

    def test_assert_same_type(self):
        checks.assert_same_type(0, 1)
        checks.assert_same_type(np.zeros(1), np.empty(1))
        try:
            checks.assert_type(0, np.zeros(1))
            raise ValueError
        except:
            pass

    def test_assert_dtype(self):
        checks.assert_dtype(np.zeros(1), np.float)
        checks.assert_dtype(pd.Series([1, 2, 3]), np.int)
        checks.assert_dtype(pd.DataFrame([[1, 2, 3]]), np.int)
        try:
            checks.assert_dtype(pd.DataFrame([[1, 2, 3.]]), np.int)
            raise ValueError
        except:
            pass

    def test_assert_same_dtype(self):
        checks.assert_same_dtype(np.zeros(1), np.zeros((3, 3)))
        checks.assert_same_dtype(pd.Series([1, 2, 3]), pd.DataFrame([[1, 2, 3]]))
        checks.assert_same_dtype(pd.DataFrame([[1, 2, 3.]]), pd.DataFrame([[1, 2, 3.]]))
        try:
            checks.assert_same_dtype(pd.DataFrame([[1, 2, 3]]), pd.DataFrame([[1, 2, 3.]]))
            raise ValueError
        except:
            pass

    def test_assert_ndim(self):
        checks.assert_ndim(0, 0)
        checks.assert_ndim(np.zeros(1), 1)
        checks.assert_ndim(pd.Series([1, 2, 3]), (1, 2))
        checks.assert_ndim(pd.DataFrame([1, 2, 3]), (1, 2))
        try:
            checks.assert_ndim(np.zeros((3, 3, 3)), (1, 2))
            raise ValueError
        except:
            pass

    def test_assert_same_len(self):
        checks.assert_same_len([[1]], [[2]])
        checks.assert_same_len([[1]], [[2, 3]])
        try:
            checks.assert_same_len([[1]], [[2], [3]])
            raise ValueError
        except:
            pass

    def test_assert_same_shape(self):
        checks.assert_same_shape(0, 1)
        checks.assert_same_shape([1, 2, 3], np.asarray([1, 2, 3]))
        checks.assert_same_shape([1, 2, 3], pd.Series([1, 2, 3]))
        checks.assert_same_shape(np.zeros((3, 3)), pd.Series([1, 2, 3]), axis=0)
        checks.assert_same_shape(np.zeros((2, 3)), pd.Series([1, 2, 3]), axis=(1, 0))
        try:
            checks.assert_same_shape(np.zeros((2, 3)), pd.Series([1, 2, 3]), axis=(0, 1))
            raise ValueError
        except:
            pass

    def test_assert_same_index(self):
        index = ['a', 'b', 'c']
        checks.assert_same_index(pd.Series([1, 2, 3], index=index), pd.DataFrame([1, 2, 3], index=index))
        try:
            checks.assert_same_index(pd.Series([1, 2, 3]), pd.DataFrame([1, 2, 3], index=index))
            raise ValueError
        except:
            pass

    def test_assert_same_columns(self):
        columns = ['a', 'b', 'c']
        checks.assert_same_index(pd.DataFrame([[1, 2, 3]], columns=columns), pd.DataFrame([[1, 2, 3]], columns=columns))
        try:
            checks.assert_same_index(pd.DataFrame([[1, 2, 3]]), pd.DataFrame([[1, 2, 3]], columns=columns))
            raise ValueError
        except:
            pass

    def test_assert_same_meta(self):
        index = ['x', 'y', 'z']
        columns = ['a', 'b', 'c']
        checks.assert_same_meta(np.array([1, 2, 3]), np.array([1, 2, 3]))
        checks.assert_same_meta(pd.Series([1, 2, 3], index=index), pd.Series([1, 2, 3], index=index))
        checks.assert_same_meta(pd.DataFrame([[1, 2, 3]], columns=columns), pd.DataFrame([[1, 2, 3]], columns=columns))
        try:
            checks.assert_same_meta(pd.Series([1, 2]), pd.DataFrame([1, 2]))
            raise ValueError
        except:
            pass

        try:
            checks.assert_same_meta(pd.DataFrame([1, 2]), pd.DataFrame([1, 2, 3]))
            raise ValueError
        except:
            pass

        try:
            checks.assert_same_meta(pd.DataFrame([1, 2, 3]), pd.DataFrame([1, 2, 3], index=index))
            raise ValueError
        except:
            pass

        try:
            checks.assert_same_meta(pd.DataFrame([[1, 2, 3]]), pd.DataFrame([[1, 2, 3]], columns=columns))
            raise ValueError
        except:
            pass

    def test_assert_same(self):
        index = ['x', 'y', 'z']
        columns = ['a', 'b', 'c']
        checks.assert_same(np.array([1, 2, 3]), np.array([1, 2, 3]))
        checks.assert_same(pd.Series([1, 2, 3], index=index), pd.Series([1, 2, 3], index=index))
        checks.assert_same(pd.DataFrame([[1, 2, 3]], columns=columns), pd.DataFrame([[1, 2, 3]], columns=columns))
        try:
            checks.assert_same(np.array([1, 2]), np.array([1, 2, 3]))
            raise ValueError
        except:
            pass

    def test_assert_level_not_exists(self):
        i = pd.Index(['x', 'y', 'z'], name='i')
        multi_i = pd.MultiIndex.from_arrays([['x', 'y', 'z'], ['x2', 'y2', 'z2']], names=['i', 'i2'])
        checks.assert_level_not_exists(i, 'i2')
        checks.assert_level_not_exists(multi_i, 'i3')
        try:
            checks.assert_level_not_exists(i, 'i')
            checks.assert_level_not_exists(multi_i, 'i')
            raise ValueError
        except:
            pass